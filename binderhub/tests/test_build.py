"""Test building repos"""

import json
import sys
from time import monotonic
from unittest import mock
from urllib.parse import quote
from uuid import uuid4

import docker
import pytest
from kubernetes import client
from tornado.httputil import url_concat
from tornado.queues import Queue

from binderhub.build import BuildExecutor, KubernetesBuildExecutor, ProgressEvent
from binderhub.build_local import LocalRepo2dockerBuild, ProcessTerminated, _execute_cmd

from .utils import async_requests


# We have optimized this slow test, for more information, see the README of
# https://github.com/binderhub-ci-repos/minimal-dockerfile.
@pytest.mark.asyncio(timeout=900)
@pytest.mark.parametrize(
    "slug",
    [
        # git/ Git repo provider
        "git/{}/HEAD".format(
            quote(
                "https://github.com/binderhub-ci-repos/cached-minimal-dockerfile",
                safe="",
            )
        ),
        "git/{}/596b52f10efb0c9befc0c4ae850cc5175297d71c".format(
            quote(
                "https://github.com/binderhub-ci-repos/cached-minimal-dockerfile",
                safe="",
            )
        ),
        # gh/ GitHub repo provider
        "gh/binderhub-ci-repos/cached-minimal-dockerfile/HEAD",
        "gh/binderhub-ci-repos/cached-minimal-dockerfile/596b52f10efb0c9befc0c4ae850cc5175297d71c",
        # test redirect master->HEAD
        "gh/binderhub-ci-repos/cached-minimal-dockerfile/master",
        # gl/ GitLab repo provider
        "gl/binderhub-ci-repos%2Fcached-minimal-dockerfile/HEAD",
        "gl/binderhub-ci-repos%2Fcached-minimal-dockerfile/596b52f10efb0c9befc0c4ae850cc5175297d71c",
    ],
)
@pytest.mark.remote
async def test_build(app, needs_build, needs_launch, always_build, slug, pytestconfig):
    """
    Test build a repo that is very quick and easy to build.
    """
    # can't use mark.github_api since only some tests here use GitHub
    if slug.startswith("gh/") and "not github_api" in pytestconfig.getoption(
        "markexpr"
    ):
        pytest.skip("Skipping GitHub API test")
    build_url = f"{app.url}/build/{slug}"
    r = await async_requests.get(build_url, stream=True)
    r.raise_for_status()
    events = []
    launch_events = 0
    async for line in async_requests.iter_lines(r):
        line = line.decode("utf8", "replace")
        if line.startswith("data:"):
            event = json.loads(line.split(":", 1)[1])
            events.append(event)
            assert "message" in event
            sys.stdout.write(f"{event.get('phase', '')}: {event['message']}")
            # this is the signal that everything is ready, pod is launched
            # and server is up inside the pod. Break out of the loop now
            # because BinderHub keeps the connection open for many seconds
            # after to avoid "reconnects" from slow clients
            if event.get("phase") == "ready":
                r.close()
                break
            if event.get("phase") == "launching" and not event["message"].startswith(
                ("Launching server...", "Launch attempt ")
            ):
                # skip standard launching events of builder
                # we are interested in launching events from spawner
                launch_events += 1

    assert launch_events > 0
    final = events[-1]
    assert "phase" in final
    assert final["phase"] == "ready"
    assert "url" in final
    assert "token" in final
    print(final["url"])
    r = await async_requests.get(url_concat(final["url"], {"token": final["token"]}))
    r.raise_for_status()
    assert r.url.startswith(final["url"])

    # stop the server
    stop = await async_requests.post(
        url_concat(f"{final['url']}api/shutdown", {"token": final["token"]})
    )
    stop.raise_for_status()


