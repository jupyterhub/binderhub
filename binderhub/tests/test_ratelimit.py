import time
from unittest import mock

import pytest

from binderhub.ratelimit import RateLimiter, RateLimitExceeded


def test_rate_limit():
    r = RateLimiter(limit=10, period_seconds=60)
    assert r._limits == {}
    now = r.time()
    reset = int(now) + 60
    with mock.patch.object(r, "time", lambda: now):
        limit = r.increment("1.2.3.4")
    assert limit == {
        "remaining": 9,
        "reset": reset,
    }
    assert r._limits == {
        "1.2.3.4": limit,
    }
    for i in range(1, 10):
        limit = r.increment("1.2.3.4")
        assert limit == {
            "remaining": 9 - i,
            "reset": reset,
        }

    for i in range(5):
        with pytest.raises(RateLimitExceeded):
            r.increment("1.2.3.4")

    assert r._limits["1.2.3.4"]["remaining"] == -5


def test_rate_limit_expires():
    r = RateLimiter(limit=10, period_seconds=60)
    assert r._limits == {}
    now = r.time()
    reset = int(now) + 60

    for i in range(5):
        limit = r.increment("1.2.3.4")

    # now expire period, should get fresh limit
    with mock.patch.object(r, "time", lambda: now + 65):
        limit = r.increment("1.2.3.4")
    assert limit == {
        "remaining": 9,
        "reset": int(now) + 65 + 60,
    }


def test_rate_limit_clean():
    r = RateLimiter(limit=10, period_seconds=60)
    assert r._limits == {}
    now = r.time()

    limit = r.increment("1.2.3.4")

    with mock.patch.object(r, "time", lambda: now + 30):
        limit2 = r.increment("4.3.2.1")

    # force clean, shouldn't expire
    r._last_cleaned = now - r.clean_seconds
    with mock.patch.object(r, "time", lambda: now + 35):
        limit2 = r.increment("4.3.2.1")

    assert "1.2.3.4" in r._limits

    # force clean again, should expire
    r._last_cleaned = now - r.clean_seconds
    with mock.patch.object(r, "time", lambda: now + 65):
        limit2 = r.increment("4.3.2.1")

    assert r._last_cleaned == now + 65
    assert "1.2.3.4" not in r._limits
    assert "4.3.2.1" in r._limits
    # 4.3.2.1 hasn't expired, still consuming rate limit
    assert limit2["remaining"] == 7
