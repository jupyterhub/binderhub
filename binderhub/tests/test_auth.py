"""Test authentication"""
import pytest
from .utils import async_requests


@pytest.fixture
def use_session():
    # setup
    async_requests.set_session()
    yield "run the test function"
    # teardown
    async_requests.delete_session()


@pytest.mark.parametrize(
    'app,path,authenticated',
    [
        (True, '', True),  # main page
        (True, 'v2/gh/binderhub-ci-repos/requirements/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd', True),
        (True, 'metrics', False),
    ],
    indirect=['app']  # send param True to app fixture, so that it loads authentication configuration
)
@pytest.mark.auth_test
async def test_auth(app, path, authenticated, use_session):
    service_path = app.base_url.lstrip('/')
    service_url = f'{app.hub_url}{service_path}'
    url = f'{service_url}{path}'
    r = await async_requests.get(url)
    assert r.status_code == 200, f"{r.status_code} {url}"
    r2 = await async_requests.post(r.url, data={'username': 'dummy', 'password': 'dummy'})
    if authenticated:
        assert r2.status_code == 200, f"{r2.status_code} {r.url}"
    else:
        # not allowed
        assert r2.status_code == 405, f"{r2.status_code} {r.url}"
    assert r2.url == url
