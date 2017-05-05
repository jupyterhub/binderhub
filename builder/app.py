from traitlets import Unicode, Integer, Bool
from traitlets.config import Application
import tornado.ioloop
import tornado.web
import os
from .github import GitHubBuildHandler
from .redirect import RedirectHandler
from .main import MainHandler


class BuilderApp(Application):
    config_file = Unicode(
        'builder_config.py',
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

    docker_push_secret = Unicode(
        'docker-push-secret',
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

    hub_redirect_url_template = Unicode(
        None,
        allow_none=True,
        help="""
        Template used to generate the URL to redirect user to after building.

        {image} is replaced with the name of the built image.

        For example, if your configured JupyterHub is at mydomain.org,
        you would set this to 'mydomain.org/hub/tmplogin?image={image}'
        """,
        config=True
    )

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)

        self.tornado_settings = {
            "docker_push_secret": self.docker_push_secret,
            "docker_image_prefix": self.docker_image_prefix,
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "github_auth_token": self.github_auth_token,
            "debug": self.debug,
            'hub_redirect_url_template': self.hub_redirect_url_template
        }

        self.tornado_app = tornado.web.Application([
            (r"/build/github/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)/(\w+)", GitHubBuildHandler),
            (r"/redirect", RedirectHandler),
            (r"/", MainHandler)
        ], **self.tornado_settings)

    @classmethod
    def launch_instance(cls, argv=None):
        instance = cls.instance()
        instance.initialize()
        instance.tornado_app.listen(instance.port)
        tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    BuilderApp.launch_instance()
