import asyncio

from tornado.web import authenticated
from tornado.ioloop import IOLoop
from tornado.log import app_log

from ..build import Build, FakeBuild
from ..builder import Builder, BuildFailed, LaunchFailed

from ..base import EventStreamHandler


class BuildHandler(EventStreamHandler):
    """GET /build/:provider/:spec triggers a build and launch

    response is an event stream watching progress as the build and launch proceed
    """

    path = r"/build/([^/]+)/(.+)"

    build = None

    def on_finish(self):
        super().on_finish()
        if self.build:
            # if we have a build, tell it to stop watching
            self.build.stop()

    def initialize(self):
        super().initialize()
        if self.settings['use_registry']:
            self.registry = self.settings['registry']

        self.event_log = self.settings['event_log']

    async def fail(self, message):
        await self.emit({'phase': 'failed', 'message': message + '\n'})

    @authenticated
    async def get(self, provider_prefix, _unescaped_spec):
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
        prefix = '/build/' + provider_prefix
        spec = self.get_spec_from_request(prefix)

        # create a heartbeat
        IOLoop.current().spawn_callback(self.keep_alive)

        spec = spec.rstrip("/")
        key = '%s:%s' % (provider_prefix, spec)

        # get a provider object that encapsulates the provider and the spec
        try:
            provider = self.get_provider(provider_prefix, spec=spec)
        except KeyError:
            await self.fail("No provider found for prefix %r" % provider_prefix)
            return
        except Exception as e:
            app_log.exception("Failed to get provider for %s", key)
            await self.fail(str(e))
            return

        if provider.is_banned():
            await self.emit(
                {
                    'phase': 'failed',
                    'message': 'Sorry, {} has been temporarily disabled from launching. Please contact admins for more info!'.format(
                        spec
                    ),
                }
            )
            return

        origin = (
            self.settings['normalized_origin']
            if self.settings['normalized_origin']
            else self.request.host
        )

        binder_launch_host = self.get_badge_base_url() or '{proto}://{host}{base_url}'.format(
            proto=self.request.protocol,
            host=self.request.host,
            base_url=self.settings['base_url'],
        )

        self.builder = Builder(
            settings=self.settings,
            provider=provider,
            provider_prefix=provider_prefix,
            spec=spec,
            event_log=self.settings['event_log'],
            registry=self.registry if self.settings['use_registry'] else None,
            origin=origin,
            binder_launch_host=binder_launch_host,
        )

        ref = await self.builder.resolve_provider()
        image_found = not await self.builder.image_needs_building()
        image_name = self.builder.image_name

        # Launch a notebook server if the image already is built
        kube = self.settings['kubernetes_client']

        if image_found:
            await self.emit(
                {
                    'phase': 'built',
                    'imageName': image_name,
                    'message': 'Found built image, launching...\n',
                }
            )
            await self.builder.launch()
            return

        # Prepare to build
        build = await self.builder.request_build()
        failed = False
        try:
            async for event in self.builder.watch(stream_logs=True):
                await self.emit(event)
        except BuildFailed:
            # failed event was already emitted!
            print("build failed!")
            failed = True

        # Launch after building an image
        if not failed:
            async for event in self.builder.launch():
                await self.emit(event)

        # Don't close the eventstream immediately.
        # (javascript) eventstream clients reconnect automatically on dropped connections,
        # so if the server closes the connection first,
        # the client will reconnect which starts a new build.
        # If we sleep here, that makes it more likely that a well-behaved
        # client will close its connection first.
        # The duration of this shouldn't matter because
        # well-behaved clients will close connections after they receive the launch event.
        await asyncio.sleep(60)

default_handlers = [BuildHandler]
