import asyncio
import json
import time
from functools import wraps

from tornado.httpclient import AsyncHTTPClient
from tornado.log import app_log

from .base import BaseHandler
from .builder import _get_image_basename_and_tag
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
                        app_log.exception(
                            f"Error checking {f.__name__}: {e}. Retrying ({attempts} attempts remaining)"
                        )
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
        except Exception:
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
    # use 'unset' singleton to indicate that last_result has not yet been cached
    last_result = unset = object()
    outstanding = None

    def caller(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            nonlocal last_time, last_result, outstanding
            if outstanding is not None:
                # do not allow multiple concurrent calls, return an existing future
                return await outstanding
            now = time.monotonic()
            if last_result is unset or now > last_time + interval:
                outstanding = asyncio.ensure_future(f(*args, **kwargs))
                try:
                    last_result = await outstanding
                finally:
                    # complete, clear outstanding future and note the time
                    outstanding = None
                    last_time = time.monotonic()

            if last_result is unset:
                # this should be impossible, but make sure we don't return our no-result singleton
                raise RuntimeError("No cached result to return")

            return last_result

        return wrapper

    if _f is None:
        return caller
    else:
        return caller(_f)


def _log_duration(f):
    """Record the time for a given health check to run"""

    @wraps(f)
    async def wrapped(*args, **kwargs):
        tic = time.perf_counter()
        try:
            return await f(*args, **kwargs)
        finally:
            t = time.perf_counter() - tic
            if t > 0.5:
                log = app_log.info
            else:
                log = app_log.debug
            log(f"Health check {f.__name__} took {t:.3f}s")

    return wrapped


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

    @at_most_every(interval=15)
    @false_if_raises
    @retry
    @_log_duration
    async def check_jupyterhub_api(self, hub_url):
        """Check JupyterHub API health"""
        await AsyncHTTPClient().fetch(hub_url + "hub/api/health", request_timeout=3)
        return True

    @at_most_every(interval=15)
    @false_if_raises
    @retry
    @_log_duration
    async def check_docker_registry(self):
        """Check docker registry health"""
        app_log.info("Checking registry status")
        registry = self.settings["registry"]
        # we are only interested in getting a response from the registry, we
        # don't care if the image actually exists or not
        image_fullname = self.settings["image_prefix"] + "some-image-name:12345"
        name, tag = _get_image_basename_and_tag(image_fullname)
        await registry.get_image_manifest(name, tag)
        return True

    def get_checks(self, checks):
        """Add health checks to the `checks` dict

        checks: Dictionary, updated in-place:
          key: service name
          value: a future that resolves to either:
            - a bool (success/fail)
            - a dict with the field `"ok": bool` plus other information
        """
        if self.settings["use_registry"]:
            checks["Docker registry"] = self.check_docker_registry()
        checks["JupyterHub API"] = self.check_jupyterhub_api(self.hub_url)

    async def check_all(self):
        """Runs all health checks and returns a tuple (overall, results).

        `overall` is a bool representing the overall status of the service
        `results` contains detailed information on each check's result
        """
        checks = {}
        results = []
        self.get_checks(checks)

        for result, service in zip(
            await asyncio.gather(*checks.values()), checks.keys()
        ):
            if isinstance(result, bool):
                results.append({"service": service, "ok": result})
            else:
                results.append(dict({"service": service}, **result))

        # Some checks are for information but do not count as a health failure
        overall = all(r["ok"] for r in results if not r.get("_ignore_failure", False))
        if not overall:
            unhealthy = [r for r in results if not r["ok"]]
            app_log.warning(f"Unhealthy services: {unhealthy}")
        return overall, results

    async def get(self):
        overall, checks = await self.check_all()
        if not overall:
            self.set_status(503)
        self.write({"ok": overall, "checks": checks})

    async def head(self):
        overall, checks = await self.check_all()
        if not overall:
            self.set_status(503)


class KubernetesHealthHandler(HealthHandler):
    """Serve health status on Kubernetes"""

    @at_most_every
    @_log_duration
    async def _get_pods(self):
        """Get information about build and user pods"""
        namespace = self.settings["example_builder"].namespace
        k8s = self.settings["example_builder"].api
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

    def get_checks(self, checks):
        super().get_checks(checks)
        checks["Pod quota"] = self._check_pod_quotas()

    async def _check_pod_quotas(self):
        """Compare number of active pods to available quota"""
        user_pods, build_pods = await self._get_pods()

        n_user_pods = len(user_pods)
        n_build_pods = len(build_pods)

        quota = self.settings["launch_quota"].total_quota
        total_pods = n_user_pods + n_build_pods
        usage = {
            "total_pods": total_pods,
            "build_pods": n_build_pods,
            "user_pods": n_user_pods,
            "quota": quota,
            "ok": total_pods <= quota if quota is not None else True,
            # The pod quota is treated as a soft quota
            # Being above quota doesn't mean the service is unhealthy
            "_ignore_failure": True,
        }
        return usage
