import asyncio
import time

from functools import wraps

from tornado.httpclient import AsyncHTTPClient
from tornado.log import app_log

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


def at_most_every(_f=None, *, interval=10):
    """Call the wrapped function at most every `interval` seconds.

    Useful when `f` is (very) expensive to compute and you are happy
    to have results which are possibly a few seconds out of date.
    """
    last_time = time.monotonic() - interval - 1
    last_result = None

    def caller(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            nonlocal last_time, last_result
            now = time.monotonic()
            if now > last_time + interval:
                last_result = await f(*args, **kwargs)
                last_time = now
            return last_result

        return wrapper

    if _f is None:
        return caller
    else:
        return caller(_f)


class HealthHandler(BaseHandler):
    """Serve health status"""

    def initialize(self, hub_url=None):
        self.hub_url = hub_url

    @at_most_every
    async def _get_pods(self):
        """Get information about build and user pods"""
        app_log.info("Getting pod statistics")
        k8s = self.settings["kubernetes_client"]
        pool = self.settings["executor"]

        get_user_pods = asyncio.wrap_future(
            pool.submit(
                k8s.list_namespaced_pod,
                self.settings["build_namespace"],
                label_selector="app=jupyterhub,component=singleuser-server",
            )
        )

        get_build_pods = asyncio.wrap_future(
            pool.submit(
                k8s.list_namespaced_pod,
                self.settings["build_namespace"],
                label_selector="component=binderhub-build",
            )
        )

        return await asyncio.gather(get_user_pods, get_build_pods)

    @false_if_raises
    @retry
    async def check_jupyterhub_api(self, hub_url):
        """Check JupyterHub API health"""
        await AsyncHTTPClient().fetch(hub_url + "hub/health", request_timeout=3)

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

    async def check_pod_quota(self):
        """Compare number of active pods to available quota"""
        user_pods, build_pods = await self._get_pods()

        n_user_pods = len(user_pods.items)
        n_build_pods = len(build_pods.items)

        quota = self.settings["pod_quota"]
        total_pods = n_user_pods + n_build_pods
        usage = {
            "total_pods": total_pods,
            "build_pods": n_build_pods,
            "user_pods": n_user_pods,
            "quota": quota,
            "ok": total_pods <= quota,
        }
        return usage

    async def get(self):
        checks = []
        check_futures = []

        if self.settings["use_registry"]:
            check_futures.append(self.check_docker_registry())
            checks.append({"service": "Docker registry", "ok": False})

        check_futures.append(self.check_jupyterhub_api(self.hub_url))
        checks.append({"service": "JupyterHub API", "ok": False})

        check_futures.append(self.check_pod_quota())
        checks.append({"service": "Pod quota", "ok": False})

        for result, check in zip(await asyncio.gather(*check_futures), checks):
            if isinstance(result, bool):
                check["ok"] = result
            else:
                check.update(result)

        # The pod quota is treated as a soft quota this means being above
        # quota doesn't mean the service is unhealthy
        overall = all(
            check["ok"] for check in checks if check["service"] != "Pod quota"
        )
        if not overall:
            self.set_status(503)

        self.write({"ok": overall, "checks": checks})
