"""Test main handlers"""

import time
from urllib.parse import quote

import jwt
import pytest
from bs4 import BeautifulSoup

from .utils import async_requests


@pytest.mark.remote
@pytest.mark.helm
async def test_custom_template(app):
    """Check that our custom template config is applied via the helm chart"""
    r = await async_requests.get(app.url)
    assert r.status_code == 200
    assert "test-template" in r.text


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
