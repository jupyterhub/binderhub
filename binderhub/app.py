"""
The binderhub application
"""
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from urllib.parse import urlparse

import kubernetes.client
import kubernetes.config
from jinja2 import Environment, FileSystemLoader, PrefixLoader, ChoiceLoader
from tornado.httpclient import AsyncHTTPClient
import tornado.ioloop
import tornado.options
import tornado.log
import tornado.web
from traitlets import Unicode, Integer, Bool, Dict, validate, TraitError, default
from traitlets.config import Application

from .base import Custom404
from .builder import BuildHandler
from .launcher import Launcher
from .registry import DockerRegistry
from .main import MainHandler, ParameterizedMainHandler, LegacyRedirectHandler
from .repoproviders import GitHubRepoProvider, GitRepoProvider, GitLabRepoProvider, GistRepoProvider
from .metrics import MetricsHandler
from .utils import ByteSpecification, url_path_join


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
            {'BinderHub': {'debug': True}},
            "Enable debug HTTP serving & debug logging"
        )
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

    google_analytics_domain = Unicode(
        'auto',
        help="""
        The Google Analytics domain to use on the main page.

        By default this is set to 'auto', which sets it up for current domain and all
        subdomains. This can be set to a more restrictive domain here for better privacy
        """,
        config=True
    )

    base_url = Unicode(
        '/',
        help="The base URL of the entire application",
        config=True)

    @validate('base_url')
    def _valid_base_url(self, proposal):
        if not proposal.value.startswith('/'):
            proposal.value = '/' + proposal.value
        if not proposal.value.endswith('/'):
            proposal.value = proposal.value + '/'
        return proposal.value

    port = Integer(
        8585,
        help="""
        Port for the builder to listen on.
        """,
        config=True
    )

    appendix = Unicode(
        help="""
        Appendix to pass to repo2docker

        A multi-line string of Docker directives to run.
        Since the build context cannot be affected,
        ADD will typically not be useful.

        This should be a Python string template.
        It will be formatted with at least the following names available:

        - binder_url: the shareable URL for the current image
          (e.g. for sharing links to the current Binder)
        - repo_url: the repository URL used to build the image
        """,
        config=True,
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

    per_repo_quota = Integer(
        0,
        help="""
        Maximum number of concurrent users running from a given repo.

        Limits the amount of Binder that can be consumed by a single repo.

        0 (default) means no quotas.
        """,
        config=True,
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

    docker_registry_host = Unicode(
        "",
        help="""
        Docker registry host.
        """,
        config=True
    )

    docker_auth_host = Unicode(
        help="""
        Docker authentication host.
        """,
        config=True
    )

    @default('docker_auth_host')
    def _docker_auth_host_default(self):
        return self.docker_registry_host

    docker_token_url = Unicode(
        "",
        help="""
        Url to request docker registry authentication token.
        """,
        config=True
    )

    build_memory_limit = ByteSpecification(
        0,
        help="""
        Max amount of memory allocated for each image build process.

        0 sets no limit.

        This is used as both the memory limit & request for the pod
        that is spawned to do the building, even though the pod itself
        will not be using that much memory since the docker building is
        happening outside the pod. However, it makes kubernetes aware of
        the resources being used, and lets it schedule more intelligently.
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

    build_docker_host = Unicode(
        "/var/run/docker.sock",
        config=True,
        help="""
        The docker URL repo2docker should use to build the images.

        Currently, only paths are supported, and they are expected to be available on
        all the hosts.
        """
    )
    @validate('build_docker_host')
    def docker_build_host_validate(self, proposal):
        parts = urlparse(proposal.value)
        if parts.scheme != 'unix' or parts.netloc != '':
            raise TraitError("Only unix domain sockets on same node are supported for build_docker_host")
        return proposal.value

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
        'jupyter/repo2docker:687788f',
        help="""
        The builder image to be used for doing builds
        """,
        config=True
    )

    build_node_selector = Dict(
        {},
        config=True,
        help="""
        Select the node where build pod runs on.
        """
    )

    repo_providers = Dict(
        {
            'gh': GitHubRepoProvider,
            'gist': GistRepoProvider,
            'git': GitRepoProvider,
            'gl': GitLabRepoProvider,
        },
        config=True,
        help="""
        List of Repo Providers to register and try
        """
    )
    concurrent_build_limit = Integer(
        32,
        config=True,
        help="""The number of concurrent builds to allow."""
    )

    # FIXME: Come up with a better name for it?
    builder_required = Bool(
        True,
        config=True,
        help="""
        If binderhub should try to continue to run without a working build infrastructure.

        Build infrastructure is kubernetes cluster + docker. This is useful for pure HTML/CSS/JS local development.
        """
    )

    tornado_settings = Dict(
        config=True,
        help="""
        additional settings to pass through to tornado.

        can include things like additional headers, etc.
        """
    )

    template_variables = Dict(
        config=True,
        help="Extra variables to supply to jinja templates when rendering.",
    )

    template_path = Unicode(
        help="Path to search for custom jinja templates, before using the default templates.",
        config=True,
    )

    @default('template_path')
    def _template_path_default(self):
        return os.path.join(os.path.dirname(__file__), 'templates')

    @staticmethod
    def add_url_prefix(prefix, handlers):
        """add a url prefix to handlers"""
        for i, tup in enumerate(handlers):
            lis = list(tup)
            lis[0] = url_path_join(prefix, tup[0])
            handlers[i] = tuple(lis)
        return handlers

    def init_pycurl(self):
        try:
            AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        except ImportError as e:
            self.log.debug("Could not load pycurl: %s\npycurl is recommended if you have a large number of users.", e)
        # set max verbosity of curl_httpclient at INFO
        # because debug-logging from curl_httpclient
        # includes every full request and response
        if self.log_level < logging.INFO:
            curl_log = logging.getLogger('tornado.curl_httpclient')
            curl_log.setLevel(logging.INFO)

    def initialize(self, *args, **kwargs):
        """Load configuration settings."""
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)
        # hook up tornado logging
        if self.debug:
            self.log_level = logging.DEBUG
        tornado.options.options.logging = logging.getLevelName(self.log_level)
        tornado.log.enable_pretty_logging()
        self.log = tornado.log.app_log

        self.init_pycurl()

        # initialize kubernetes config
        if self.builder_required:
            try:
                kubernetes.config.load_incluster_config()
            except kubernetes.config.ConfigException:
                kubernetes.config.load_kube_config()
            self.tornado_settings["kubernetes_client"] = kubernetes.client.CoreV1Api()


        # times 2 for log + build threads
        self.build_pool = ThreadPoolExecutor(self.concurrent_build_limit * 2)

        jinja_options = dict(autoescape=True, )
        template_paths = [self.template_path]
        base_template_path = self._template_path_default()
        if base_template_path not in template_paths:
            # add base templates to the end, so they are looked up at last after custom templates
            template_paths.append(base_template_path)
        loader = ChoiceLoader([
            # first load base templates with prefix
            PrefixLoader({'templates': FileSystemLoader([base_template_path])}, '/'),
            # load all templates
            FileSystemLoader(template_paths)
        ])
        jinja_env = Environment(loader=loader, **jinja_options)
        if self.use_registry and self.builder_required:
            registry = DockerRegistry(self.docker_auth_host,
                                      self.docker_token_url,
                                      self.docker_registry_host)
        else:
            registry = None

        self.launcher = Launcher(
            parent=self,
            hub_url=self.hub_url,
            hub_api_token=self.hub_api_token,
        )

        self.tornado_settings.update({
            "docker_push_secret": self.docker_push_secret,
            "docker_image_prefix": self.docker_image_prefix,
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "github_auth_token": self.github_auth_token,
            "debug": self.debug,
            'hub_url': self.hub_url,
            'hub_api_token': self.hub_api_token,
            'launcher': self.launcher,
            'appendix': self.appendix,
            "build_namespace": self.build_namespace,
            "builder_image_spec": self.builder_image_spec,
            'build_node_selector': self.build_node_selector,
            'build_pool': self.build_pool,
            'per_repo_quota': self.per_repo_quota,
            'repo_providers': self.repo_providers,
            'use_registry': self.use_registry,
            'registry': registry,
            'traitlets_config': self.config,
            'google_analytics_code': self.google_analytics_code,
            'google_analytics_domain': self.google_analytics_domain,
            'jinja2_env': jinja_env,
            'build_memory_limit': self.build_memory_limit,
            'build_docker_host': self.build_docker_host,
            'base_url': self.base_url,
            'static_url_prefix': url_path_join(self.base_url, 'static/'),
            'template_variables': self.template_variables,
        })

        handlers = [
            (r'/metrics', MetricsHandler),
            (r"/build/([^/]+)/(.+)", BuildHandler),
            (r"/v2/([^/]+)/(.+)", ParameterizedMainHandler),
            (r"/repo/([^/]+)/([^/]+)(/.*)?", LegacyRedirectHandler),
            # for backward-compatible mybinder.org badge URLs
            # /assets/images/badge.svg
            (r'/assets/(images/badge\.svg)',
                tornado.web.StaticFileHandler,
                {'path': self.tornado_settings['static_path']}),
            # /badge.svg
            (r'/(badge\.svg)',
                tornado.web.StaticFileHandler,
                {'path': os.path.join(self.tornado_settings['static_path'], 'images')}),
            # /favicon_XXX.ico
            (r'/(favicon\_fail\.ico)',
                tornado.web.StaticFileHandler,
                {'path': os.path.join(self.tornado_settings['static_path'], 'images')}),
            (r'/(favicon\_success\.ico)',
                tornado.web.StaticFileHandler,
                {'path': os.path.join(self.tornado_settings['static_path'], 'images')}),
            (r'/(favicon\_building\.ico)',
                tornado.web.StaticFileHandler,
                {'path': os.path.join(self.tornado_settings['static_path'], 'images')}),
            (r'/', MainHandler),
            (r'.*', Custom404),
        ]
        handlers = self.add_url_prefix(self.base_url, handlers)
        self.tornado_app = tornado.web.Application(handlers, **self.tornado_settings)

    def stop(self):
        self.http_server.stop()
        self.build_pool.shutdown()

    def start(self, run_loop=True):
        self.log.info("BinderHub starting on port %i", self.port)
        self.http_server = self.tornado_app.listen(self.port)
        if run_loop:
            tornado.ioloop.IOLoop.current().start()


main = BinderHub.launch_instance

if __name__ == '__main__':
    main()
