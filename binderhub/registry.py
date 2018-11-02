"""
Interaction with the Docker Registry
"""
import base64
import json
import os
from urllib.parse import urlparse

from tornado import gen, httpclient
from tornado.httputil import url_concat
from traitlets.config import LoggingConfigurable
from traitlets import Dict, Unicode, default


class DockerRegistry(LoggingConfigurable):
    registry_host = Unicode(
        "https://registry.hub.docker.com",
        help="""
        Docker registry host.

        Default: same as auth_host,
        no need to set this if using docker hub or registry host
        is the same as the auth host.
        """,
        config=True,
    )
    @default('registry_host')
    def _default_registry_host(self):
        auth_host = self.auth_host
        url = urlparse(auth_host)
        # special-case docker, where these are different
        if ('.' + url.hostname).endswith(('.docker.io', '.docker.com')):
            return 'https://registry.hub.docker.com'
        # default to the same as the auth host, if not defined
        return "{}://{}".format(url.scheme, url.netloc)

    auth_host = Unicode(
        help="""
        Docker authentication host.

        Default: first entry in docker config.json if found,
        otherwise the default docker auth host.

        No need to set this if docker config contains
        the right auth host.
        """,
        config=True,
    )

    @default('auth_host')
    def _auth_host_default(self):
        config_path = os.path.expanduser('~/.docker/config.json')
        default = "https://index.docker.io/v1"
        cfg = self._docker_config
        auths = cfg.get("auths", {})
        # by default: return the first host in our docker config file
        return next(iter(auths.keys()), default)

    docker_config_path = Unicode(
        os.path.join(
            os.environ.get('DOCKER_CONFIG', os.path.expanduser('~/.docker')),
            'config.json',
        ),
        help=""""
        path to docker config.json

        Default: ~/.docker/config.json
        """,
        config=True,
    )
    _docker_config = Dict()
    @default('_docker_config')
    def _load_docker_config(self):
        if not os.path.exists(self.docker_config_path):
            self.log.warning("No docker config at %s", self.docker_config_path)
            return {}
        self.log.info("Loading docker config %s", self.docker_config_path)
        with open(self.docker_config_path) as f:
            return json.load(f)

    token_url = Unicode(
        help="""
        URL to request docker registry authentication token.

        No need to set if using Docker Hub or gcr.io
        """,
        config=True,
    )
    @default("token_url")
    def _default_token_url(self):
        if self.registry_host == "https://gcr.io":
            return "https://gcr.io/v2/token?service=gcr.io"
        elif self.registry_host.endswith(".docker.com"):
            return "https://auth.docker.io/token?service=registry.docker.io"
        else:
            return ""

    username = Unicode(
        help="""
        Username for authenticating with docker registry

        Default: retrieved from docker config.
        """,
        config=True,
    )
    @default('username')
    def _default_username(self):
        b64_auth = None
        if self.auth_host in self._docker_config.get('auths', {}):
            b64_auth = self._docker_config['auths'][self.auth_host].get('auth')

        if not b64_auth:
            self.log.warning("No username for docker registry at %s", self.auth_host)
            return ''

        return base64.b64decode(
            b64_auth.encode('utf-8')
        ).decode('utf-8').split(':', 1)[0]

    password = Unicode(
        help="""
        Password for authenticating with docker registry

        Default: retrieved from docker config.
        """,
        config=True,
    )
    @default('password')
    def _default_password(self):
        b64_auth = None
        if self.auth_host in self._docker_config.get('auths', {}):
            b64_auth = self._docker_config['auths'][self.auth_host].get('auth')

        if not b64_auth:
            self.log.warning("No password for docker registry at %s", self.auth_host)
            return ''

        return base64.b64decode(
            b64_auth.encode('utf-8')
        ).decode('utf-8').split(':', 1)[1]

    @gen.coroutine
    def get_image_manifest(self, image, tag):
        client = httpclient.AsyncHTTPClient()
        # first, get a token to perform the manifest request
        auth_req = httpclient.HTTPRequest(
            url_concat(self.token_url,
                       {'scope': 'repository:{}:pull'.format(image)}),
            auth_username=self.username,
            auth_password=self.password,
        )
        auth_resp = yield client.fetch(auth_req)
        token = json.loads(auth_resp.body.decode('utf-8', 'replace'))['token']

        req = httpclient.HTTPRequest(
            '{}/v2/{}/manifests/{}'.format(self.registry_host, image, tag),
            headers={'Authorization': 'Bearer {}'.format(token)},
        )
        try:
            resp = yield client.fetch(req)
        except httpclient.HTTPError as e:
            if e.code == 404:
                # 404 means it doesn't exist
                return None
            else:
                raise
        else:
            return json.loads(resp.body.decode('utf-8'))
