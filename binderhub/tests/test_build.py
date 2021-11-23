"""Test building repos"""

import docker
import json
import sys
from time import monotonic
from unittest import mock
from urllib.parse import quote
from uuid import uuid4

import pytest
from tornado.httputil import url_concat
from tornado.queues import Queue

from kubernetes import client

from binderhub.build import Build, ProgressEvent
from binderhub.build_local import _execute_cmd, LocalRepo2dockerBuild, ProcessTerminated
from .utils import async_requests


# We have optimized this slow test, for more information, see the README of
# https://github.com/binderhub-ci-repos/minimal-dockerfile.
@pytest.mark.asyncio(timeout=900)
@pytest.mark.parametrize("slug", [
    # git/ Git repo provider
    "git/{}/HEAD".format(
        quote("https://github.com/binderhub-ci-repos/cached-minimal-dockerfile", safe='')
    ),
    "git/{}/596b52f10efb0c9befc0c4ae850cc5175297d71c".format(
        quote("https://github.com/binderhub-ci-repos/cached-minimal-dockerfile", safe='')
    ),
    # gh/ GitHub repo provider
    "gh/binderhub-ci-repos/cached-minimal-dockerfile/HEAD",
    "gh/binderhub-ci-repos/cached-minimal-dockerfile/596b52f10efb0c9befc0c4ae850cc5175297d71c",
    # gl/ GitLab repo provider
    "gl/binderhub-ci-repos%2Fcached-minimal-dockerfile/HEAD",
    "gl/binderhub-ci-repos%2Fcached-minimal-dockerfile/596b52f10efb0c9befc0c4ae850cc5175297d71c",
])
@pytest.mark.remote
async def test_build(app, needs_build, needs_launch, always_build, slug, pytestconfig):
    """
    Test build a repo that is very quick and easy to build.
    """
    # can't use mark.github_api since only some tests here use GitHub
    if slug.startswith('gh/') and "not github_api" in pytestconfig.getoption('markexpr'):
        pytest.skip("Skipping GitHub API test")
    build_url = f"{app.url}/build/{slug}"
    r = await async_requests.get(build_url, stream=True)
    r.raise_for_status()
    events = []
    launch_events = 0
    async for line in async_requests.iter_lines(r):
        line = line.decode('utf8', 'replace')
        if line.startswith('data:'):
            event = json.loads(line.split(':', 1)[1])
            events.append(event)
            assert 'message' in event
            sys.stdout.write(f"{event.get('phase', '')}: {event['message']}")
            # this is the signal that everything is ready, pod is launched
            # and server is up inside the pod. Break out of the loop now
            # because BinderHub keeps the connection open for many seconds
            # after to avoid "reconnects" from slow clients
            if event.get('phase') == 'ready':
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
    assert 'phase' in final
    assert final['phase'] == 'ready'
    assert 'url' in final
    assert 'token' in final
    print(final['url'])
    r = await async_requests.get(url_concat(final['url'], {'token': final['token']}))
    r.raise_for_status()
    assert r.url.startswith(final['url'])


def _list_dind_pods_mock():
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

    mock_k8s_api = _list_dind_pods_mock()

    build = Build(
        mock.MagicMock(), api=mock_k8s_api, name='test_build',
        namespace='build_namespace', repo_url=mock.MagicMock(),
        ref=mock.MagicMock(), build_image=mock.MagicMock(),
        image_name=mock.MagicMock(), push_secret=mock.MagicMock(),
        memory_limit=mock.MagicMock(), git_credentials=None,
        docker_host='http://mydockerregistry.local',
        node_selector=mock.MagicMock())

    affinity = build.get_affinity()

    assert isinstance(affinity, client.V1Affinity)
    assert affinity.node_affinity is None
    assert affinity.pod_affinity is None
    assert affinity.pod_anti_affinity is not None


def test_sticky_builds_affinity():
    # Setup some mock objects for the response from the k8s API
    mock_k8s_api = _list_dind_pods_mock()

    build = Build(
        mock.MagicMock(), api=mock_k8s_api, name='test_build',
        namespace='build_namespace', repo_url=mock.MagicMock(),
        ref=mock.MagicMock(), build_image=mock.MagicMock(),
        image_name=mock.MagicMock(), push_secret=mock.MagicMock(),
        memory_limit=mock.MagicMock(), git_credentials=None,
        docker_host='http://mydockerregistry.local',
        node_selector=mock.MagicMock(),
        sticky_builds=True)

    affinity = build.get_affinity()

    assert isinstance(affinity, client.V1Affinity)
    assert affinity.node_affinity is not None
    assert affinity.pod_affinity is None
    assert affinity.pod_anti_affinity is None

    # One of the two nodes we have in our mock should be the preferred node
    assert affinity.node_affinity.preferred_during_scheduling_ignored_during_execution[0].preference.match_expressions[0].values[0] in ("node-a", "node-b")


