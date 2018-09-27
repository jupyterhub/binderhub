"""Test authentication"""
import pytest
from .utils import async_requests


@pytest.mark.parametrize(
    'app,path,authenticated',
    [
        (True, '', True),  # main page
        (True, 'v2/gh/binderhub-ci-repos/requirements/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd', True),
        (True, 'metrics', False),
    ],
    indirect=['app']  # send param True to app fixture, so that it loads authentication configuration
)
@pytest.mark.gen_test
@pytest.mark.auth_test
def test_auth(app, path, authenticated):
    service_path = app.base_url.lstrip('/')
    service_url = f'{app.hub_url}{service_path}'
    url = f'{service_url}{path}'
    async_requests.set_session()
    r = yield async_requests.get(url)
    assert r.status_code == 200, f"{r.status_code} {url}"
    if authenticated:
        login_url = r.url
        r = yield async_requests.post(login_url, data={'username': 'dummy', 'password': 'dummy'})
        assert r.status_code == 200, f"{r.status_code} {login_url}"
    assert r.url == url
    async_requests.delete_session()
