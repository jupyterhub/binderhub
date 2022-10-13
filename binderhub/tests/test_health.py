"""Test health handler"""

from .utils import async_requests


async def test_basic_health(app):
    r = await async_requests.get(app.url + "/health")

    assert r.status_code == 200
    results = r.json()

    assert results["ok"]
    assert "checks" in results

    checks = results["checks"]

    assert {"service": "JupyterHub API", "ok": True} in checks

    # find the result of the quota check
    quota_check = [c for c in checks if c["service"] == "Pod quota"][0]
    assert quota_check
    assert quota_check["quota"] is None
    for key in ("build_pods", "total_pods", "user_pods"):
        assert key in quota_check

    assert (
        quota_check["total_pods"]
        == quota_check["build_pods"] + quota_check["user_pods"]
    )

    # HEAD requests should work as well
    r = await async_requests.head(app.url + "/health")
    assert r.status_code == 200
