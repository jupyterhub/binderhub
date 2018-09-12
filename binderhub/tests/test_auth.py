"""Test authentication"""
import pytest
from urllib.parse import quote
from .utils import async_requests


@pytest.mark.parametrize(
    'path,authenticated',
    [
        ('', True),  # main page
        ('v2/gh/binderhub-ci-repos/requirements/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd', True),
        ('metrics', False),
    ]
)
@pytest.mark.gen_test
@pytest.mark.auth_test
def test_auth(app_with_auth, path, authenticated):
    url = f'{app_with_auth.service_url}{path}'
    r = yield async_requests.get(url)
    assert r.status_code == 200
    if authenticated:
        next_url = f'{app_with_auth.base_url}{path}'
        assert r.url == f'{app_with_auth.hub_url}hub/login?next={quote(next_url, safe="")}'

        r = yield async_requests.post(r.url, data={'username': 'dummy', 'password': 'dummy'})
        assert r.status_code == 200
    assert r.url == url
