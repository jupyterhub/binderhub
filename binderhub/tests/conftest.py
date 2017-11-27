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

TEST_NAMESPACE = os.environ.get('BINDER_TEST_NAMESPACE') or 'binder-test'
KUBERNETES_AVAILABLE = False

ON_TRAVIS = os.environ.get('TRAVIS')

# set BINDER_TEST_URL to run tests against an already-running binderhub
# this will skip launching BinderHub internally in the app fixture
BINDER_URL = os.environ.get('BINDER_TEST_URL')
REMOTE_BINDER = bool(BINDER_URL)


@pytest.fixture(scope='session')
def _binderhub_config():
    """Load the binderhub configuration

    Currently separate from the app fixture
    so that it can have a different scope (only once per session).
    """
    cfg = PyFileConfigLoader(minikube_testing_config).load_config()
    cfg.BinderHub.build_namespace = TEST_NAMESPACE
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
        # wait for the remote binder to be up
        remaining = 30
        deadline = time.monotonic() + remaining
        success = False
        last_error = None
        while remaining:
            try:
                requests.get(BINDER_URL, timeout=remaining)
            except Exception as e:
                print(f"Waiting for binder: {e}")
                last_error = e
                time.sleep(1)
                remaining = deadline - time.monotonic()
            else:
                success = True
                break
        if not success:
            raise last_error
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
        """Return  list of pods matching given labels"""
        return [
            pod for pod in kube.list_namespaced_pod(namespace).items
            if all(
                pod.metadata.labels.get(key) == value
                for key, value in labels.items()
            )
        ]

    all_pods = pods = get_pods()
    for pod in pods:
        print(f"deleting pod {pod.metadata.name}")
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
        print(f"Waiting for {len(pods)} pods to exit")
        time.sleep(1)
        pods = get_pods()
    if all_pods:
        pod_names = ','.join([pod.metadata.name for pod in all_pods])
        print(f"Deleted {len(all_pods)} pods: {pod_names}")


@pytest.fixture(scope='session')
def cleanup_binder_pods(request):
    """Cleanup running binders.

    Fires at beginning and end of session
    """
    if not KUBERNETES_AVAILABLE:
        # kubernetes not available, nothing to do
        return

    def cleanup():
        return cleanup_pods(TEST_NAMESPACE,
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
            kubernetes.client.V1Namespace(metadata={'name': TEST_NAMESPACE})
        )
    except kubernetes.client.rest.ApiException as e:
        # ignore 409: already exists
        if e.status != 409:
            raise

    def cleanup():
        return cleanup_pods(TEST_NAMESPACE,
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
    # make it long to ensure we run into max build slug length
    session_id = b2a_hex(os.urandom(16)).decode('ascii')

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