@pytest.mark.asyncio(timeout=900)
@pytest.mark.parametrize(
    "app,build_only_query_param",
    [
        ("api_only_app", "True"),
    ],
    indirect=[
        "app"
    ],  # send param "api_only_app" to app fixture, so that it loads `enable_api_only_mode` configuration
)
async def test_build_only(app, build_only_query_param, needs_build):
    """
    Test build a repo that is very quick and easy to build.
    """
    slug = "gh/binderhub-ci-repos/cached-minimal-dockerfile/HEAD"
    build_url = f"{app.url}/build/{slug}"
    r = await async_requests.get(
        build_url, stream=True, params={"build_only": build_only_query_param}
    )
    r.raise_for_status()
    events = []
    launch_events = 0
    async for line in async_requests.iter_lines(r):
        line = line.decode("utf8", "replace")
        if line.startswith("data:"):
            event = json.loads(line.split(":", 1)[1])
            events.append(event)
            assert "message" in event
            sys.stdout.write(f"{event.get('phase', '')}: {event['message']}")
            if event.get("phase") == "ready":
                r.close()
                break
            if event.get("phase") == "info":
                assert (
                    "The built image will not be launched because the API only mode was enabled and the query parameter `build_only` was set to true"
                    in event["message"]
                )
            if event.get("phase") == "launching" and not event["message"].startswith(
                ("Launching server...", "Launch attempt ")
            ):
                # skip standard launching events of builder
                # we are interested in launching events from spawner
                launch_events += 1

    assert launch_events == 0
    final = events[-1]
    assert "phase" in final
    assert final["phase"] == "ready"


@pytest.mark.asyncio(timeout=120)
@pytest.mark.remote
async def test_build_fail(app, needs_build, needs_launch, always_build):
    """
    Test build a repo that should fail immediately.
    """
    slug = "gh/binderhub-ci-repos/minimal-dockerfile/failed"
    build_url = f"{app.url}/build/{slug}"
    r = await async_requests.get(build_url, stream=True)
    r.raise_for_status()
    failed_events = 0
    async for line in async_requests.iter_lines(r):
        line = line.decode("utf8", "replace")
        if line.startswith("data:"):
            event = json.loads(line.split(":", 1)[1])
            assert event.get("phase") not in ("launching", "ready")
            if event.get("phase") == "failed":
                failed_events += 1
                break
    r.close()

    assert failed_events > 0, "Should have seen phase 'failed'"


@pytest.mark.asyncio(timeout=120)
@pytest.mark.parametrize(
    "app,build_only_query_param,expected_error_msg",
    [
        (
            "app_without_require_build_only",
            True,
            "Building but not launching is not permitted",
        ),
    ],
    indirect=[
        "app"
    ],  # send param "require_build_only_app" to app fixture, so that it loads `require_build_only` configuration
)
async def test_build_only_fail(
    app, build_only_query_param, expected_error_msg, needs_build
):
    """
    Test the scenarios that are expected to fail when setting configs for building but no launching.

    Table for evaluating whether or not the image will be launched after build based on the values of
    the `enable_api_only_mode` traitlet and the `build_only` query parameter.

    | `enable_api_only_mode` trait | `build_only` query param | Outcome
    ------------------------------------------------------------------------------------------------
    |  false                     | missing                  | OK, image will be launched after build
    |  false                     | false                    | OK, image will be launched after build
    |  false                     | true                     | ERROR, building but not launching is not permitted when UI is still enabled
    |  true                      | missing                  | OK, image will be launched after build
    |  true                      | false                    | OK, image will be launched after build
    |  true                      | true                     | OK, image won't be launched after build
    """

    slug = "gh/binderhub-ci-repos/cached-minimal-dockerfile/HEAD"
    build_url = f"{app.url}/build/{slug}"
    r = await async_requests.get(
        build_url, stream=True, params={"build_only": build_only_query_param}
    )
    r.raise_for_status()
    failed_events = 0
    async for line in async_requests.iter_lines(r):
        line = line.decode("utf8", "replace")
        if line.startswith("data:"):
            event = json.loads(line.split(":", 1)[1])
            assert event.get("phase") not in ("launching", "ready")
            if event.get("phase") == "failed":
                failed_events += 1
                assert expected_error_msg in event["message"]
                break
    r.close()

    assert failed_events > 0, "Should have seen phase 'failed'"


def _list_image_builder_pods_mock():
    """Mock list of DIND pods"""
    mock_response = mock.MagicMock()
    mock_response.read.return_value = json.dumps(
        {
            "items": [
                {
                    "spec": {"nodeName": name},
                }
                for name in ["node-a", "node-b"]
            ]
        }
    )
    mock_k8s_api = mock.MagicMock()
    mock_k8s_api.list_namespaced_pod.return_value = mock_response
    return mock_k8s_api


