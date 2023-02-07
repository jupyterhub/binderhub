"""
Singleuser server quotas
"""

import asyncio
import json
import os
from collections import namedtuple

import kubernetes.config
from kubernetes import client
from traitlets import Any, Integer, Unicode, default
from traitlets.config import LoggingConfigurable

from .utils import KUBE_REQUEST_TIMEOUT


class LaunchQuotaExceeded(Exception):
    """Raised when a quota will be exceeded by a launch"""

    def __init__(self, message, *, quota, used, status):
        """
        message: User-facing message
        quota: Quota limit
        used: Quota used
        status: String indicating the type of quota
        """
        super().__init__()
        self.message = message
        self.quota = quota
        self.used = used
        self.status = status


ServerQuotaCheck = namedtuple("ServerQuotaCheck", ["total", "matching", "quota"])


class LaunchQuota(LoggingConfigurable):
    executor = Any(
        allow_none=True, help="Optional Executor to use for blocking operations"
    )

    total_quota = Integer(
        None,
        help="""
        The number of concurrent singleuser servers that can be run.

        None: no quota
        0: the hub can't run any singleuser servers (e.g. in maintenance mode)
        Positive integer: sets the quota
        """,
        allow_none=True,
        config=True,
    )

    async def check_repo_quota(self, image_name, repo_config, repo_url):
        """
        Check whether launching a repository would exceed a quota.

        Parameters
        ----------
        image_name: str
        repo_config: dict
        repo_url: str

        Returns
        -------
        If quotas are disabled returns None
        If quotas are exceeded raises LaunchQuotaExceeded
        Otherwise returns:
          - total servers
          - matching servers running image_name
          - quota
        """
        return None


class KubernetesLaunchQuota(LaunchQuota):
    api = Any(
        help="Kubernetes API object to make requests (kubernetes.client.CoreV1Api())",
    )

    @default("api")
    def _default_api(self):
        try:
            kubernetes.config.load_incluster_config()
        except kubernetes.config.ConfigException:
            kubernetes.config.load_kube_config()
        return client.CoreV1Api()

    namespace = Unicode(help="Kubernetes namespace to check", config=True)

    @default("namespace")
    def _default_namespace(self):
        return os.getenv("BUILD_NAMESPACE", "default")

    async def check_repo_quota(self, image_name, repo_config, repo_url):
        # the image name (without tag) is unique per repo
        # use this to count the number of pods running with a given repo
        # if we added annotations/labels with the repo name via KubeSpawner
        # we could do this better
        image_no_tag = image_name.rsplit(":", 1)[0]

        # TODO: put busy users in a queue rather than fail?
        # That would be hard to do without in-memory state.
        repo_quota = repo_config.get("quota")
        pod_quota = self.total_quota

        # Fetch info on currently running users *only* if quotas are set
        if pod_quota is not None or repo_quota:
            matching_pods = 0

            # TODO: run a watch to keep this up to date in the background
            f = self.executor.submit(
                self.api.list_namespaced_pod,
                self.namespace,
                label_selector="app=jupyterhub,component=singleuser-server",
                _request_timeout=KUBE_REQUEST_TIMEOUT,
                _preload_content=False,
            )
            resp = await asyncio.wrap_future(f)
            pods = json.loads(resp.read())["items"]
            total_pods = len(pods)

            if pod_quota is not None and total_pods >= pod_quota:
                # check overall quota first
                self.log.error(f"BinderHub is full: {total_pods}/{pod_quota}")
                raise LaunchQuotaExceeded(
                    "Too many users on this BinderHub! Try again soon.",
                    quota=pod_quota,
                    used=total_pods,
                    status="pod_quota",
                )

            for pod in pods:
                for container in pod["spec"]["containers"]:
                    # is the container running the same image as us?
                    # if so, count one for the current repo.
                    image = container["image"].rsplit(":", 1)[0]
                    if image == image_no_tag:
                        matching_pods += 1
                        break

            if repo_quota and matching_pods >= repo_quota:
                self.log.error(
                    f"{repo_url} has exceeded quota: {matching_pods}/{repo_quota} ({total_pods} total)"
                )
                raise LaunchQuotaExceeded(
                    f"Too many users running {repo_url}! Try again soon.",
                    quota=repo_quota,
                    used=matching_pods,
                    status="repo_quota",
                )

            return ServerQuotaCheck(
                total=total_pods, matching=matching_pods, quota=repo_quota
            )

        return None
