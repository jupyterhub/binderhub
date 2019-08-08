import asyncio
import time

from functools import wraps

from tornado.log import app_log

from .base import BaseHandler
from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST


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


class MetricsHandler(BaseHandler):
    async def get(self):
        self.set_header("Content-Type", CONTENT_TYPE_LATEST)
        self.write(generate_latest(REGISTRY))


class PodQuotaHandler(BaseHandler):
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

    async def get(self):
        """Serve statistics about current usage and maximum capacity"""
        user_pods, build_pods = await self._get_pods()

        n_user_pods = len(user_pods.items)
        n_build_pods = len(build_pods.items)

        usage = {
            "total_pods": n_user_pods + n_build_pods,
            "build_pods": n_build_pods,
            "user_pods": n_user_pods,
        }

        pod_quota = self.settings.get("pod_quota", None)
        if pod_quota is not None:
            usage["quota"] = pod_quota

        self.write(usage)
