"""Rate limiting utilities"""

import time
from traitlets import Integer, Dict, Float, default
from traitlets.config import LoggingConfigurable


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""


class RateLimiter(LoggingConfigurable):
    """Class representing a collection of rate limits

    Has one method: `.increment(key)` which should be called when
    a given actor is attempting to consume a resource.
    `key` can be any hashable (e.g. request ip address).
    Each `key` has its own rate limit counter.

    If the rate limit is exhausted, a RateLimitExceeded exception is raised,
    otherwise a summary of the current rate limit remaining is returned.

    Rate limits are reset to zero at the end of `period_seconds`,
    not a sliding window,
    so the entire rate limit can be consumed instantly
    """

    period_seconds = Integer(
        3600,
        config=True,
        help="""The rate limit window""",
    )

    limit = Integer(
        10,
        config=True,
        help="""The number of requests to allow within period_seconds""",
    )

    clean_seconds = Integer(
        600,
        config=True,
        help="""Interval on which to clean out old limits.

        Avoids memory growth of unused limits
        """,
    )

    _limits = Dict()

    _last_cleaned = Float()

    @default("_last_cleaned")
    def _default_last_cleaned(self):
        return self.time()

    def _clean_limits(self):
        now = self.time()
        self._last_cleaned = now
        self._limits = {
            key: limit for key, limit in self._limits.items() if limit["reset"] > now
        }

    @staticmethod
    def time():
        """Mostly here to enable override in tests"""
        return time.time()

    def increment(self, key):
        """Check rate limit for a key

        key: key for recording rate limit. Each key tracks a different rate limit.
        Returns: {"remaining": int_remaining, "reset": int_timestamp}
        Raises: RateLimitExceeded if the request would exceed the rate limit.
        """
        now = int(self.time())
        if now - self._last_cleaned > self.clean_seconds:
            self._clean_limits()

        if key not in self._limits or self._limits[key]["reset"] < now:
            # no limit recorded, or reset expired
            self._limits[key] = {
                "remaining": self.limit,
                "reset": now + self.period_seconds,
            }
        limit = self._limits[key]
        # keep decrementing, so we have a track of excess requests
        # which indicate abuse
        limit["remaining"] -= 1
        if limit["remaining"] < 0:
            seconds_until_reset = int(limit["reset"] - now)
            raise RateLimitExceeded(
                f"Rate limit exceeded (by {-limit['remaining']}) for {key!r}, reset in {seconds_until_reset}s."
            )
        return limit
