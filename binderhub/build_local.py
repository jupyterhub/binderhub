"""
Contains build of a docker image from a git repository.
"""

from functools import partial
import json
import os
# These methods are synchronous so don't use tornado.queue
import queue
import subprocess
from threading import Event, Thread
from tornado.ioloop import IOLoop
from tornado.log import app_log

from .build import ProgressEvent, Build


DEFAULT_READ_TIMEOUT = 1


class ProcessTerminated(subprocess.CalledProcessError):
    """
    Thrown when a process was forcibly terminated
    """

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        s = "ProcessTerminated: {}".format(self.message)
        return s


# https://github.com/jupyterhub/repo2docker/blob/2021.08.0/repo2docker/utils.py#L13-L58
# With modifications to allow asynchronous termination of the process
#
# BinderHub runs asynchronously but the repo2docker or K8S calls are
# synchronous- they are run inside a thread pool managed by BinderHub.
# This means we can't use asyncio subprocesses here to provide a way to allow
# a subprocess to be interrupted.
# Instead we run the subprocess inside a thread, and use a queue to pass the
# output of the subprocess to the caller.
# Since it's running inside its own thread we can set/check a flag to
# indicate whether the process should stop itself.
def _execute_cmd(cmd, capture=False, break_callback=None, **kwargs):
    """
    Call given command, yielding output line by line if capture=True.

    break_callback: A callable that returns a boolean indicating whether to
    stop execution.
    See https://stackoverflow.com/a/4896288

    Must be yielded from.
    """
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.STDOUT

    proc = subprocess.Popen(cmd, **kwargs)

    if not capture:
        # not capturing output, let subprocesses talk directly to terminal
        ret = proc.wait()
        if ret != 0:
            raise subprocess.CalledProcessError(ret, cmd)
        return

    # Capture output for logging.
    # Each line will be yielded as text.
    q = queue.Queue()

    def read_to_queue(proc, capture, q):
        try:
            for line in proc.stdout:
                q.put(line)
        finally:
            proc.wait()

    t = Thread(target=read_to_queue, args=(proc, capture, q))
    # thread dies with the program
    t.daemon = True
    t.start()

    c_last = ""
    terminated = False
    while True:
        try:
            line = q.get(True, timeout=DEFAULT_READ_TIMEOUT)
            yield line.decode("utf8", "replace")
            if break_callback and break_callback():
                proc.kill()
                terminated = True
        except queue.Empty:
            if break_callback and break_callback():
                proc.kill()
                terminated = True
            if not t.is_alive():
                break

    t.join()

    if terminated:
        raise ProcessTerminated(cmd)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


class LocalRepo2dockerBuild(Build):
    """Represents a build of a git repository into a docker image.

    This runs a build using the repo2docker command line tool.

    WARNING: This is still under development. Breaking changes may be made at any time.
    """

    def __init__(
        self,
        q,
        api,
        name,
        *,
        namespace,
        repo_url,
        ref,
        build_image,
        docker_host,
        image_name,
        git_credentials=None,
        push_secret=None,
        memory_limit=0,
        memory_request=0,
        node_selector=None,
        appendix="",
        log_tail_lines=100,
        sticky_builds=False,
    ):
        """
        Parameters
        ----------

        q : tornado.queues.Queue
            Queue that receives progress events after the build has been submitted
        api : ignored
        name : str
            A unique name for the thing (repo, ref) being built. Used to coalesce
            builds, make sure they are not being unnecessarily repeated
        namespace : ignored
        repo_url : str
            URL of repository to build.
            Passed through to repo2docker.
        ref : str
            Ref of repository to build
            Passed through to repo2docker.
        build_image : ignored
        docker_host : ignored
        image_name : str
            Full name of the image to build. Includes the tag.
            Passed through to repo2docker.
        git_credentials : str
            Git credentials to use to clone private repositories. Passed
            through to repo2docker via the GIT_CREDENTIAL_ENV environment
            variable. Can be anything that will be accepted by git as
            a valid output from a git-credential helper. See
            https://git-scm.com/docs/gitcredentials for more information.
        push_secret : ignored
        memory_limit
            Memory limit for the docker build process. Can be an integer in
            bytes, or a byte specification (like 6M).
            Passed through to repo2docker.
        memory_request
            Memory request of the build pod. The actual building happens in the
            docker daemon, but setting request in the build pod makes sure that
            memory is reserved for the docker build in the node by the kubernetes
            scheduler.
        node_selector : ignored
        appendix : str
            Appendix to be added at the end of the Dockerfile used by repo2docker.
            Passed through to repo2docker.
        log_tail_lines : int
            Number of log lines to fetch from a currently running build.
            If a build with the same name is already running when submitted,
            only the last `log_tail_lines` number of lines will be fetched and
            displayed to the end user. If not, all log lines will be streamed.
        sticky_builds : ignored
        """
        self.q = q
        self.repo_url = repo_url
        self.ref = ref
        self.name = name
        self.image_name = image_name
        self.push_secret = push_secret
        self.main_loop = IOLoop.current()
        self.memory_limit = memory_limit
        self.memory_request = memory_request
        self.appendix = appendix
        self.log_tail_lines = log_tail_lines

        self.stop_event = Event()
        self.git_credentials = git_credentials

    @classmethod
    def cleanup_builds(cls, kube, namespace, max_age):
        app_log.debug("Not implemented")

    def progress(self, kind: ProgressEvent.Kind, payload: str):
        """
        Put current progress info into the queue on the main thread
        """
        self.main_loop.add_callback(self.q.put, ProgressEvent(kind, payload))

    def get_affinity(self):
        raise NotImplementedError()

    def submit(self):
        """
        Run a build to create the image for the repository.

        Progress of the build can be monitored by listening for items in
        the Queue passed to the constructor as `q`.
        """
        def break_callback():
            return self.stop_event.is_set()

        env = os.environ.copy()
        if self.git_credentials:
            env['GIT_CREDENTIAL_ENV'] = self.git_credentials

        cmd = self.get_cmd()
        app_log.info("Starting build: %s", " ".join(cmd))

        try:
            self.progress(ProgressEvent.Kind.BUILD_STATUS_CHANGE, ProgressEvent.BuildStatus.RUNNING)
            for line in _execute_cmd(cmd, capture=True, break_callback=break_callback, env=env):
                self._handle_log(line)
            self.progress(ProgressEvent.Kind.BUILD_STATUS_CHANGE, ProgressEvent.BuildStatus.COMPLETED)
        except subprocess.CalledProcessError:
            self.progress(ProgressEvent.Kind.BUILD_STATUS_CHANGE, ProgressEvent.BuildStatus.FAILED)
        except Exception:
            app_log.exception("Error in watch stream for %s", self.name)
            raise

    def _handle_log(self, line):
        try:
            json.loads(line)
        except ValueError:
            # log event wasn't JSON.
            # use the line itself as the message with unknown phase.
            # We don't know what the right phase is, use 'unknown'.
            # If it was a fatal error, presumably a 'failure'
            # message will arrive shortly.
            app_log.error("log event not json: %r", line)
            line = json.dumps({
                'phase': 'unknown',
                'message': line,
            })
        self.progress(ProgressEvent.Kind.LOG_MESSAGE, line)

    def stream_logs(self):
        pass

    def cleanup(self):
        pass

    def stop(self):
        self.stop_event.set()
