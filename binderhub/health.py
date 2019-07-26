import asyncio
import json

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
        registry = self.settings["registry"]
        # we are only interested in getting a response from the registry, we
        # don't care if the image actually exists or not
        await registry.get_image_manifest(
            self.settings["image_prefix"] + "some-image-name"
        )
        return True

    async def get(self):
        checks = []

        if self.settings["use_registry"]:
            res = await self.check_docker_registry()
            checks.append({"service": "docker-registry", "ok": res})

        res = await self.check_jupyterhub_api(self.hub_url)
        checks.append({"service": "JupyterHub API", "ok": res})

        self.write(
            json.dumps({"ok": all(check["ok"] for check in checks), "checks": checks})
        )
