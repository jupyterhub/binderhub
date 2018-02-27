"""
Handlers for working with version control services (i.e. GitHub) for builds.
"""

import hashlib
from http.client import responses
import json
import string
import time
import escapism

import docker
from kubernetes import client
from tornado.concurrent import chain_future, Future
from tornado import gen, web
from tornado.queues import Queue
from tornado.iostream import StreamClosedError
from tornado.ioloop import IOLoop
from tornado.log import app_log
from prometheus_client import Histogram, Gauge

from .base import BaseHandler
from .build import Build, FakeBuild
BUCKETS = [2, 5, 10, 15, 20, 25, 30, 60, 120, 240, 480, 960, 1920, float("inf")]
BUILD_TIME = Histogram('binderhub_build_time_seconds', 'Histogram of build times', ['status'], buckets=BUCKETS)
LAUNCH_TIME = Histogram('binderhub_launch_time_seconds', 'Histogram of launch times', ['status'], buckets=BUCKETS)
BUILDS_INPROGRESS = Gauge('binderhub_inprogress_builds', 'Builds currently in progress')
LAUNCHES_INPROGRESS = Gauge('binderhub_inprogress_launches', 'Launches currently in progress')


class BuildHandler(BaseHandler):
    """A handler for working with GitHub."""
    # emit keepalives every 25 seconds to avoid idle connections being closed
    KEEPALIVE_INTERVAL = 25

    async def emit(self, data):
        if type(data) is not str:
            serialized_data = json.dumps(data)
        else:
            serialized_data = data
        try:
            self.write('data: {}\n\n'.format(serialized_data))
            await self.flush()
        except StreamClosedError:
            app_log.warning("Stream closed while handling %s", self.request.uri)
            # raise Finish to halt the handler
            raise web.Finish()

    def on_finish(self):
        """Stop keepalive when finish has been called"""
        self._keepalive = False

    async def keep_alive(self):
        """Constantly emit keepalive events

        So that intermediate proxies don't terminate an idle connection
        """
        self._keepalive = True
        while True:
            await gen.sleep(self.KEEPALIVE_INTERVAL)
            if not self._keepalive:
                return
            try:
                # lines that start with : are comments
                # and should be ignored by event consumers
                self.write(':keepalive\n\n')
                await self.flush()
            except StreamClosedError:
                return

    def send_error(self, status_code, **kwargs):
        """event stream cannot set an error code, so send an error event"""
        exc_info = kwargs.get('exc_info')
        message = ''
        if exc_info:
            message = self.extract_message(exc_info)
        if not message:
            message = responses.get(status_code, 'Unknown HTTP Error')

        # this cannot be async
        evt = json.dumps({
            'phase': 'failed',
            'status_code': status_code,
            'message': message + '\n',
        })
        self.write('data: {}\n\n'.format(evt))
        self.finish()

    def initialize(self):
        if self.settings['use_registry']:
            self.registry = self.settings['registry']

    def _generate_build_name(self, build_slug, ref, prefix='', limit=63, hash_length=6, ref_length=6):
        """
        Generate a unique build name with a limited character length..

        Guaranteed (to acceptable level) to be unique for a given user, repo,
        and ref.

        We really, *really* care that we always end up with the same
        'build_name' for a particular repo + ref, but the default max
        character limit for build names is 63. To meet this constraint, we
        include a prefixed hash of the user / repo in all build names and do
        some length limiting :)

        Note that ``build`` names only need to be unique over a shorter period
        of time, while ``image`` names need to be unique for longer. Hence,
        different strategies are used.

        We also ensure that the returned value is DNS safe, by only using
        ascii lowercase + digits. everything else is escaped
        """
        build_slug_hash = hashlib.sha256(build_slug.encode('utf-8')).hexdigest()

        # escape parts that came from providers (build slug, ref)
        # only build_slug *really* needs this (refs should be sha1 hashes)
        # build names are case-insensitive because ascii_letters are allowed,
        # and `.lower()` is called at the end
        safe_chars = set(string.ascii_letters + string.digits)
        def escape(s):
            return escapism.escape(s, safe=safe_chars, escape_char='-')
        build_slug = escape(build_slug)
        ref = escape(ref)

        return '{prefix}{name}-{hash}-{ref}'.format(
            prefix=prefix,
            name=build_slug[:limit - hash_length - ref_length - len(prefix) - 2],
            hash=build_slug_hash[:hash_length],
            ref=ref[:ref_length],
        ).lower()

    async def fail(self, message):
        await self.emit({
            'phase': 'failed',
            'message': message + '\n',
        })

    async def get(self, provider_prefix, spec):
        """Get a built image for a given spec and repo provider.

        Different repo providers will require different spec information. This
        function relies on the functionality of the tornado `GET` request.

        Parameters
        ----------
            provider_prefix : str
                the nickname for a repo provider (i.e. 'gh')
            spec:
                specifies information needed by the repo provider (i.e. user,
                repo, ref, etc.)

        """
        # set up for sending event streams
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

        # Verify if the provider is valid for EventSource.
        # EventSource cannot handle HTTP errors, so we must validate and send
        # error messages on the eventsource.
        if provider_prefix not in self.settings['repo_providers']:
            await self.fail("No provider found for prefix %s" % provider_prefix)
            return

        # create a heartbeat
        IOLoop.current().spawn_callback(self.keep_alive)

        key = '%s:%s' % (provider_prefix, spec)

        # get a provider object that encapsulates the provider and the spec
        try:
            provider = self.get_provider(provider_prefix, spec=spec)
        except Exception as e:
            app_log.exception("Failed to get provider for %s", key)
            await self.fail(str(e))
            return

        if provider.is_banned():
            await self.emit({
                'phase': 'failed',
                'message': 'Sorry, {} has been temporarily disabled from launching. Please contact admins for more info!'.format(spec)
            })
            return

        repo = self.repo = provider.get_repo_url()

        try:
            ref = await provider.get_resolved_ref()
        except Exception as e:
            await self.fail("Error resolving ref for %s: %s" % (key, e))
            return
        if ref is None:
            await self.fail("Could not resolve ref for %s. Double check your URL." % key)
            return

        # generate a complete build name (for GitHub: `build-{user}-{repo}-{ref}`)
        build_name = self._generate_build_name(provider.get_build_slug(), ref, prefix='build-')

        # FIXME: EnforceMax of 255 before image and 128 for tag
        image_name = self.image_name = '{prefix}{build_slug}:{ref}'.format(
            prefix=self.settings['docker_image_prefix'],
            build_slug=provider.get_build_slug(), ref=ref
        ).replace('_', '-').lower()

        if self.settings['use_registry']:
            image_manifest = await self.registry.get_image_manifest(*image_name.split('/', 1)[1].split(':', 1))
            image_found = bool(image_manifest)
        else:
            # Check if the image exists locally!
            # Assume we're running in single-node mode or all binder pods are assigned to the same node!
            docker_client = docker.from_env(version='auto')
            try:
                docker_client.images.get(image_name)
            except docker.errors.ImageNotFound:
                # image doesn't exist, so do a build!
                image_found = False
            else:
                image_found = True

        # Launch a notebook server if the image already is built
        kube = client.CoreV1Api()

        if image_found:
            await self.emit({
                'phase': 'built',
                'imageName': image_name,
                'message': 'Found built image, launching...\n'
            })
            await self.launch(kube)
            return

        # Prepare to build
        q = Queue()

        if self.settings['use_registry']:
            push_secret = self.settings['docker_push_secret']
        else:
            push_secret = None

        BuildClass = FakeBuild if self.settings.get('fake_build', None) else Build

        build = BuildClass(
            q=q,
            api=kube,
            name=build_name,
            namespace=self.settings["build_namespace"],
            git_url=repo,
            ref=ref,
            image_name=image_name,
            push_secret=push_secret,
            builder_image=self.settings['builder_image_spec'],
            memory_limit=self.settings['build_memory_limit'],
            docker_host=self.settings['build_docker_host'],
            node_selector=self.settings['build_node_selector']
        )

        with BUILDS_INPROGRESS.track_inprogress():
            build_starttime = time.perf_counter()
            pool = self.settings['build_pool']
            """----- Build starts here -----"""
            submit_future = pool.submit(build.submit)
            # TODO: hook up actual error handling when this fails
            IOLoop.current().add_callback(lambda : submit_future)

            log_future = None

            # initial waiting event
            await self.emit({
                'phase': 'waiting',
                'message': 'Waiting for build to start...\n',
            })

            done = False
            failed = False
            while not done:
                progress = await q.get()

                # FIXME: If pod goes into an unrecoverable stage, such as ImagePullBackoff or
                # whatever, we should fail properly.
                if progress['kind'] == 'pod.phasechange':
                    if progress['payload'] == 'Pending':
                        # nothing to do, just waiting
                        continue
                    elif progress['payload'] == 'Deleted':
                        event = {
                            'phase': 'built',
                            'message': 'Built image, launching...\n',
                            'imageName': image_name,
                        }
                        done = True
                    elif progress['payload'] == 'Running':
                        # start capturing build logs once the pod is running
                        if log_future is None:
                            log_future = pool.submit(build.stream_logs)
                        continue
                    elif progress['payload'] == 'Succeeded':
                        # Do nothing, is ok!
                        continue
                    else:
                        # FIXME: message? debug?
                        event = {'phase': progress['payload']}
                elif progress['kind'] == 'log':
                    # We expect logs to be already JSON structured anyway
                    event = progress['payload']
                    payload = json.loads(event)
                    if payload.get('phase', None) == 'failure':
                        failed = True
                        BUILD_TIME.labels(status='failure').observe(time.perf_counter() - build_starttime)

                await self.emit(event)

        # Launch after building an image
        if not failed:
            BUILD_TIME.labels(status='success').observe(time.perf_counter() - build_starttime)
            with LAUNCHES_INPROGRESS.track_inprogress():
                await self.launch(kube)

        # Don't close the eventstream immediately.
        # (javascript) eventstream clients reconnect automatically on dropped connections,
        # so if the server closes the connection first,
        # the client will reconnect which starts a new build.
        # If we sleep here, that makes it more likely that a well-behaved
        # client will close its connection first.
        # The duration of this shouldn't matter because
        # well-behaved clients will close connections after they receive the launch event.
        await gen.sleep(60)

    async def launch(self, kube):
        """Ask JupyterHub to launch the image."""
        # check quota first
        quota = self.settings.get('per_repo_quota')

        # the image name (without tag) is unique per repo
        # use this to count the number of pods running with a given repo
        # if we added annotations/labels with the repo name via KubeSpawner
        # we could do this better
        image_no_tag = self.image_name.rsplit(':', 1)[0]
        matching_pods = 0
        total_pods = 0

        # TODO: run a watch to keep this up to date in the background
        pool = self.settings['build_pool']
        f = pool.submit(kube.list_namespaced_pod,
            self.settings["build_namespace"],
            label_selector='app=jupyterhub,component=singleuser-server',
        )
        # concurrent.futures.Future isn't awaitable
        # wrap in tornado Future
        # tornado 5 will have `.run_in_executor`
        tf = Future()
        chain_future(f, tf)
        pods = await tf
        for pod in pods.items:
            total_pods += 1
            for container in pod.spec.containers:
                # is the container running the same image as us?
                # if so, count one for the current repo.
                image = container.image.rsplit(':', 1)[0]
                if image == image_no_tag:
                    matching_pods += 1
                    break

        # TODO: allow whitelist of repos to exceed quota
        # TODO: put busy users in a queue rather than fail?
        # That would be hard to do without in-memory state.
        if quota and matching_pods >= quota:
            app_log.error("%s has exceeded quota: %s/%s (%s total)",
                self.repo, matching_pods, quota, total_pods)
            await self.fail("Too many users running %s! Try again soon." % self.repo)
            return

        if quota and matching_pods >= 0.5 * quota:
            log = app_log.warning
        else:
            log = app_log.info
        log("Launching pod for %s: %s other pods running this repo (%s total)",
            self.repo, matching_pods, total_pods)

        await self.emit({
            'phase': 'launching',
            'message': 'Launching server...\n',
        })

        launcher = self.settings['launcher']
        username = launcher.username_from_repo(self.repo)
        try:
            launch_starttime = time.perf_counter()
            server_info = await launcher.launch(image=self.image_name, username=username)
            LAUNCH_TIME.labels(status='success').observe(time.perf_counter() - launch_starttime)
        except:
            LAUNCH_TIME.labels(status='failure').observe(time.perf_counter() - launch_starttime)
            raise
        event = {
            'phase': 'ready',
            'message': 'server running at %s\n' % server_info['url'],
        }
        event.update(server_info)
        await self.emit(event)
