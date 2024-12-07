"""Test main handlers"""

import time
from urllib.parse import quote

import jwt
import pytest
from bs4 import BeautifulSoup

from binderhub import __version__ as binder_version

from .utils import async_requests


@pytest.mark.parametrize(
    "old_url, new_url",
    [
        (
            "/repo/binderhub-ci-repos/requirements",
            "/v2/gh/binderhub-ci-repos/requirements/master",
        ),
        (
            "/repo/binderhub-ci-repos/requirements/",
            "/v2/gh/binderhub-ci-repos/requirements/master",
        ),
        (
            "/repo/binderhub-ci-repos/requirements/notebooks/index.ipynb",
            "/v2/gh/binderhub-ci-repos/requirements/master?urlpath=%2Fnotebooks%2Findex.ipynb",
        ),
    ],
)
async def test_legacy_redirect(app, old_url, new_url):
    r = await async_requests.get(app.url + old_url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == new_url


@pytest.mark.remote
@pytest.mark.helm
async def test_custom_template(app):
    """Check that our custom template config is applied via the helm chart"""
    r = await async_requests.get(app.url)
    assert r.status_code == 200
    assert "test-template" in r.text


@pytest.mark.remote
async def test_versions_handler(app):
    # Check that the about page loads
    r = await async_requests.get(app.url + "/versions")
    assert r.status_code == 200

    data = r.json()
    # builder_info is different for KubernetesExecutor and LocalRepo2dockerBuild
    try:
        import repo2docker

        allowed_builder_info = [{"repo2docker-version": repo2docker.__version__}]
    except ImportError:
        allowed_builder_info = []
    allowed_builder_info.append({"build_image": app.build_image})

    assert data["builder_info"] in allowed_builder_info
    assert data["binderhub"].split("+")[0] == binder_version.split("+")[0]


@pytest.mark.parametrize(
    "origin,host,expected_origin",
    [
        ("https://my.host", "my.host", "my.host"),
        ("https://my.origin", "my.host", "my.origin"),
        (None, "my.host", "my.host"),
    ],
)
async def test_build_token_origin(app, origin, host, expected_origin):
    provider_spec = "git/{}/HEAD".format(
        quote(
            "https://github.com/binderhub-ci-repos/cached-minimal-dockerfile",
            safe="",
        )
    )
    uri = f"/v2/{provider_spec}"
    headers = {}
    if origin:
        headers["Origin"] = origin
    if host:
        headers["Host"] = host

    r = await async_requests.get(app.url + uri, headers=headers)

    soup = BeautifulSoup(r.text, "html5lib")
    assert soup.find(id="build-token")
    token_element = soup.find(id="build-token")
    assert token_element
    assert "data-token" in token_element.attrs
    build_token = token_element["data-token"]
    payload = jwt.decode(
        build_token,
        audience=provider_spec,
        options=dict(verify_signature=False),
    )
    assert payload["aud"] == provider_spec
    assert payload["origin"] == expected_origin
    assert time.time() < payload["exp"] < time.time() + 7200
