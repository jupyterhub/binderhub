"""pytest fixtures for binderhub"""
import os

import kubernetes.config
import pytest
import requests
from traitlets.config.loader import PyFileConfigLoader

from ..app import BinderHub


here = os.path.abspath(os.path.dirname(__file__))
root = os.path.join(here, os.pardir, os.pardir)
minikube_testing_config = os.path.join(root, 'testing', 'minikube', 'binderhub_config.py')


@pytest.fixture
def app(request, io_loop):
    """Launch the BinderHub app

    Currently reads minikube test config from the repo.
    TODO: support input of test config files.

    Detects whether kubernetes is available, and if not disables build.
    Detects whether jupyterhub is available, and if not disables launch.

    app.url will contain the base URL of binderhub.

    """

    cfg = PyFileConfigLoader(minikube_testing_config).load_config()
    cfg.BinderHub.build_namespace = 'binder-test'
    try:
        kubernetes.config.load_kube_config()
    except Exception:
        cfg.BinderHub.builder_required = False
    # check if Hub is running
    try:
        requests.get(cfg.BinderHub.hub_url)
    except Exception as e:
        # no hub
        cfg.BinderHub.hub_url = ''
    bhub = BinderHub.instance(config=cfg)
    bhub.initialize([])
    bhub.start(run_loop=False)
    def cleanup():
        bhub.stop()
        BinderHub.clear_instance()

    request.addfinalizer(cleanup)
    # convenience for accessing binder in tests
    bhub.url = 'http://127.0.0.1:%i' % bhub.port
    return bhub


@pytest.fixture
def launch(app):
    """Fixture to skip tests if launch is unavailable"""
    if not app.hub_url:
        raise pytest.skip("test requires launcher (jupyterhub)")


@pytest.fixture
def build(app):
    """Fixture to skip tests if build is unavailable"""
    if not app.builder_required:
        raise pytest.skip("test requires builder (kubernetes)")
