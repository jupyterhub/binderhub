"""Test main handlers"""

import json
import time
from urllib.parse import quote

import jwt
import pytest
from bs4 import BeautifulSoup

from .utils import async_requests


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
    script_tag = soup.select_one("head > script")
    page_config_str = (
        script_tag.string.strip().removeprefix("window.pageConfig = ").removesuffix(";")
    )
    print(page_config_str)
    page_config = json.loads(page_config_str)
    print(page_config)

    assert "buildToken" in page_config

    build_token = page_config["buildToken"]
    payload = jwt.decode(
        build_token,
        audience=provider_spec,
        options=dict(verify_signature=False),
    )
    assert payload["aud"] == provider_spec
    assert payload["origin"] == expected_origin
    assert time.time() < payload["exp"] < time.time() + 7200
