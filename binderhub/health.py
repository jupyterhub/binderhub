import asyncio
import json
import time

from functools import wraps

from tornado.httpclient import AsyncHTTPClient
from tornado.log import app_log

from .base import BaseHandler
from .utils import KUBE_REQUEST_TIMEOUT


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
            app_log.exception(f"Error checking {f.__name__}")
            res = False
        return res

    return wrapper


def at_most_every(_f=None, *, interval=60):
    """Call the wrapped function at most every `interval` seconds.

    Useful when `f` is (very) expensive to compute and you are happy
    to have results which are possibly a few seconds out of date.
    """
    last_time = time.monotonic() - interval - 1
    last_result = None
    outstanding = None

    def caller(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            nonlocal last_time, last_result, outstanding
            if outstanding is not None:
                # do not allow multiple concurrent calls, return an existing future
                return await outstanding
            now = time.monotonic()
            if now > last_time + interval:
                outstanding = asyncio.ensure_future(f(*args, **kwargs))
                try:
                    last_result = await outstanding
                finally:
                    # complete, clear outstanding future and note the time
                    outstanding = None
                    last_time = time.monotonic()
            return last_result

        return wrapper

    if _f is None:
        return caller
    else:
        return caller(_f)


class HealthHandler(BaseHandler):
    """Serve health status"""

    # demote logging of 200 responses to debug-level
    # to avoid flooding logs with health checks
    log_success_debug = True

    # Do not check request ip when getting health status
    # we want to allow e.g. federation members to check each other's
    # health, but not launch Binders
    skip_check_request_ip = True

    def initialize(self, hub_url=None):
        self.hub_url = hub_url

    @at_most_every
    async def _get_pods(self):
        """Get information about build and user pods"""
        namespace = self.settings["build_namespace"]
        k8s = self.settings["kubernetes_client"]
        pool = self.settings["executor"]

        app_log.info(f"Getting pod statistics for {namespace}")

        label_selectors = [
            "app=jupyterhub,component=singleuser-server",
            "component=binderhub-build",
        ]
        requests = [
            asyncio.wrap_future(
                pool.submit(
                    k8s.list_namespaced_pod,
                    namespace,
                    label_selector=label_selector,
                    _preload_content=False,
                    _request_timeout=KUBE_REQUEST_TIMEOUT,
                )
            )
            for label_selector in label_selectors
        ]
        responses = await asyncio.gather(*requests)
        return [json.loads(resp.read())["items"] for resp in responses]

    @false_if_raises
    @retry
    async def check_jupyterhub_api(self, hub_url):
        """Check JupyterHub API health"""
        await AsyncHTTPClient().fetch(hub_url + "hub/health", request_timeout=3)
        return True

    @false_if_raises
    @at_most_every(interval=15)
    @retry
    async def check_docker_registry(self):
        """Check docker registry health"""
        app_log.info("Checking registry status")
        registry = self.settings["registry"]
        # we are only interested in getting a response from the registry, we
        # don't care if the image actually exists or not
        image_name = self.settings["image_prefix"] + "some-image-name:12345"
        await registry.get_image_manifest(
            *'/'.join(image_name.split('/')[-2:]).split(':', 1)
        )
        return True

    async def check_pod_quota(self):
        """Compare number of active pods to available quota"""
        user_pods, build_pods = await self._get_pods()

        n_user_pods = len(user_pods)
        n_build_pods = len(build_pods)

        quota = self.settings["pod_quota"]
        total_pods = n_user_pods + n_build_pods
        usage = {
            "total_pods": total_pods,
            "build_pods": n_build_pods,
            "user_pods": n_user_pods,
            "quota": quota,
            "ok": total_pods <= quota if quota is not None else True,
        }
        return usage

    async def check_all(self):
        """Runs all health checks and returns a tuple (overall, checks).

        `overall` is a bool representing the overall status of the service
        `checks` contains detailed information on each check's result
        """
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
            unhealthy = [check for check in checks if not check["ok"]]
            app_log.warning(f"Unhealthy services: {unhealthy}")
        return overall, checks

    async def get(self):
        overall, checks = await self.check_all()
        if not overall:
            self.set_status(503)
        self.write({"ok": overall, "checks": checks})

    async def head(self):
        overall, checks = await self.check_all()
        if not overall:
            self.set_status(503)
