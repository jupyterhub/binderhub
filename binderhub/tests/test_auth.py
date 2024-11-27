"""Test authentication"""

import ipaddress
import json
from unittest import mock
from urllib.parse import urlparse

import pytest

from .conftest import skip_remote
from .utils import async_requests


@pytest.fixture
def use_session():
    # setup
    async_requests.set_session()
    yield "run the test function"
    # teardown
    async_requests.delete_session()


@pytest.mark.parametrize(
    "app,path,authenticated",
    [
        ("app_with_auth_config", "/", True),  # main page
        (
            True,
            "/v2/gh/binderhub-ci-repos/requirements/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd",
            True,
        ),
        ("app_with_auth_config", "/metrics", False),
    ],
    indirect=[
        "app"
    ],  # send param "app_with_auth_config" to app fixture, so that it loads authentication configuration
)
@pytest.mark.auth
async def test_auth(app, path, authenticated, use_session):
    url = f"{app.url}{path}"
    r = await async_requests.get(url)
    assert r.status_code == 200, f"{r.status_code} {url}"
    if not authenticated:
        # not authenticated, we should get the page and be done
        assert r.url == url
        return
    assert "/hub/login" in urlparse(r.url).path

    # acquire a _xsrf cookie to pass in the post request we are about to make
    login_url = f"{app.hub_url}/hub/login"
    r2 = await async_requests.get(login_url)
    assert r2.status_code == 200, f"{r2.status_code} {r2.url}"
    _xsrf_cookie = r2.cookies.get("_xsrf", path="/hub/")
    assert _xsrf_cookie

    # submit login form
    r3 = await async_requests.post(
        r.url, data={"username": "dummy", "password": "dummy", "_xsrf": _xsrf_cookie}
    )
    assert r3.status_code == 200, f"{r3.status_code} {r3.url}"
    # verify that we landed at the destination after auth
    assert r3.url == url


@skip_remote
@pytest.mark.parametrize(
    "path, banned, prefixlen, status",
    [
        ("/", True, 32, 403),
        ("/", False, 32, 200),
        (
            "/v2/gh/binderhub-ci-repos/requirements/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd",
            True,
            24,
            403,
        ),
        (
            "/build/gh/binderhub-ci-repos/requirements/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd",
            True,
            24,
            200,  # due to event-stream, status is always 200 even when rejected
        ),
        # ban_networks shouldn't affect health endpoint
        ("/health", True, 32, (200, 503)),
        ("/health", False, 24, (200, 503)),
    ],
)
async def test_ban_networks(request, app, use_session, path, banned, prefixlen, status):
    url = f"{app.url}{path}"
    ban_networks = {
        "255.255.255.255/32": "255.x",
        "1.0.0.0/8": "1.x",
    }
    local_net = [
        str(ipaddress.ip_network("127.0.0.1").supernet(new_prefix=prefixlen)),
        str(ipaddress.ip_network("::1").supernet(new_prefix=prefixlen)),
    ]

    if banned:
        for net in local_net:
            ban_networks[net] = "local"

    # pass through trait validators on app
    app.ban_networks = ban_networks

    def reset():
        app.ban_networks = {}

    request.addfinalizer(reset)
    with mock.patch.dict(
        app.tornado_app.settings,
        {
            "ban_networks": app.ban_networks,
        },
    ):
        r = await async_requests.get(url)
    if isinstance(status, int):
        assert r.status_code == status
    else:
        # allow container of statuses
        assert r.status_code in status

    ban_message = "Requests from local are not allowed"
    if status == 403:
        # check error message on 403
        assert ban_message in r.text

    if banned and path.startswith("/build"):
        # /build/ is event-stream, so allow connecting with status 200
        # and a failure message
        assert r.headers["content-type"] == "text/event-stream"
        assert ban_message in r.text
        events = []
        for line in r.text.splitlines():
            if line.startswith("data:"):
                _, json_event = line.split(":", 1)
                events.append(json.loads(json_event))
        event = events[-1]
        assert event["phase"] == "failed"
        assert event["status_code"] == 403
        assert ban_message in event["message"]
