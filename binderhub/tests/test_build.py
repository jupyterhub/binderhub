"""Test building repos"""

import json
import sys
from unittest import mock
from urllib.parse import quote

import pytest
from tornado.httputil import url_concat

from binderhub.build import Build
from .utils import async_requests


@pytest.mark.asyncio(timeout=900)
@pytest.mark.parametrize("slug", [
    "gh/binderhub-ci-repos/requirements/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd",
    "git/{}/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd".format(
        quote("https://github.com/binderhub-ci-repos/requirements", safe='')
    ),
    "git/{}/master".format(
        quote("https://github.com/binderhub-ci-repos/requirements", safe='')
    ),
    "gl/minrk%2Fbinderhub-ci/0d4a217d40660efaa58761d8c6084e7cf5453cca",
])
@pytest.mark.remote
async def test_build(app, needs_build, needs_launch, always_build, slug, pytestconfig):
    # can't use mark.github_api since only some tests here use GitHub
    if slug.startswith('gh/') and "not github_api" in pytestconfig.getoption('markexpr'):
        pytest.skip("Skipping GitHub API test")
    build_url = f"{app.url}/build/{slug}"
    r = await async_requests.get(build_url, stream=True)
    r.raise_for_status()
    events = []
    async for line in async_requests.iter_lines(r):
        line = line.decode('utf8', 'replace')
        if line.startswith('data:'):
            event = json.loads(line.split(':', 1)[1])
            events.append(event)
            assert 'message' in event
            sys.stdout.write(event['message'])

    final = events[-1]
    assert 'phase' in final
    assert final['phase'] == 'ready'
    assert 'url' in final
    assert 'token' in final
    print(final['url'])
    r = await async_requests.get(url_concat(final['url'], {'token': final['token']}))
    r.raise_for_status()
    assert r.url.startswith(final['url'])


def test_git_credentials_passed_to_podspec_upon_submit():
    git_credentials = {
        'client_id': 'my_username',
        'access_token': 'my_access_token',
    }
    build = Build(
        mock.MagicMock(), api=mock.MagicMock(), name='test_build',
        namespace='build_namespace', repo_url=mock.MagicMock(), ref=mock.MagicMock(),
        git_credentials=git_credentials, build_image=mock.MagicMock(),
        image_name=mock.MagicMock(), push_secret=mock.MagicMock(),
        memory_limit=mock.MagicMock(), docker_host='http://mydockerregistry.local',
        node_selector=mock.MagicMock())

    with mock.patch.object(build, 'api') as api_patch, \
            mock.patch.object(build.stop_event, 'is_set', return_value=True):
        build.submit()

    call_args_list = api_patch.create_namespaced_pod.call_args_list
    assert len(call_args_list) == 1

    args = call_args_list[0][0]
    pod = args[1]

    assert len(pod.spec.containers) == 1

    env = {
        env_var.name: env_var.value
        for env_var in pod.spec.containers[0].env
    }

    assert env['GIT_CREDENTIAL_ENV'] == git_credentials
