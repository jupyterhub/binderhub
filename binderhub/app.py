"""
The binderhub application
"""
from concurrent.futures import ThreadPoolExecutor
import logging
import os

from jinja2 import Environment, FileSystemLoader
import tornado.ioloop
import tornado.options
import tornado.log
import tornado.web
from traitlets import Unicode, Integer, Bool, Dict, validate
from traitlets.config import Application

from .base import Custom404
from .builder import BuildHandler
from .redirect import RedirectHandler
from .registry import DockerRegistry
from .main import MainHandler, ParameterizedMainHandler, LegacyRedirectHandler
from .repoproviders import RepoProvider, GitHubRepoProvider

TEMPLATE_PATH = [os.path.join(os.path.dirname(__file__), 'templates')]


class BinderHub(Application):
    """An Application for starting a builder."""
    aliases = {
        'log-level': 'Application.log_level',
        'f': 'BinderHub.config_file',
        'config': 'BinderHub.config_file',
        'port': 'BinderHub.port',
    }
    flags = {
        'debug': (
            {'Application': {'log_level': logging.DEBUG}},
            "Enable debug-level logging",
        ),
    }

    config_file = Unicode(
        'binderhub_config.py',
        help="""
        Config file to load.

        If a relative path is provided, it is taken relative to current directory
        """,
        config=True
    )

    google_analytics_code = Unicode(
        None,
        allow_none=True,
        help="""
        The Google Analytics code to use on the main page.

        Note that we'll respect Do Not Track settings, despite the fact that GA does not.
        We will not load the GA scripts on browsers with DNT enabled.
        """,
        config=True
    )

    port = Integer(
        8585,
        help="""
        Port for the builder to listen on.
        """,
        config=True
    )

    use_registry = Bool(
        True,
        help="""
        Set to true to push images to a registry & check for images in registry.

        Set to false to use only local docker images. Useful when running
        in a single node.
        """,
        config=True
    )

    docker_push_secret = Unicode(
        'docker-push-secret',
        allow_none=True,
        help="""
        A kubernetes secret object that provides credentials for pushing built images.
        """,
        config=True
    )

    docker_image_prefix = Unicode(
        "",
        help="""
        Prefix for all built docker images.

        If you are pushing to gcr.io, you would have this be:
            gcr.io/<your-project-name>/

        Set according to whatever registry you are pushing to.

        Defaults to "", which is probably not what you want :)
        """,
        config=True
    )

    # TODO: Factor this out!
    github_auth_token = Unicode(
        None,
        allow_none=True,
        help="""
        GitHub OAuth token to use for talking to the GitHub API.

        Might get throttled otherwise!
        """,
        config=True
    )

    debug = Bool(
        False,
        help="""
        Turn on debugging.
        """,
        config=True
    )

    hub_api_token = Unicode(
        help="""API token for talking to the JupyterHub API""",
        config=True,
    )
    hub_url = Unicode(
        help="""
        The base URL of the JupyterHub instance where users will run.

        e.g. https://hub.mybinder.org/
        """,
        config=True,
    )
    @validate('hub_url')
    def _add_slash(self, proposal):
        """trait validator to ensure hub_url ends with a trailing slash"""
        if proposal.value is not None and not proposal.value.endswith('/'):
            return proposal.value + '/'
        return proposal.value

    build_namespace = Unicode(
        'default',
        help="""
        Kubernetes namespace to spawn build pods in.

        Note that the docker_push_secret must refer to a secret in this namespace.
        """,
        config=True
    )

    builder_image_spec = Unicode(
        'jupyter/repo2docker:v0.4.1',
        help="""
        The builder image to be used for doing builds
        """,
        config=True
    )

    repo_providers = Dict(
        {'gh': GitHubRepoProvider},
        config=True,
        help="""
        List of Repo Providers to register and try
        """
    )
    concurrent_build_limit = Integer(
        32,
        config=True,
        help="""The number of concurrent builds to allow.""")

    def initialize(self, *args, **kwargs):
        """Load configuration settings."""
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)
        # hook up tornado logging
        tornado.options.logging = logging.getLevelName(self.log_level)
        tornado.log.enable_pretty_logging()
        self.log = tornado.log.app_log

        # times 2 for log + build threads
        build_pool = ThreadPoolExecutor(self.concurrent_build_limit * 2)

        jinja_options = dict(autoescape=True, )
        jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH), **jinja_options)
        if self.use_registry:
            registry = DockerRegistry(self.docker_image_prefix.split('/', 1)[0])
        else:
            registry = None

        self.tornado_settings = {
            "docker_push_secret": self.docker_push_secret,
            "docker_image_prefix": self.docker_image_prefix,
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "github_auth_token": self.github_auth_token,
            "debug": self.debug,
            'hub_url': self.hub_url,
            'hub_api_token': self.hub_api_token,
            "build_namespace": self.build_namespace,
            "builder_image_spec": self.builder_image_spec,
            'build_pool': build_pool,
            'repo_providers': self.repo_providers,
            'use_registry': self.use_registry,
            'registry': registry,
            'traitlets_config': self.config,
            'google_analytics_code': self.google_analytics_code,
            'jinja2_env': jinja_env,
        }

        self.tornado_app = tornado.web.Application([
            (r"/build/([^/]+)/(.+)", BuildHandler),
            (r"/run", RedirectHandler),
            (r"/v2/([^/]+)/(.+)", ParameterizedMainHandler),
            (r"/repo/([^/]+)/([^/]+)", LegacyRedirectHandler),
            # for backward-compatible mybinder.org badge URLs
            # /assets/images/badge.svg
            (r'/assets/(images/badge\.svg)',
                tornado.web.StaticFileHandler,
                {'path': self.tornado_settings['static_path']}),
            # /badge.svg
            (r'/(badge\.svg)',
                tornado.web.StaticFileHandler,
                {'path': os.path.join(self.tornado_settings['static_path'], 'images')}),
            (r'/', MainHandler),
            (r'.*', Custom404),
        ], **self.tornado_settings)

    def start(self):
        self.log.info("BinderHub starting on port %i", self.port)
        self.tornado_app.listen(self.port)
        tornado.ioloop.IOLoop.current().start()


main = BinderHub.launch_instance

if __name__ == '__main__':
    main()
