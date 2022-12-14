"""Tests for the registry"""
import base64
import json
import os
from random import randint

import pytest
from tornado import httpclient
from tornado.web import Application, HTTPError, RequestHandler

from binderhub.registry import DockerRegistry


def test_registry_defaults(tmpdir):
    registry = DockerRegistry(docker_config_path=str(tmpdir.join("doesntexist.json")))
    assert registry.url == "https://registry-1.docker.io"
    assert registry.auth_config_url == "https://index.docker.io/v1"
    assert (
        registry.token_url == "https://auth.docker.io/token?service=registry.docker.io"
    )
    assert registry.username == ""
    assert registry.password == ""


def test_registry_username_password(tmpdir):
    config_json = tmpdir.join("dockerconfig.json")
    with config_json.open("w") as f:
        json.dump(
            {
                "auths": {
                    "https://index.docker.io/v1": {
                        "auth": base64.encodebytes(b"user:pass").decode("ascii")
                    }
                }
            },
            f,
        )
    registry = DockerRegistry(docker_config_path=str(config_json))
    assert registry.username == "user"
    assert registry.password == "pass"
    assert registry.url == "https://registry-1.docker.io"


def test_registry_gcr_defaults(tmpdir):
    config_json = tmpdir.join("dockerconfig.json")
    with config_json.open("w") as f:
        json.dump(
            {
                "auths": {
                    "https://gcr.io": {
                        "auth": base64.encodebytes(b"_json_key:{...}").decode("ascii")
                    }
                }
            },
            f,
        )
    registry = DockerRegistry(docker_config_path=str(config_json))
    assert registry.url == "https://gcr.io"
    assert registry.auth_config_url == "https://gcr.io"
    assert registry.token_url == "https://gcr.io/v2/token?service=gcr.io"
    assert registry.username == "_json_key"
    assert registry.password == "{...}"


@pytest.mark.parametrize(
    "header,expected",
    [
        (
            'Bearer realm="https://example.org/abc/token",service="example.org",scope=""',
            ("https://example.org/abc/token", "example.org", ""),
        ),
        (
            'BEARER scope="abc",service="example.org",realm="https://example.org/abc/token"',
            ("https://example.org/abc/token", "example.org", "abc"),
        ),
    ],
)
def test_parse_www_authenticate_header(header, expected):
    registry = DockerRegistry()
    assert expected == registry._parse_www_authenticate_header(header)


@pytest.mark.parametrize(
    "header,expected",
    [
        (
            'basic realm="https://example.org/abc/token"',
            "Only WWW-Authenticate Bearer type supported",
        ),
        (
            'bearer realm="https://example.org/abc/token"',
            "Expected WWW-Authenticate to include realm service scope",
        ),
    ],
)
def test_parse_www_authenticate_header_invalid(header, expected):
    registry = DockerRegistry()
    with pytest.raises(ValueError) as excinfo:
        registry._parse_www_authenticate_header(header)
    assert excinfo.value.args[0].startswith(expected)


# Mock the registry API calls made by get_image_manifest


class MockTokenHandler(RequestHandler):
    """Mock handler for the registry token handler"""

    def initialize(self, test_handle, service=None, scope=None):
        self.test_handle = test_handle
        self.service = service
        self.scope = scope

    def get(self):
        scope = self.get_argument("scope")
        if self.scope:
            assert scope == self.scope
        service = self.get_argument("service")
        if self.service:
            assert service == self.service
        auth_header = self.request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            raise HTTPError(401, "No basic auth")
        b64_auth = auth_header[6:].encode("ascii")
        decoded = base64.decodebytes(b64_auth).decode("utf8")
        username, password = decoded.split(":", 2)
        if username != self.test_handle["username"]:
            raise HTTPError(403, "Bad username %r" % username)
        if password != self.test_handle["password"]:
            raise HTTPError(403, "Bad password %r" % password)
        self.test_handle["token"] = token = (
            base64.encodebytes(os.urandom(5)).decode("ascii").rstrip()
        )
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({"token": token}))


class MockManifestHandler(RequestHandler):
    """Mock handler for the registry token handler"""

    def initialize(self, test_handle):
        self.test_handle = test_handle

    def get(self, image, tag):
        auth_header = self.request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPError(401, "No bearer auth")
        token = auth_header[7:]
        if token != self.test_handle["token"]:
            raise HTTPError(403, "{} != {}".format(token, self.test_handle["token"]))
        self.set_header("Content-Type", "application/json")
        # get_image_manifest never looks at the contents here
        self.write(json.dumps({"image": image, "tag": tag}))

    def write_error(self, status_code, **kwargs):
        err_cls, err, traceback = kwargs["exc_info"]
        if status_code == 401:
            r = self.request
            self.set_header(
                "WWW-Authenticate",
                f'Bearer realm="{r.protocol}://{r.host}/token",service="service=1",scope="scope-2"',
            )
            super().write_error(status_code, **kwargs)


async def test_get_token():
    username = "user"
    password = "pass"
    test_handle = {"username": username, "password": password}
    app = Application(
        [
            (r"/token", MockTokenHandler, {"test_handle": test_handle}),
        ]
    )
    ip = "127.0.0.1"
    port = randint(10000, 65535)
    app.listen(port, ip)

    registry = DockerRegistry(
        url="https://example.org", username=username, password=password
    )

    assert registry.url == "https://example.org"
    assert registry.auth_config_url == "https://example.org"
    # token_url should be unset, since it should be determined by the caller from a
    # WWW-Authenticate header
    assert registry.token_url == ""
    assert registry.username == username
    assert registry.password == password
    token = await registry._get_token(
        httpclient.AsyncHTTPClient(),
        f"http://{ip}:{port}/token",
        "service.1",
        "scope.2",
    )
    assert token == test_handle["token"]


@pytest.mark.parametrize("token_url_known", [True, False])
async def test_get_image_manifest(tmpdir, token_url_known):
    username = "asdf"
    password = "asdf;ouyag"
    test_handle = {"username": username, "password": password}
    app = Application(
        [
            (r"/token", MockTokenHandler, {"test_handle": test_handle}),
            (
                r"/v2/([^/]+)/manifests/([^/]+)",
                MockManifestHandler,
                {"test_handle": test_handle},
            ),
        ]
    )
    ip = "127.0.0.1"
    port = randint(10000, 65535)
    url = f"http://{ip}:{port}"
    app.listen(port, ip)
    config_json = tmpdir.join("dockerconfig.json")
    with config_json.open("w") as f:
        json.dump(
            {
                "auths": {
                    url: {
                        "auth": base64.encodebytes(
                            f"{username}:{password}".encode()
                        ).decode("ascii")
                    }
                }
            },
            f,
        )
    if token_url_known:
        token_url = url + "/token"
    else:
        token_url = ""
    registry = DockerRegistry(
        docker_config_path=str(config_json), token_url=token_url, url=url
    )
    assert registry.url == url
    assert registry.auth_config_url == url
    assert registry.token_url == token_url
    assert registry.username == username
    assert registry.password == password
    manifest = await registry.get_image_manifest("myimage", "abc123")
    assert manifest == {"image": "myimage", "tag": "abc123"}
