"""
Handlers for working with version control services (i.e. GitHub) for builds.
"""

import asyncio
import hashlib
from functools import partial
import json
import string
import time

import docker
import escapism
from tornado.concurrent import chain_future, Future
from tornado import gen
from tornado.queues import Queue
from tornado.ioloop import IOLoop
from tornado.log import app_log
from traitlets import Dict, HasTraits, Instance, Unicode
from prometheus_client import Counter, Histogram, Gauge

from .build import Build, BuildWatcher, FakeBuild
from .events import EventLog
from .registry import DockerRegistry
from .repoproviders import RepoProvider

# Separate buckets for builds and launches.
# Builds and launches have very different characteristic times,
# and there is a cost to having too many buckets in prometheus.
BUILD_BUCKETS = [60, 120, 300, 600, 1800, 3600, 7200, float("inf")]
LAUNCH_BUCKETS = [2, 5, 10, 20, 30, 60, 120, 300, 600, float("inf")]
BUILD_TIME = Histogram(
    'binderhub_build_time_seconds',
    'Histogram of build times',
    ['status'],
    buckets=BUILD_BUCKETS,
)
LAUNCH_TIME = Histogram(
    'binderhub_launch_time_seconds',
    'Histogram of launch times',
    ['status', 'retries'],
    buckets=LAUNCH_BUCKETS,
)
BUILD_COUNT = Counter(
    'binderhub_build_count', 'Counter of builds by repo', ['status', 'provider', 'repo']
)
LAUNCH_COUNT = Counter(
    'binderhub_launch_count',
    'Counter of launches by repo',
    ['status', 'provider', 'repo'],
)
BUILDS_INPROGRESS = Gauge('binderhub_inprogress_builds', 'Builds currently in progress')
LAUNCHES_INPROGRESS = Gauge(
    'binderhub_inprogress_launches', 'Launches currently in progress'
)


class BuildFailed(Exception):
    """Exception to raise when a build fails"""


class LaunchFailed(Exception):
    """Exception to raise when a launch fails"""


