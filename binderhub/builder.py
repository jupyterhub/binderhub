"""
Handlers for working with version control services (i.e. GitHub) for builds.
"""

import hashlib
import json
from queue import Queue, Empty
import threading

import docker
from kubernetes import client, config
from tornado import web, gen
from tornado.iostream import StreamClosedError
from tornado.log import app_log

from .base import BaseHandler
from .build import Build


class BuildHandler(BaseHandler):
    """A handler for working with GitHub."""

    @gen.coroutine
    def emit(self, data):
        if type(data) is not str:
            serialized_data = json.dumps(data)
        else:
            serialized_data = data
        self.write('data: {}\n\n'.format(serialized_data))
        yield self.flush()

    def initialize(self):
        if self.settings['use_registry']:
            self.registry = self.settings['registry']

    def _generate_build_name(self, build_slug, ref, limit=63, hash_length=6, ref_length=6):
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

        TODO: Make sure that the returned value matches the k8s name
        validation regex, which is:
        [a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*

        """
        build_slug_hash = hashlib.sha256(build_slug.encode('utf-8')).hexdigest()

        return '{name}-{hash}-{ref}'.format(
            name=build_slug[:limit - hash_length - ref_length - 2],
            hash=build_slug_hash[:hash_length],
            ref=ref[:ref_length]
        ).lower()

    @gen.coroutine
    def fail(self, message):
        self.emit({
            'phase': 'failed',
            'message': message + '\n',
        })

    @gen.coroutine
    def get(self, provider_prefix, spec):
        """Get a built image for a given GitHub user, repo, and ref."""
        # We gonna send out event streams!
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

        # EventSource cannot handle HTTP errors,
        # so we have to send error messages on the eventsource
        if provider_prefix not in self.settings['repo_providers']:
            yield self.fail("No provider found for prefix %s" % provider_prefix)
            return

        key = '%s:%s' % (provider_prefix, spec)

        try:
            provider = self.get_provider(provider_prefix, spec=spec)
        except Exception as e:
            app_log.exception("Failed to get provider for %s", key)
            yield self.fail(str(e))
            return

        ref = yield provider.get_resolved_ref()
        if ref is None:
            yield self.fail("Could not resolve ref for %s. Double check your URL." % key)
            return
        build_name = self._generate_build_name(provider.get_build_slug(), ref).replace('_', '-')

        # FIXME: EnforceMax of 255 before image and 128 for tag
        image_name = '{prefix}{build_slug}:{ref}'.format(
            prefix=self.settings['docker_image_prefix'],
            build_slug=provider.get_build_slug(), ref=ref
        ).replace('_', '-').lower()

        if self.settings['use_registry']:
            image_manifest = yield self.registry.get_image_manifest(*image_name.split('/', 1)[1].split(':', 1))
            if image_manifest:
                self.emit({
                    'phase': 'built',
                    'imageName': image_name,
                    'message': 'Found built image, launching...\n'
                })
                return
        else:
            # Check if the image exists locally!
            # Assume we're running in single-node mode!
            docker_client = docker.from_env(version='auto')
            try:
                image = docker_client.images.get(image_name)
                self.emit({
                    'phase': 'built',
                    'imageName': image_name,
                    'message': 'Found built image, launching...\n'
                })
                return
            except docker.errors.ImageNotFound:
                # image doesn't exist, so do a build!
                pass

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        api = client.CoreV1Api()

        q = Queue()

        if self.settings['use_registry']:
            push_secret = self.settings['docker_push_secret']
        else:
            push_secret = None

        build = Build(
            q=q,
            api=api,
            name=build_name,
            namespace=self.settings["build_namespace"],
            git_url=provider.get_repo_url(),
            ref=ref,
            image_name=image_name,
            push_secret=push_secret,
            builder_image=self.settings['builder_image_spec']
        )

        # FIXME: use a thread pool
        build_thread = threading.Thread(target=build.submit)
        log_thread = threading.Thread(target=build.stream_logs)

        build_thread.start()

        done = False

        while True:
            # FIXME: use Futures
            try:
                progress = q.get_nowait()
            except Empty:
                yield gen.sleep(0.5)
                continue

            # FIXME: If pod goes into an unrecoverable stage, such as ImagePullBackoff or
            # whatever, we should fail properly.
            if progress['kind'] == 'pod.phasechange':
                if progress['payload'] == 'Pending':
                    event = {'message': 'Waiting for build to start...\n', 'phase': 'waiting'}
                elif progress['payload'] == 'Deleted':
                    event = {
                        'phase': 'built',
                        'message': 'Built image, launching...\n',
                        'imageName': image_name
                    }
                    done = True
                elif progress['payload'] == 'Running':
                    if not log_thread.is_alive():
                        log_thread.start()
                    continue
                elif progress['payload'] == 'Succeeded':
                    # Do nothing, is ok!
                    continue
                else:
                    event = {'phase': progress['payload']}
            elif progress['kind'] == 'log':
                # We expect logs to be already JSON structured anyway
                event = progress['payload']

            try:
                yield self.emit(event)
                q.task_done()
                if done:
                    break
            except StreamClosedError:
                # Client has gone away!
                break
