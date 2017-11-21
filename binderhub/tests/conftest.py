"""pytest fixtures for binderhub"""

from binascii import b2a_hex
import os
import time
from unittest import mock

import kubernetes.client
import kubernetes.config
import pytest
import requests
from traitlets.config.loader import PyFileConfigLoader

from ..app import BinderHub


here = os.path.abspath(os.path.dirname(__file__))
root = os.path.join(here, os.pardir, os.pardir)
minikube_testing_config = os.path.join(root, 'testing', 'minikube', 'binderhub_config.py')

BUILD_NAMESPACE = os.environ.get('BINDER_TEST_BUILD_NAMESPACE') or 'binder-test'
HUB_NAMESPACE = os.environ.get('BINDER_TEST_HUB_NAMESPACE')or 'binder-test-hub'
KUBERNETES_AVAILABLE = False

ON_TRAVIS = os.environ.get('TRAVIS')

BINDER_URL = os.environ.get('BINDER_TEST_URL')
REMOTE_BINDER = bool(BINDER_URL)


@pytest.fixture(scope='session')
def _binderhub_config():
    """separate from app fixture to load config and check for hub only once"""
    cfg = PyFileConfigLoader(minikube_testing_config).load_config()
    cfg.BinderHub.build_namespace = BUILD_NAMESPACE
    if ON_TRAVIS:
        cfg.BinderHub.hub_url = cfg.BinderHub.hub_url.replace('192.168.99.100', '127.0.0.1')
    global KUBERNETES_AVAILABLE
    try:
        kubernetes.config.load_kube_config()
    except Exception:
        cfg.BinderHub.builder_required = False
        KUBERNETES_AVAILABLE = False
        if ON_TRAVIS:
            pytest.fail("Kubernetes should be available on Travis")
    else:
        KUBERNETES_AVAILABLE = True
    if REMOTE_BINDER:
        return

    # check if Hub is running and ready
    try:
        requests.get(cfg.BinderHub.hub_url, timeout=5, allow_redirects=False)
    except Exception as e:
        print(f"JupyterHub not available at {cfg.BinderHub.hub_url}: {e}")
        if ON_TRAVIS:
            pytest.fail("JupyterHub should be available on Travis")
        cfg.BinderHub.hub_url = ''
    else:
        print(f"JupyterHub available at {cfg.BinderHub.hub_url}")
    return cfg


class RemoteBinderHub(object):
    """Mock class for the app fixture when Binder is remote

    Only has a URL for the binder location.
    """
    url = None


@pytest.fixture
def app(request, io_loop, _binderhub_config):
    """Launch the BinderHub app

    Currently reads minikube test config from the repo.
    TODO: support input of test config files.

    Detects whether kubernetes is available, and if not disables build.
    Detects whether jupyterhub is available, and if not disables launch.

    app.url will contain the base URL of binderhub.
    """
    if REMOTE_BINDER:
        app = RemoteBinderHub()
        app.url = BINDER_URL
        return app

    bhub = BinderHub.instance(config=_binderhub_config)
    bhub.initialize([])
    bhub.start(run_loop=False)
    def cleanup():
        bhub.stop()
        BinderHub.clear_instance()

    request.addfinalizer(cleanup)
    # convenience for accessing binder in tests
    bhub.url = 'http://127.0.0.1:%i' % bhub.port
    return bhub

def cleanup_pods(namespace, labels):
    """Cleanup pods in a namespace that match the given labels"""
    kube = kubernetes.client.CoreV1Api()
    def get_pods():
        return [
            pod for pod in kube.list_namespaced_pod(namespace).items
            if all(
                pod.metadata.labels.get(key) == value
                for key, value in labels.items()
            )
        ]
    pods = get_pods()
    for pod in pods:
        print('deleting', pod.metadata.name, pod.metadata.labels)
        try:
            kube.delete_namespaced_pod(
                pod.metadata.name,
                namespace,
                kubernetes.client.V1DeleteOptions(grace_period_seconds=0),
            )
        except kubernetes.client.rest.ApiException as e:
            # ignore 404, 409: already gone
            if e.status not in (404, 409):
                raise
    while pods:
        print(f"Waiting for {len(pods)} binder pods to exit")
        time.sleep(1)
        pods = get_pods()


@pytest.fixture(scope='session')
def cleanup_binder_pods(request):
    """Cleanup running binders.

    Fires at beginning and end of session
    """
    if not KUBERNETES_AVAILABLE:
        # kubernetes not available, nothing to do
        return
    cleanup = lambda : cleanup_pods(HUB_NAMESPACE,
                                    {'component': 'singleuser-server'})
    cleanup()
    request.addfinalizer(cleanup)


@pytest.fixture
def needs_launch(app, cleanup_binder_pods):
    """Fixture to skip tests if launch is unavailable"""
    if not BINDER_URL and not app.hub_url:
        raise pytest.skip("test requires launcher (jupyterhub)")


@pytest.fixture(scope='session')
def cleanup_build_pods(request):
    if not KUBERNETES_AVAILABLE:
        # kubernetes not available, nothing to do
        return
    kube = kubernetes.client.CoreV1Api()
    try:
        kube.create_namespace(
            kubernetes.client.V1Namespace(metadata={'name': BUILD_NAMESPACE})
        )
    except kubernetes.client.rest.ApiException as e:
        # ignore 409: already exists
        if e.status != 409:
            raise

    cleanup = lambda : cleanup_pods(BUILD_NAMESPACE,
                                    {'component': 'binderhub-build'})
    cleanup()
    request.addfinalizer(cleanup)


@pytest.fixture
def needs_build(app, cleanup_build_pods):
    """Fixture to skip tests if build is unavailable"""
    if not BINDER_URL and not app.builder_required:
        raise pytest.skip("test requires builder (kubernetes)")


@pytest.fixture
def always_build(app, request):
    """Fixture to ensure checks for cached build return False

    by giving the build slug a random prefix
    """
    if REMOTE_BINDER:
        return
    session_id = b2a_hex(os.urandom(5)).decode('ascii')
    def patch_provider(Provider):
        original_slug = Provider.get_build_slug
        def patched_slug(self):
            slug = original_slug(self)
            return f"test-{session_id}-{slug}"
        return mock.patch.object(Provider, 'get_build_slug', patched_slug)

    for Provider in app.repo_providers.values():
        patch = patch_provider(Provider)
        patch.start()
        request.addfinalizer(patch.stop)