def test_default_affinity():
    # check that the default affinity is a pod anti-affinity

    mock_k8s_api = _list_image_builder_pods_mock()

    build = KubernetesBuildExecutor(
        q=mock.MagicMock(),
        api=mock_k8s_api,
        name="test_build",
        namespace="build_namespace",
        repo_url="repo",
        ref="ref",
        build_image="image",
        image_name="name",
        push_secret="",
        memory_limit=0,
        git_credentials="",
        docker_host="http://mydockerregistry.local",
        node_selector={},
    )

    affinity = build.get_affinity()

    assert isinstance(affinity, client.V1Affinity)
    assert affinity.node_affinity is None
    assert affinity.pod_affinity is None
    assert affinity.pod_anti_affinity is not None


def test_sticky_builds_affinity():
    # Setup some mock objects for the response from the k8s API
    mock_k8s_api = _list_image_builder_pods_mock()

    build = KubernetesBuildExecutor(
        q=mock.MagicMock(),
        api=mock_k8s_api,
        name="test_build",
        namespace="build_namespace",
        repo_url="repo",
        ref="ref",
        build_image="image",
        image_name="name",
        push_secret="",
        memory_limit=0,
        git_credentials="",
        docker_host="http://mydockerregistry.local",
        node_selector={},
        sticky_builds=True,
    )

    affinity = build.get_affinity()

    assert isinstance(affinity, client.V1Affinity)
    assert affinity.node_affinity is not None
    assert affinity.pod_affinity is None
    assert affinity.pod_anti_affinity is None

    # One of the two nodes we have in our mock should be the preferred node
    assert affinity.node_affinity.preferred_during_scheduling_ignored_during_execution[
        0
    ].preference.match_expressions[0].values[0] in ("node-a", "node-b")


def test_build_memory_limits():
    # Setup some mock objects for the response from the k8s API
    mock_k8s_api = _list_image_builder_pods_mock()

    build = KubernetesBuildExecutor(
        q=mock.MagicMock(),
        api=mock_k8s_api,
        name="test_build",
        namespace="build_namespace",
        repo_url="repo",
        ref="ref",
        build_image="image",
        image_name="name",
        push_secret="",
        memory_limit="2T",
        memory_request="123G",
        git_credentials="",
        docker_host="http://mydockerregistry.local",
        node_selector={},
        sticky_builds=True,
    )
    assert build.memory_limit == 2199023255552
    assert build.memory_request == 132070244352


def test_git_credentials_passed_to_podspec_upon_submit():
    git_credentials = """{
        "client_id": "my_username",
        "access_token": "my_access_token",
    }"""

    mock_k8s_api = _list_image_builder_pods_mock()

    build = KubernetesBuildExecutor(
        q=mock.MagicMock(),
        api=mock_k8s_api,
        name="test_build",
        namespace="build_namespace",
        repo_url="repo",
        ref="ref",
        build_image="image",
        image_name="name",
        push_secret="",
        memory_limit=0,
        git_credentials=git_credentials,
        docker_host="http://mydockerregistry.local",
        node_selector={},
    )

    with mock.patch.object(build.stop_event, "is_set", return_value=True):
        build.submit()

    call_args_list = mock_k8s_api.create_namespaced_pod.call_args_list
    assert len(call_args_list) == 1

    args = call_args_list[0][0]
    pod = args[1]

    assert len(pod.spec.containers) == 1

    env = {env_var.name: env_var.value for env_var in pod.spec.containers[0].env}

    assert env["GIT_CREDENTIAL_ENV"] == git_credentials


def test_extra_environment_variables_passed_to_podspec_upon_submit():
    extra_environments = {
        "CONTAINER_HOST": "unix:///var/run/docker.sock",
        "REGISTRY_AUTH_FILE": "/root/.docker/config.json",
    }

    mock_k8s_api = _list_image_builder_pods_mock()

    class EnvBuild(KubernetesBuildExecutor):
        q = mock.MagicMock()
        api = mock_k8s_api
        name = "test_build"
        repo_url = "repo"
        ref = "ref"
        image_name = "name"
        extra_envs = extra_environments
        namespace = "build_namespace"
        push_secret = ""
        build_image = "image"
        memory_limit = 0
        docker_host = "http://mydockerregistry.local"
        node_selector = {}

    build = EnvBuild()

    with mock.patch.object(build.stop_event, "is_set", return_value=True):
        build.submit()

    call_args_list = mock_k8s_api.create_namespaced_pod.call_args_list
    assert len(call_args_list) == 1

    args = call_args_list[0][0]
    pod = args[1]

    assert len(pod.spec.containers) == 1

    env = {env_var.name: env_var.value for env_var in pod.spec.containers[0].env}

    assert env == extra_environments


