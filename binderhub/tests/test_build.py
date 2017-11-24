"""Test building repos"""

import json
import sys

import pytest
from tornado.httputil import url_concat

from .utils import async_requests

@pytest.mark.gen_test(timeout=900)
@pytest.mark.parametrize("slug", [
    "gh/binderhub-ci-repos/requirements/d687a7f9e6946ab01ef2baa7bd6d5b73c6e904fd",
])
@pytest.mark.remote
def test_build(app, needs_build, needs_launch, always_build, slug):
    build_url = f"{app.url}/build/{slug}"
    r = yield async_requests.get(build_url, stream=True)
    r.raise_for_status()
    events = []
    for f in async_requests.iter_lines(r):
        # await line Future
        try:
            line = yield f
        except StopIteration:
            break
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
    r = yield async_requests.get(url_concat(final['url'], {'token': final['token']}))
    r.raise_for_status()
    assert r.url.startswith(final['url'])



