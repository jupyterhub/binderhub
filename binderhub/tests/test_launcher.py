"""Test launcher"""

import pytest

from binderhub.launcher import Launcher
from tornado import web


async def my_pre_launch_hook(launcher, *args):
    raise web.HTTPError(400, 'Launch is not possible with parameters: ' + ','.join(args))


async def test_pre_launch_hook():
    launcher = Launcher(create_user=False, pre_launch_hook=my_pre_launch_hook)
    parameters = ['image', 'test_user', 'test_server', 'repo_url']
    with pytest.raises(web.HTTPError) as excinfo:
        _ = await launcher.launch(*parameters)
    assert excinfo.value.status_code == 400
    message = excinfo.value.log_message
    assert parameters == message.split(':', 1)[-1].lstrip().split(',')
