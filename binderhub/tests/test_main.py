"""Test main handlers"""

import pytest
from tornado.httputil import url_concat

from .utils import async_requests

@pytest.mark.gen_test
@pytest.mark.parametrize(
    "old_url, new_url", [
        ("/repo/minrk/ligo-binder", "/v2/gh/minrk/ligo-binder/master"),
        ("/repo/minrk/ligo-binder/", "/v2/gh/minrk/ligo-binder/master"),
        (
            "/repo/minrk/ligo-binder/notebooks/index.ipynb",
            "/v2/gh/minrk/ligo-binder/master?urlpath=%2Fnotebooks%2Findex.ipynb",
        ),
    ]
)
def test_legacy_redirect(app, old_url, new_url):
    r = yield async_requests.get(app.url + old_url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers['location'] == new_url
