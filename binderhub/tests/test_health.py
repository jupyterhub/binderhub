"""Test health handler"""

import pytest

from .utils import async_requests


#@pytest.mark.remote
async def test_basic_health(app):
    r = await async_requests.get(app.url + "/health")
    print(r.json())
    assert r.status_code == 200
