"""Test legacy redirects"""

import pytest

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
