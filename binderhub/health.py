import asyncio

from functools import wraps

from tornado.httpclient import AsyncHTTPClient

from .base import BaseHandler


def retry(_f=None, *, delay=1, attempts=3):
    """Retry calling the decorated function if it raises an exception

    Repeated calls are spaced by `delay` seconds and a total of `attempts`
    retries will be made.
    """

    def repeater(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            nonlocal attempts
            while attempts > 0:
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    if attempts == 1:
                        raise
                    else:
                        attempts -= 1
                        await asyncio.sleep(delay)

        return wrapper

    if _f is None:
        return repeater
    else:
        return repeater(_f)


def false_if_raises(f):
    """Return False if `f` raises an exception"""

    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            res = await f(*args, **kwargs)
        except Exception as e:
            res = False
        return res

    return wrapper


class HealthHandler(BaseHandler):
    """Serve health status"""

    def initialize(self, hub_url=None):
        self.hub_url = hub_url

    @false_if_raises
    @retry
    async def check_jupyterhub_api(self, hub_url):
        """Check JupyterHub API health"""
        await AsyncHTTPClient().fetch(hub_url + "hub/health", request_timeout=2)

        return True

    @false_if_raises
    @retry
    async def check_docker_registry(self):
        """Check docker registry health"""
        registry = self.settings["registry"].url

        if not registry.endswith("/"):
            registry += "/"

        # docker registries don't have an explicit health check endpoint.
        # Instead the recommendation is to query the "root" endpoint which
        # should return a 401 status when everything is well
        r = await AsyncHTTPClient().fetch(
            registry, request_timeout=3, raise_error=False
        )
        return r.code in (200, 401)

    async def get(self):
        checks = []

        if self.settings["use_registry"]:
            res = await self.check_docker_registry()
            checks.append({"service": "docker-registry", "ok": res})

        res = await self.check_jupyterhub_api(self.hub_url)
        checks.append({"service": "JupyterHub API", "ok": res})

        overall = all(check["ok"] for check in checks)
        if not overall:
            self.set_status(503)

        self.write({"ok": overall, "checks": checks})
