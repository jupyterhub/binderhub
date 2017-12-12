"""
Handlers for working with version control services (i.e. GitHub) for builds.
"""

import hashlib
from http.client import responses
import json
import threading
import string
import time
import escapism

import docker
from kubernetes import client
from tornado import gen, web
from tornado.queues import Queue
from tornado.iostream import StreamClosedError
from tornado.ioloop import IOLoop
from tornado.log import app_log
from prometheus_client import Histogram, Gauge, Counter

from .base import BaseHandler
from .build import Build, FakeBuild


BUILD_TIME = Histogram('binderhub_build_time_seconds', 'Histogram of build times', ['status'], buckets=[1, 5, 10, 30, 60, 300, 600, float("inf")])
LAUNCH_TIME = Histogram('binderhub_launch_time_seconds', 'Histogram of launch times', ['status'], buckets=[1, 5, 10, 30, 60, 300, 600, float("inf")])
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
        """Get a built image for a given GitHub user, repo, and ref."""
        # We gonna send out event streams!
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

        # EventSource cannot handle HTTP errors,
        # so we have to send error messages on the eventsource
        if provider_prefix not in self.settings['repo_providers']:
            await self.fail("No provider found for prefix %s" % provider_prefix)
            return

        IOLoop.current().spawn_callback(self.keep_alive)

        key = '%s:%s' % (provider_prefix, spec)

        try:
            provider = self.get_provider(provider_prefix, spec=spec)
        except Exception as e:
            app_log.exception("Failed to get provider for %s", key)
            await self.fail(str(e))
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
        build_name = self._generate_build_name(provider.get_build_slug(), ref, prefix='build-')

        # FIXME: EnforceMax of 255 before image and 128 for tag
        image_name = self.image_name = '{prefix}{build_slug}:{ref}'.format(
            prefix=self.settings['docker_image_prefix'],
            build_slug=provider.get_build_slug(), ref=ref
        ).replace('_', '-').lower()

        image_manifest = await self.registry.get_image_manifest(*image_name.split('/', 1)[1].rsplit(':', 1))
        image_found = bool(image_manifest)

        if image_found:
            await self.emit({
                'phase': 'built',
                'imageName': image_name,
                'message': 'Found built image, launching...\n'
            })
            await self.launch()
            return

        api = client.CoreV1Api()

        q = Queue()

        push_secret = self.settings['docker_push_secret']

        BuildClass = FakeBuild if self.settings.get('fake_build', None) else Build

        build = BuildClass(
            q=q,
            api=api,
            name=build_name,
            namespace=self.settings["build_namespace"],
            git_url=repo,
            ref=ref,
            image_name=image_name,
            push_secret=push_secret,
            builder_image=self.settings['builder_image_spec'],
            memory_limit=self.settings['build_memory_limit'],
            docker_host=self.settings['build_docker_host']
        )

        with BUILDS_INPROGRESS.track_inprogress():
            build_starttime = time.perf_counter()
            pool = self.settings['build_pool']
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

        if not failed:
            BUILD_TIME.labels(status='success').observe(time.perf_counter() - build_starttime)
            with LAUNCHES_INPROGRESS.track_inprogress():
                await self.launch()


    async def launch(self):
        """Ask the Hub to launch the image"""
        await self.emit({
            'phase': 'launching',
            'message': 'Launching server...\n',
        })
        # build finished, time to launch!
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
