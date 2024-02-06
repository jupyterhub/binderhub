"""Test launch quotas"""

import concurrent.futures
import json
from unittest import mock

import pytest

from binderhub.quota import KubernetesLaunchQuota, LaunchQuotaExceeded


@pytest.fixture
def mock_pod_list_resp():
    r = mock.MagicMock()
    r.read.return_value = json.dumps(
        {
            "items": [
                {
                    "spec": {
                        "containers": [
                            {"image": "example.org/test/kubernetes_quota:1.2.3"}
                        ],
                    },
                },
                {
                    "spec": {
                        "containers": [
                            {"image": "example.org/test/kubernetes_quota:latest"}
                        ],
                    },
                },
                {
                    "spec": {
                        "containers": [{"image": "example.org/test/other:abc"}],
                    },
                },
            ]
        }
    )
    f = concurrent.futures.Future()
    f.set_result(r)
    return f


async def test_kubernetes_quota_none(mock_pod_list_resp):
    quota = KubernetesLaunchQuota(api=mock.MagicMock(), executor=mock.MagicMock())
    quota.executor.submit.return_value = mock_pod_list_resp

    r = await quota.check_repo_quota(
        "example.org/test/kubernetes_quota", {}, "repo.url"
    )
    assert r is None


async def test_kubernetes_quota_allowed(mock_pod_list_resp):
    quota = KubernetesLaunchQuota(api=mock.MagicMock(), executor=mock.MagicMock())
    quota.executor.submit.return_value = mock_pod_list_resp

    r = await quota.check_repo_quota(
        "example.org/test/kubernetes_quota", {"quota": 3}, "repo.url"
    )
    assert r.total == 3
    assert r.matching == 2
    assert r.quota == 3


async def test_kubernetes_quota_total_exceeded(mock_pod_list_resp):
    quota = KubernetesLaunchQuota(
        api=mock.MagicMock(), executor=mock.MagicMock(), total_quota=3
    )
    quota.executor.submit.return_value = mock_pod_list_resp

    with pytest.raises(LaunchQuotaExceeded) as excinfo:
        await quota.check_repo_quota(
            "example.org/test/kubernetes_quota", {}, "repo.url"
        )
    assert excinfo.value.message == "Too many users on this BinderHub! Try again soon."
    assert excinfo.value.quota == 3
    assert excinfo.value.used == 3
    assert excinfo.value.status == "pod_quota"


async def test_kubernetes_quota_repo_exceeded(mock_pod_list_resp):
    quota = KubernetesLaunchQuota(api=mock.MagicMock(), executor=mock.MagicMock())
    quota.executor.submit.return_value = mock_pod_list_resp

    with pytest.raises(LaunchQuotaExceeded) as excinfo:
        await quota.check_repo_quota(
            "example.org/test/kubernetes_quota", {"quota": 2}, "repo.url"
        )
    assert excinfo.value.message == "Too many users running repo.url! Try again soon."
    assert excinfo.value.quota == 2
    assert excinfo.value.used == 2
    assert excinfo.value.status == "repo_quota"
