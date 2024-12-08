"""Test version handler"""

import pytest

from binderhub import __version__ as binder_version

from .utils import async_requests


@pytest.mark.remote
async def test_versions_handler(app):
    # Check that the about page loads
    r = await async_requests.get(app.url + "/versions")
    assert r.status_code == 200

    data = r.json()
    # builder_info is different for KubernetesExecutor and LocalRepo2dockerBuild
    try:
        import repo2docker

        allowed_builder_info = [{"repo2docker-version": repo2docker.__version__}]
    except ImportError:
        allowed_builder_info = []
    allowed_builder_info.append({"build_image": app.build_image})

    assert data["builder_info"] in allowed_builder_info
    assert data["binderhub"].split("+")[0] == binder_version.split("+")[0]
