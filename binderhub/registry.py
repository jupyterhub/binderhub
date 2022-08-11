"""
Interaction with the Docker Registry
"""
import base64
import json
import os
from urllib.parse import urlparse

import boto3
import kubernetes.client
import kubernetes.config
from tornado import httpclient
from tornado.httputil import url_concat
from traitlets import Dict, Unicode, default, Any
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
            # is gcr.io's token url common? If so, it might be worth defaulting
            # to https://registry.host/v2/token?service=registry.host
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

    async def get_image_manifest(self, image, tag):
        client = httpclient.AsyncHTTPClient()
        url = f"{self.url}/v2/{image}/manifests/{tag}"
        # first, get a token to perform the manifest request
        if self.token_url:
            auth_req = httpclient.HTTPRequest(
                url_concat(
                    self.token_url,
                    {
                        "scope": f"repository:{image}:pull",
                        "service": "container_registry",
                    },
                ),
                auth_username=self.username,
                auth_password=self.password,
            )
            auth_resp = await client.fetch(auth_req)
            response_body = json.loads(auth_resp.body.decode("utf-8", "replace"))

            if "token" in response_body.keys():
                token = response_body["token"]
            elif "access_token" in response_body.keys():
                token = response_body["access_token"]

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

        try:
            resp = await client.fetch(req)
        except httpclient.HTTPError as e:
            if e.code == 404:
                # 404 means it doesn't exist
                return None
            else:
                raise
        else:
            return json.loads(resp.body.decode("utf-8"))


class AWSElasticContainerRegistry(DockerRegistry):
    aws_region = Unicode(
        config=True,
        help="""
        AWS region for ECR service
        """,
    )

    ecr_client = Any()

    @default("ecr_client")
    def _get_ecr_client(self):
        return boto3.client("ecr", region_name=self.aws_region)

    username = "AWS"

    kubernetes.config.load_incluster_config()
    kube_client = kubernetes.client.CoreV1Api()

    def _get_ecr_auth(self):
        return self.ecr_client.get_authorization_token()["authorizationData"][0]

    @default("url")
    def _default_url(self):
        return self._get_ecr_auth()["proxyEndpoint"]

    def _patch_docker_config_secret(self, auth):
        """Patch binder-push-secret"""
        secret_data = {"auths": {self.url: {"auth": auth["authorizationToken"]}}}
        secret_data = base64.b64encode(json.dumps(secret_data).encode("utf8")).decode(
            "utf8"
        )
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
            namespace = f.read()
        self.kube_client.patch_namespaced_secret(
            "binder-push-secret", namespace, {"data": {"config.json": secret_data}}
        )

    @default("password")
    def _get_ecr_pawssord(self):
        """Get ecr password"""
        auth = self._get_ecr_auth()
        self.password_expires = auth["expiresAt"]
        self._patch_docker_config_secret(auth)
        return base64.b64decode(auth['authorizationToken']).decode("utf-8").split(':')[1]

    async def get_image_manifest(self, image, tag):
        try:
            repo_name = image.split("/", 1)[1]
            self.ecr_client.create_repository(repositoryName=repo_name)
            self.log.info("Creating ECR repo {}".format(repo_name))
        except self.ecr_client.exceptions.RepositoryAlreadyExistsException:
            self.log.info("ECR repo {} already exists".format(repo_name))
        # TODO: check for expiration before reseting password
        self.password = self._get_ecr_pawssord()
        return await super().get_image_manifest(repo_name, tag)


class FakeRegistry(DockerRegistry):
    """
    Fake registry that contains no images
    """

    async def get_image_manifest(self, image, tag):
        return None