def test_git_credentials_passed_to_podspec_upon_submit():
    git_credentials = {
        'client_id': 'my_username',
        'access_token': 'my_access_token',
    }

    mock_k8s_api = _list_dind_pods_mock()

    build = Build(
        mock.MagicMock(), api=mock_k8s_api, name='test_build',
        namespace='build_namespace', repo_url=mock.MagicMock(), ref=mock.MagicMock(),
        git_credentials=git_credentials, build_image=mock.MagicMock(),
        image_name=mock.MagicMock(), push_secret=mock.MagicMock(),
        memory_limit=mock.MagicMock(), docker_host='http://mydockerregistry.local',
        node_selector=mock.MagicMock())

    with mock.patch.object(build.stop_event, 'is_set', return_value=True):
        build.submit()

    call_args_list = mock_k8s_api.create_namespaced_pod.call_args_list
    assert len(call_args_list) == 1

    args = call_args_list[0][0]
    pod = args[1]

    assert len(pod.spec.containers) == 1

    env = {
        env_var.name: env_var.value
        for env_var in pod.spec.containers[0].env
    }

    assert env['GIT_CREDENTIAL_ENV'] == git_credentials


async def test_local_repo2docker_build():
    q = Queue()
    repo_url = "https://github.com/binderhub-ci-repos/cached-minimal-dockerfile"
    ref = "HEAD"
    name = str(uuid4())

    build = LocalRepo2dockerBuild(
        q,
        None,
        name,
        namespace=None,
        repo_url=repo_url,
        ref=ref,
        build_image=None,
        docker_host=None,
        image_name=name
    )
    build.submit()

    events = []
    while True:
        event = await q.get(10)
        if event.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE and event.payload == ProgressEvent.BuildStatus.COMPLETED:
            break
        events.append(event)

    # Image should now exist locally
    docker_client = docker.from_env(version='auto')
    assert docker_client.images.get(name)


@pytest.mark.asyncio(timeout=20)
async def test_local_repo2docker_build_stop(event_loop):
    q = Queue()
    # We need a slow build here so that we can interrupt it, so pick a large repo that
    # will take several seconds to clone
    repo_url = "https://github.com/jupyterhub/jupyterhub"
    ref = "HEAD"
    name = str(uuid4())

    build = LocalRepo2dockerBuild(
        q,
        None,
        name,
        namespace=None,
        repo_url=repo_url,
        ref=ref,
        build_image=None,
        docker_host=None,
        image_name=name
    )
    run = event_loop.run_in_executor(None, build.submit)

    # Get first few log messages to check it successfully stared
    event = await q.get()
    assert event.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE
    assert event.payload == ProgressEvent.BuildStatus.RUNNING

    for i in range(2):
        event = await q.get()
        assert event.kind == ProgressEvent.Kind.LOG_MESSAGE
        assert 'message' in event.payload

    build.stop()

    for i in range(10):
        event = await q.get()
        if event.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE and event.payload == ProgressEvent.BuildStatus.FAILED:
            break
    assert event.kind == ProgressEvent.Kind.BUILD_STATUS_CHANGE and event.payload == ProgressEvent.BuildStatus.FAILED

    # Todo: check that process was stopped, and we didn't just return early and leave it in the background

    # Build was stopped so image should not exist locally
    docker_client = docker.from_env(version='auto')
    with pytest.raises(docker.errors.ImageNotFound):
        docker_client.images.get(name)


def test_execute_cmd():
    cmd = ['python', '-c', 'from time import sleep; print(1, flush=True); sleep(2); print(2, flush=True)']
    lines = list(_execute_cmd(cmd, capture=True))
    assert lines == ['1\n', '2\n']

def test_execute_cmd_break():
    cmd = ['python', '-c', 'from time import sleep; print(1, flush=True); sleep(10); print(2, flush=True)']
    lines = []
    now = monotonic()

    def break_callback():
        return monotonic() - now > 2

    # This should break after the first line
    with pytest.raises(ProcessTerminated) as exc:
        for line in _execute_cmd(cmd, capture=True, break_callback=break_callback):
            lines.append(line)
    assert lines == ['1\n']
    assert str(exc.value) == f'ProcessTerminated: {cmd}'
