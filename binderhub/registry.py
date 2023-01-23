"""
Interaction with the Docker Registry
"""
import base64
import json
import os
import re
from urllib.parse import urlparse

from tornado import httpclient
from tornado.httputil import url_concat
from traitlets import Dict, Unicode, default
from traitlets.config import LoggingConfigurable

DEFAULT_DOCKER_REGISTRY_URL = "https://registry-1.docker.io"
DEFAULT_DOCKER_AUTH_URL = "https://index.docker.io/v1"


class DockerRegistry(LoggingConfigurable):
    url = Unicode(
        DEFAULT_DOCKER_REGISTRY_URL,
        help="""
        Docker registry url.

        Default: retrieved from docker config.json

        Only set this if:
        - not using docker hub, and
        - more than one registry is configured in docker config.json
        """,
        config=True,
    )

    @default("url")
    def _default_url(self):
        cfg = self._docker_config
        auths = cfg.get("auths", {})
        if not auths:
            return DEFAULT_DOCKER_REGISTRY_URL

        # default to first entry in docker config.json auths
        auth_config_url = next(iter(auths.keys()))
        if "://" not in auth_config_url:
            # auth key can be just a hostname,
            # which assumes https
            auth_config_url = "https://" + auth_config_url

        if auth_config_url.rstrip("/") == DEFAULT_DOCKER_AUTH_URL:
            # default docker config key is the v1 registry,
            # but we will talk to the v2 api
            return DEFAULT_DOCKER_REGISTRY_URL

        return auth_config_url

    auth_config_url = Unicode(
        DEFAULT_DOCKER_AUTH_URL,
        help="""
        Docker auth configuration url.

        Used to lookup auth data in docker config.json.

        Not used if url, username, and password are set.

        Default: same as url

        Only set if:
        - Not using Docker Hub
        - registry url is not the auth key in docker config.json
        """,
        config=True,
    )

    @default("auth_config_url")
    def _auth_config_url_default(self):
        url = urlparse(self.url)
        cfg = self._docker_config
        auths = cfg.get("auths", {})
        # check for our url in docker config.json
        # there can be some variation, so try a few things.

        # in ~all cases, the registry url will appear in config.json
        if self.url in auths:
            # this will
            return self.url
        # ...but the config key is allowed to lack https://, so check just hostname
        if url.hostname in auths:
            return url.hostname
        # default docker special-case, where auth and registry urls are different
        if ("." + url.hostname).endswith((".docker.io", ".docker.com")):
            return DEFAULT_DOCKER_AUTH_URL

        # url not found, leave the most likely default
        return self.url

    docker_config_path = Unicode(
        os.path.join(
            os.environ.get("DOCKER_CONFIG", os.path.expanduser("~/.docker")),
            "config.json",
        ),
        help=""""
        path to docker config.json

        Default: ~/.docker/config.json (respects $DOCKER_CONFIG if set)
        """,
        config=True,
    )
    _docker_config = Dict()

    @default("_docker_config")
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
        url = urlparse(self.url)
        if ("." + url.hostname).endswith(".gcr.io"):
            return "https://{0}/v2/token?service={0}".format(url.hostname)
        elif self.url.endswith(".docker.io"):
            return "https://auth.docker.io/token?service=registry.docker.io"
        else:
            # If necessary we'll look for the WWW-Authenticate header
            return ""

    username = Unicode(
        help="""
        Username for authenticating with docker registry

        Default: retrieved from docker config.json.
        """,
        config=True,
    )

    @default("username")
    def _default_username(self):
        b64_auth = None
        if self.auth_config_url in self._docker_config.get("auths", {}):
            b64_auth = self._docker_config["auths"][self.auth_config_url].get("auth")

        if not b64_auth:
            self.log.warning(
                "No username for docker registry at %s", self.auth_config_url
            )
            return ""

        return (
            base64.b64decode(b64_auth.encode("utf-8")).decode("utf-8").split(":", 1)[0]
        )

    password = Unicode(
        help="""
        Password for authenticating with docker registry

        Default: retrieved from docker config.json.
        """,
        config=True,
    )

    @default("password")
    def _default_password(self):
        b64_auth = None
        if self.auth_config_url in self._docker_config.get("auths", {}):
            b64_auth = self._docker_config["auths"][self.auth_config_url].get("auth")

        if not b64_auth:
            self.log.warning(
                "No password for docker registry at %s", self.auth_config_url
            )
            return ""

        return (
            base64.b64decode(b64_auth.encode("utf-8")).decode("utf-8").split(":", 1)[1]
        )

    def _parse_www_authenticate_header(self, header):
        # Header takes the form
        # WWW-Authenticate: Bearer realm="https://uk-london-1.ocir.io/12345678/docker/token",service="uk-london-1.ocir.io",scope=""
        self.log.debug(f"Parsing WWW-Authenticate {header}")

        if not header.lower().startswith("bearer "):
            raise ValueError(f"Only WWW-Authenticate Bearer type supported: {header}")
        try:
            realm = re.search(r'realm="([^"]+)"', header).group(1)
            # Should service and scope parameters be optional instead of just empty?
            service = re.search(r'service="([^"]*)"', header).group(1)
            scope = re.search(r'scope="([^"]*)"', header).group(1)
            return realm, service, scope
        except AttributeError:
            raise ValueError(
                f"Expected WWW-Authenticate to include realm service scope: {header}"
            ) from None

    async def _get_token(self, client, token_url, service, scope):
        # specify required query parameters
        query_params = {
            "scope": scope,
        }

        # add optional query parameters
        if service is not None:
            query_params["service"] = service

        auth_req = httpclient.HTTPRequest(
            url_concat(
                token_url,
                query_params,
            ),
            auth_username=self.username,
            auth_password=self.password,
        )
        self.log.debug(
            f"Getting registry token from {token_url} service={service} scope={scope}"
        )
        auth_resp = await client.fetch(auth_req)
        response_body = json.loads(auth_resp.body.decode("utf-8", "replace"))

        if "token" in response_body.keys():
            token = response_body["token"]
        elif "access_token" in response_body.keys():
            token = response_body["access_token"]
        else:
            raise ValueError(f"No token in response from registry: {response_body}")
        return token

    async def _get_image_manifest_from_www_authenticate(
        self, client, www_auth_header, url
    ):
        realm, service, scope = self._parse_www_authenticate_header(www_auth_header)
        token = await self._get_token(client, realm, service, scope)
        req = httpclient.HTTPRequest(
            url,
            headers={"Authorization": f"Bearer {token}"},
        )
        self.log.debug(f"Getting image manifest from {url}")
        try:
            resp = await client.fetch(req)
        except httpclient.HTTPError as e:
            if e.code == 404:
                return None
            else:
                raise
        return json.loads(resp.body.decode("utf-8"))

    async def get_image_manifest(self, image, tag):
        """
        Get the manifest for an image.

        image: The image name without the registry and tag
        tag: The image tag
        """
        client = httpclient.AsyncHTTPClient()
        url = f"{self.url}/v2/{image}/manifests/{tag}"
        token = None
        # first, get a token to perform the manifest request
        if self.token_url:
            token = await self._get_token(
                client,
                self.token_url,
                None,  # service may be pre-set in self.token_url as per Helm chart docs for specific CRs
                f"repository:{image}:pull",
            )
            req = httpclient.HTTPRequest(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )
        else:
            # Use basic HTTP auth (htpasswd)
            req = httpclient.HTTPRequest(
                url,
                auth_username=self.username,
                auth_password=self.password,
            )

        self.log.debug(f"Getting image manifest from {url}")
        try:
            resp = await client.fetch(req)
        except httpclient.HTTPError as e:
            if e.code == 404:
                # 404 means it doesn't exist
                return None
            elif (
                e.code == 401 and not token and "www-authenticate" in e.response.headers
            ):
                # Unauthorised. If we don't have a token, try and get one using
                # information from the WWW-Authenticate header
                # https://stackoverflow.com/questions/56193110/how-can-i-use-docker-registry-http-api-v2-to-obtain-a-list-of-all-repositories-i/68654659#68654659
                www_auth_header = e.response.headers["www-authenticate"]
                return await self._get_image_manifest_from_www_authenticate(
                    client, www_auth_header, url
                )
            else:
                raise
        return json.loads(resp.body.decode("utf-8"))


class FakeRegistry(DockerRegistry):
    """
    Fake registry that contains no images
    """

    async def get_image_manifest(self, image, tag):
        return None