class Builder(HasTraits):
    """A handler for working with GitHub."""

    # general application state
    registry = Instance(DockerRegistry, allow_none=True)
    event_log = Instance(EventLog)
    settings = Dict()
    binder_launch_host = Unicode()

    # per-build
    provider_prefix = Unicode()
    provider = Instance(RepoProvider)
    spec = Unicode()
    build = Instance(BuildWatcher)
    origin = Unicode()

    def _generate_build_name(self, build_slug, ref, prefix='', limit=63, ref_length=6):
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

        # escape parts that came from providers (build slug, ref)
        # only build_slug *really* needs this (refs should be sha1 hashes)
        # build names are case-insensitive because ascii_letters are allowed,
        # and `.lower()` is called at the end
        safe_chars = set(string.ascii_letters + string.digits)

        def escape(s):
            return escapism.escape(s, safe=safe_chars, escape_char='-')

        build_slug = self._safe_build_slug(
            build_slug, limit=limit - len(prefix) - ref_length - 1
        )
        ref = escape(ref)

        return '{prefix}{safe_slug}-{ref}'.format(
            prefix=prefix, safe_slug=build_slug, ref=ref[:ref_length]
        ).lower()

    def _safe_build_slug(self, build_slug, limit, hash_length=6):
        """
        This function catches a bug where build slug may not produce a valid image name
        (e.g. repo name ending with _, which results in image name ending with '-' which is invalid).
        This ensures that the image name is always safe, regardless of build slugs returned by providers
        (rather than requiring all providers to return image-safe build slugs below a certain length).
        Since this changes the image name generation scheme, all existing cached images will be invalidated.
        """
        build_slug_hash = hashlib.sha256(build_slug.encode('utf-8')).hexdigest()
        safe_chars = set(string.ascii_letters + string.digits)

        def escape(s):
            return escapism.escape(s, safe=safe_chars, escape_char='-')

        build_slug = escape(build_slug)
        return '{name}-{hash}'.format(
            name=build_slug[: limit - hash_length - 1],
            hash=build_slug_hash[:hash_length],
        ).lower()

    async def fail(self, message):
        await self.emit({'phase': 'failed', 'message': message + '\n'})

    async def resolve_provider(self):

        provider_prefix = self.provider_prefix
        provider = self.provider
        spec = self.spec
        repo_url = self.repo_url = provider.get_repo_url()

        # labels to apply to build/launch metrics
        self.repo_metric_labels = {'provider': provider.name, 'repo': repo_url}

        ref = self.resolved_ref = await provider.get_resolved_ref()

        self.ref_url = await provider.get_resolved_ref_url()
        resolved_spec = await provider.get_resolved_spec()

        # These are relative URLs so do not have a leading /
        self.binder_request = 'v2/{provider}/{spec}'.format(
            provider=provider_prefix, spec=spec
        )
        self.binder_persistent_request = 'v2/{provider}/{spec}'.format(
            provider=provider_prefix, spec=resolved_spec
        )

        # resolve build name as well
        self.build_name = self._generate_build_name(
            provider.get_build_slug(), ref, prefix='build-'
        )
        return ref

    async def image_needs_building(self):

        # generate a complete build name (for GitHub: `build-{user}-{repo}-{ref}`)

        image_prefix = self.settings['image_prefix']

        # Enforces max 255 characters before image
        safe_build_slug = self._safe_build_slug(
            self.provider.get_build_slug(), limit=255 - len(image_prefix)
        )

        image_name = self.image_name = (
            '{prefix}{build_slug}:{ref}'.format(
                prefix=image_prefix, build_slug=safe_build_slug, ref=self.resolved_ref
            )
            .replace('_', '-')
            .lower()
        )

        if self.settings['use_registry']:
            image_manifest = await self.registry.get_image_manifest(
                *'/'.join(image_name.split('/')[-2:]).split(':', 1)
            )
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

        return image_found

    async def request_build(self):

        # Launch a notebook server if the image already is built
        kube = self.settings['kubernetes_client']
        repo_url = self.repo_url
        ref = self.resolved_ref
        image_name = self.image_name
        provider = self.provider

        # Prepare to build
        q = self.event_queue = Queue()

        if self.settings['use_registry']:
            push_secret = self.settings['push_secret']
        else:
            push_secret = None

        BuildClass = FakeBuild if self.settings.get('fake_build') else Build

        appendix = self.settings['appendix'].format(
            binder_url=self.binder_launch_host + self.binder_request,
            persistent_binder_url=self.binder_launch_host
            + self.binder_persistent_request,
            repo_url=repo_url,
            ref_url=self.ref_url,
        )

        self.build = build = BuildClass(
            q=q,
            api=kube,
            name=self.build_name,
            namespace=self.settings["build_namespace"],
            repo_url=repo_url,
            ref=ref,
            image_name=image_name,
            push_secret=push_secret,
            build_image=self.settings['build_image'],
            memory_limit=self.settings['build_memory_limit'],
            docker_host=self.settings['build_docker_host'],
            node_selector=self.settings['build_node_selector'],
            appendix=appendix,
            log_tail_lines=self.settings['log_tail_lines'],
            git_credentials=provider.git_credentials,
            sticky_builds=self.settings['sticky_builds'],
        )
        pool = self.settings['build_pool']

        async def submit_with_timing():
            with BUILDS_INPROGRESS.track_inprogress():
                self.build_starttime = time.perf_counter()
                await asyncio.wrap_future(pool.submit(build.submit))

        IOLoop.current().add_callback(submit_with_timing)

        return build

    async def watch(self, stream_logs=True):
        pool = self.settings['build_pool']
        if self.build is None:
            BuildWatcherClass = (
                FakeBuild if self.settings.get('fake_build') else BuildWatcher
            )
            q = Queue()
            self.build = BuildWatcherClass(
                q=q,
                api=self.settings['kubernetes'],
                name=self.build_name,
                namespace=self.settings['build_namespace'],
            )
            # call watch when we are instantiating a Watcher
            #
            IOLoop.current().add_callback(partial(pool.submit, self.build.watch))
        else:
            # if this happens, we already invoked .request_build()
            # which itself called build.watch()
            pass

        build = self.build

        # initial waiting event
        yield {'phase': 'waiting', 'message': 'Waiting for build to start...\n'}

        # wait for the first of:
        # 1. build is ready to start streaming logs, or
        # 2. build has stopped (success or failure)

        await asyncio.wait([self.build.stopped_future, self.build.running_future])
        if self.build.stopped_future.done():
            # ...
            return

        q = self.build.q

        log_future = None

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
                        'imageName': self.image_name,
                    }
                    done = True
                elif progress['payload'] == 'Running':
                    # start capturing build logs once the pod is running
                    if log_future is None and stream_logs:
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
                if payload.get('phase') in ('failure', 'failed'):
                    failed = True
                    BUILD_TIME.labels(status='failure').observe(
                        time.perf_counter() - self.build_starttime
                    )
                    BUILD_COUNT.labels(
                        status='failure', **self.repo_metric_labels
                    ).inc()

            yield event

        if failed:
            raise BuildFailed()
        else:
            BUILD_TIME.labels(status='success').observe(
                time.perf_counter() - self.build_starttime
            )
            BUILD_COUNT.labels(status='success', **self.repo_metric_labels).inc()

    async def launch(self):
        """Ask JupyterHub to launch the image.

        Wraps _launch in timing metrics
        """
        with LAUNCHES_INPROGRESS.track_inprogress():
            async for event in self._launch(
                self.settings['kubernetes_client'], self.provider
            ):
                yield event
        self.event_log.emit(
            'binderhub.jupyter.org/launch',
            3,
            {
                'provider': self.provider.name,
                'spec': self.spec,
                'status': 'success',
                'origin': self.origin,
            },
        )

    async def _launch(self, kube, provider):
        """Ask JupyterHub to launch the image.

        This private method"""
        # Load the spec-specific configuration if it has been overridden
        repo_config = provider.repo_config(self.settings)

        # the image name (without tag) is unique per repo
        # use this to count the number of pods running with a given repo
        # if we added annotations/labels with the repo name via KubeSpawner
        # we could do this better
        image_no_tag = self.image_name.rsplit(':', 1)[0]
        matching_pods = 0
        total_pods = 0

        # TODO: run a watch to keep this up to date in the background
        pool = self.settings['executor']
        f = pool.submit(
            kube.list_namespaced_pod,
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

        # TODO: put busy users in a queue rather than fail?
        # That would be hard to do without in-memory state.
        quota = repo_config.get('quota')
        if quota and matching_pods >= quota:
            app_log.error(
                "%s has exceeded quota: %s/%s (%s total)",
                self.repo_url,
                matching_pods,
                quota,
                total_pods,
            )
            raise LaunchFailed(
                "Too many users running %s! Try again soon." % self.repo_url
            )

        if quota and matching_pods >= 0.5 * quota:
            log = app_log.warning
        else:
            log = app_log.info
        log(
            "Launching pod for %s: %s other pods running this repo (%s total)",
            self.repo_url,
            matching_pods,
            total_pods,
        )

        yield {'phase': 'launching', 'message': 'Launching server...\n'}

        launcher = self.settings['launcher']
        retry_delay = launcher.retry_delay
        for i in range(launcher.retries):
            launch_starttime = time.perf_counter()
            if self.settings['auth_enabled']:
                # get logged in user's name
                user_model = self.hub_auth.get_user(self)
                username = user_model['name']
                if launcher.allow_named_servers:
                    # user can launch multiple servers, so create a unique server name
                    server_name = launcher.unique_name_from_repo(self.repo_url)
                else:
                    server_name = ''
            else:
                # create a name for temporary user
                username = launcher.unique_name_from_repo(self.repo_url)
                server_name = ''
            try:
                extra_args = {
                    'binder_ref_url': self.ref_url,
                    'binder_launch_host': self.binder_launch_host,
                    'binder_request': self.binder_request,
                    'binder_persistent_request': self.binder_persistent_request,
                }
                server_info = await launcher.launch(
                    image=self.image_name,
                    username=username,
                    server_name=server_name,
                    repo_url=self.repo_url,
                    extra_args=extra_args,
                )
                LAUNCH_TIME.labels(status='success', retries=i).observe(
                    time.perf_counter() - launch_starttime
                )
                LAUNCH_COUNT.labels(status='success', **self.repo_metric_labels).inc()

            except Exception as e:
                if i + 1 == launcher.retries:
                    status = 'failure'
                else:
                    status = 'retry'
                # don't count retries in failure/retry
                # retry count is only interesting in success
                LAUNCH_TIME.labels(status=status, retries=-1).observe(
                    time.perf_counter() - launch_starttime
                )
                if status == 'failure':
                    # don't count retries per repo
                    LAUNCH_COUNT.labels(status=status, **self.repo_metric_labels).inc()

                if i + 1 == launcher.retries:
                    # last attempt failed, let it raise
                    raise

                # not the last attempt, try again
                app_log.error("Retrying launch after error: %s", e)
                yield {
                    'phase': 'launching',
                    'message': 'Launch attempt {} failed, retrying...\n'.format(i + 1),
                }

                await asyncio.sleep(retry_delay)
                # exponential backoff for consecutive failures
                retry_delay *= 2
                continue
            else:
                # success
                break
        event = {
            'phase': 'ready',
            'message': 'server running at %s\n' % server_info['url'],
        }
        event.update(server_info)
        yield event