def test_build_image_pull_secrets():
    build_pull_secrets = ["build-image-secret", "build-image-secret-2"]

    mock_k8s_api = _list_image_builder_pods_mock()

    class PullBuild(KubernetesBuildExecutor):
        q = mock.MagicMock()
        api = mock_k8s_api
        name = "test_build"
        repo_url = "repo"
        ref = "ref"
        image_name = "name"
        namespace = "build_namespace"
        push_secret = ""
        build_image = "image"
        image_pull_secrets = build_pull_secrets
        memory_limit = 0
        docker_host = "http://mydockerregistry.local"
        node_selector = {}

    build = PullBuild()

    with mock.patch.object(build.stop_event, "is_set", return_value=True):
        build.submit()

    call_args_list = mock_k8s_api.create_namespaced_pod.call_args_list
    assert len(call_args_list) == 1

    args = call_args_list[0][0]
    pod = args[1]

    assert len(pod.spec.containers) == 1

    pull_secrets = [secret.name for secret in pod.spec.image_pull_secrets]

    assert pull_secrets == build_pull_secrets


async def test_local_repo2docker_build():
    q = Queue()
    repo_url = "https://github.com/binderhub-ci-repos/cached-minimal-dockerfile"
    ref = "HEAD"
    name = str(uuid4())

    build = LocalRepo2dockerBuild(
        q=q,
        name=name,
        repo_url=repo_url,
        ref=ref,
        image_name=name,
    )
    build.submit()

    events = []
    while True:
        event = await q.get(10)
        if (
            event.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE
            and event.payload == ProgressEvent.BuildStatus.BUILT
        ):
            break
        events.append(event)

    # Image should now exist locally
    docker_client = docker.from_env(version="auto")
    assert docker_client.images.get(name)


@pytest.mark.asyncio(timeout=20)
async def test_local_repo2docker_build_stop(io_loop):
    q = Queue()
    # We need a slow build here so that we can interrupt it, so pick a large repo that
    # will take several seconds to clone
    repo_url = "https://github.com/jupyterhub/jupyterhub"
    ref = "HEAD"
    name = str(uuid4())

    build = LocalRepo2dockerBuild(
        q=q,
        name=name,
        repo_url=repo_url,
        ref=ref,
        image_name=name,
    )
    io_loop.run_in_executor(None, build.submit)

    # Get first few log messages to check it successfully stared
    event = await q.get()
    assert event.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE
    assert event.payload == ProgressEvent.BuildStatus.RUNNING

    for i in range(2):
        event = await q.get()
        assert event.kind == ProgressEvent.Kind.LOG_MESSAGE
        assert "message" in event.payload

    build.stop()

    for i in range(10):
        event = await q.get()
        if (
            event.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE
            and event.payload == ProgressEvent.BuildStatus.FAILED
        ):
            break
    assert (
        event.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE
        and event.payload == ProgressEvent.BuildStatus.FAILED
    )

    # Todo: check that process was stopped, and we didn't just return early and leave it in the background

    # Build was stopped so image should not exist locally
    docker_client = docker.from_env(version="auto")
    with pytest.raises(docker.errors.ImageNotFound):
        docker_client.images.get(name)


def test_execute_cmd():
    cmd = [
        "python",
        "-c",
        "from time import sleep; print(1, flush=True); sleep(2); print(2, flush=True)",
    ]
    lines = list(_execute_cmd(cmd, capture=True))
    assert lines == ["1\n", "2\n"]


def test_execute_cmd_break():
    cmd = [
        "python",
        "-c",
        "from time import sleep; print(1, flush=True); sleep(10); print(2, flush=True)",
    ]
    lines = []
    now = monotonic()

    def break_callback():
        return monotonic() - now > 2

    # This should break after the first line
    with pytest.raises(ProcessTerminated) as exc:
        for line in _execute_cmd(cmd, capture=True, break_callback=break_callback):
            lines.append(line)
    assert lines == ["1\n"]
    assert str(exc.value) == f"ProcessTerminated: {cmd}"


def test_extra_r2d_options():
    bex = BuildExecutor()
    bex.repo2docker_extra_args = ["--repo-dir=/srv/repo"]
    bex.image_name = "test:test"
    bex.ref = "main"

    assert bex.get_r2d_cmd_options() == [
        "--ref=main",
        "--image=test:test",
        "--no-clean",
        "--no-run",
        "--json-logs",
        "--user-name=jovyan",
        "--user-id=1000",
        "--repo-dir=/srv/repo",
    ]
