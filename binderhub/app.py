"""The binderhub application"""

import logging
import os

import tornado.ioloop
import tornado.options
import tornado.log
import tornado.web
from traitlets import Unicode, Integer, Bool, Dict
from traitlets.config import Application

from .builder import BuildHandler
from .redirect import RedirectHandler
from .main import MainHandler, ParameterizedMainHandler, LegacyRedirectHandler
from .repoproviders import RepoProvider, GitHubRepoProvider


class BinderHub(Application):
    """An Application for starting a builder."""
    config_file = Unicode(
        'binderhub_config.py',
        help="""
        Config file to load.

        If a relative path is provided, it is taken relative to current directory
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

    hub_login_url = Unicode(
        None,
        allow_none=True,
        help="""
        The hub login URL to redirect the user to after image is built.

        It'll get all runtime parameters as query parameters, and it is the responsibility
        of the hub to launch this properly
        """,
        config=True
    )

    build_namespace = Unicode(
        'default',
        help="""
        Kubernetes namespace to spawn build pods in.

        Note that the docker_push_secret must refer to a secret in this namespace.
        """,
        config=True
    )

    builder_image_spec = Unicode(
        'jupyter/repo2docker:v0.2.5',
        help="""
        The builder image to be used for doing builds
        """,
        config=True
    )

    repo_providers = Dict(
        { 'gh': GitHubRepoProvider },
        config=True,
        help="""
        List of Repo Providers to register and try
        """
    )

    def initialize(self, *args, **kwargs):
        """Load configuration settings."""
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)
        # hook up tornado logging
        tornado.options.logging = logging.getLevelName(self.log_level)
        tornado.log.enable_pretty_logging()
        self.log = tornado.log.app_log

        self.tornado_settings = {
            "docker_push_secret": self.docker_push_secret,
            "docker_image_prefix": self.docker_image_prefix,
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "github_auth_token": self.github_auth_token,
            "debug": self.debug,
            'hub_login_url': self.hub_login_url,
            "build_namespace": self.build_namespace,
            "builder_image_spec": self.builder_image_spec,
            'repo_providers': self.repo_providers,
            'use_registry': self.use_registry,
            'traitlets_config': self.config
        }

        self.tornado_app = tornado.web.Application([
            (r"/build/([^/]+)/(.+)", BuildHandler),
            (r"/run", RedirectHandler),
            (r"/v2/([^/]+)/(.+)", ParameterizedMainHandler),
            (r"/repo/([^/]+)/([^/]+)", LegacyRedirectHandler),
            (r'/', MainHandler)
        ], **self.tornado_settings)

    def start(self):
        self.log.info("BinderHub starting on port %i", self.port)
        self.tornado_app.listen(self.port)
        tornado.ioloop.IOLoop.current().start()

main = BinderHub.launch_instance

if __name__ == '__main__':
    main()
