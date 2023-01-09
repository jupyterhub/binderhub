"""
Contains build of a docker image from a git repository.
"""

import json
import os

# These methods are synchronous so don't use tornado.queue
import queue
import subprocess
from threading import Thread

from tornado.log import app_log
from traitlets import default

from .build import BuildExecutor, ProgressEvent

DEFAULT_READ_TIMEOUT = 1


class ProcessTerminated(subprocess.CalledProcessError):
    """
    Thrown when a process was forcibly terminated
    """

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        s = f"ProcessTerminated: {self.message}"
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


class LocalRepo2dockerBuild(BuildExecutor):
    """Represents a build of a git repository into a docker image.

    This runs a build using the repo2docker command line tool.

    WARNING: This is still under development. Breaking changes may be made at any time.
    """

    @default("builder_info")
    def _default_builder_info(self):
        try:
            import repo2docker

            return {"repo2docker-version": repo2docker.__version__}
        except ImportError:
            self.log.error("repo2docker not installed")
            return {}

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
            env["GIT_CREDENTIAL_ENV"] = self.git_credentials

        cmd = self.get_cmd()
        app_log.info("Starting build: %s", " ".join(cmd))

        try:
            self.progress(
                ProgressEvent.Kind.BUILD_STATUS_CHANGE,
                ProgressEvent.BuildStatus.RUNNING,
            )
            for line in _execute_cmd(
                cmd, capture=True, break_callback=break_callback, env=env
            ):
                self._handle_log(line)
            self.progress(
                ProgressEvent.Kind.BUILD_STATUS_CHANGE,
                ProgressEvent.BuildStatus.BUILT,
            )
        except subprocess.CalledProcessError:
            self.progress(
                ProgressEvent.Kind.BUILD_STATUS_CHANGE, ProgressEvent.BuildStatus.FAILED
            )
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
            line = json.dumps(
                {
                    "phase": "unknown",
                    "message": line,
                }
            )
        self.progress(ProgressEvent.Kind.LOG_MESSAGE, line)
