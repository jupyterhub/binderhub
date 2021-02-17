"""Tests for the registry"""
import base64
import json
import os

import pytest

from tornado.web import Application, RequestHandler, HTTPError

from binderhub.registry import DockerRegistry


def test_registry_defaults(tmpdir):
    registry = DockerRegistry(docker_config_path=str(tmpdir.join("doesntexist.json")))
    assert registry.url == "https://registry.hub.docker.com"
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
    assert registry.url == "https://registry.hub.docker.com"


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

# Mock the registry API calls made by get_image_manifest

class MockTokenHandler(RequestHandler):
    """Mock handler for the registry token handler"""

    def initialize(self, test_handle):
        self.test_handle = test_handle

    def get(self):
        scope = self.get_argument("scope")
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
        self.test_handle["token"] = token = base64.encodebytes(os.urandom(5)).decode(
            "ascii"
        ).rstrip()
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
            raise HTTPError(403, "%s != %s" % (token, self.test_handle["token"]))
        self.set_header("Content-Type", "application/json")
        # get_image_manifest never looks at the contents here
        self.write(json.dumps({"image": image, "tag": tag}))


async def test_get_image_manifest(tmpdir, request):
    username = "asdf"
    password = "asdf;ouyag"
    test_handle = {"username": username, "password": password}
    app = Application(
        [
            (r"/token", MockTokenHandler, {"test_handle": test_handle}),
            (
                r"/v2/([a-zA-Z0-9]+(?:/[a-zA-Z0-9]+)*)/manifests/([a-zA-Z0-9]+)",
                MockManifestHandler,
                {"test_handle": test_handle},
            ),
        ]
    )
    ip = "127.0.0.1"
    port = 10504
    url = f"http://{ip}:{port}"
    app.listen(port, ip)
    config_json = tmpdir.join("dockerconfig.json")
    with config_json.open("w") as f:
        json.dump(
            {
                "auths": {
                    url: {
                        "auth": base64.encodebytes(
                            f"{username}:{password}".encode("utf8")
                        ).decode("ascii")
                    }
                }
            },
            f,
        )
    registry = DockerRegistry(
        docker_config_path=str(config_json), token_url=url + "/token", url=url
    )
    assert registry.url == url
    assert registry.auth_config_url == url
    assert registry.token_url == url + "/token"
    assert registry.username == username
    assert registry.password == password

    names = ["myimage:abc123", "localhost/myimage:abc1234", "localhost:8080/myimage:abc3",
              "192.168.1.1:8080/myimage:abc321", "192.168.1.1:8080/some/repo/myimage:abc3210"]
    for name in names:
        manifest = await registry.get_image_manifest(name)
        assert manifest == {"image": name.split("/", 1)[-1].rsplit(":", 1)[0], "tag": name.rsplit(":", 1)[-1]}
