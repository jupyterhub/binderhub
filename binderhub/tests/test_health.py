"""Test health handler"""

from .utils import async_requests


async def test_basic_health(app):
    r = await async_requests.get(app.url + "/health")

    assert r.status_code == 200
    assert r.json() == {
        "ok": True,
        "checks": [{"service": "JupyterHub API", "ok": True}],
    }
