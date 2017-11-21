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

BUILD_NAMESPACE = 'binder-test'
HUB_NAMESPACE = 'binder-test-hub'
KUBERNETES_AVAILABLE = False


@pytest.fixture(scope='session')
def _binderhub_config():
    """separate from app fixture to load config and check for hub only once"""
    cfg = PyFileConfigLoader(minikube_testing_config).load_config()
    cfg.BinderHub.build_namespace = BUILD_NAMESPACE
    global KUBERNETES_AVAILABLE
    try:
        kubernetes.config.load_kube_config()
    except Exception:
        cfg.BinderHub.builder_required = False
        KUBERNETES_AVAILABLE = False
    else:
        KUBERNETES_AVAILABLE = True

    # check if Hub is running and ready
    try:
        requests.get(cfg.BinderHub.hub_url, timeout=5, allow_redirects=False)
    except Exception as e:
        print(f"JupyterHub not available at {cfg.BinderHub.hub_url}: {e}")
        cfg.BinderHub.hub_url = ''
    else:
        print(f"JupyterHub available at {cfg.BinderHub.hub_url}")
    return cfg


@pytest.fixture
def app(request, io_loop, _binderhub_config):
    """Launch the BinderHub app

    Currently reads minikube test config from the repo.
    TODO: support input of test config files.

    Detects whether kubernetes is available, and if not disables build.
    Detects whether jupyterhub is available, and if not disables launch.

    app.url will contain the base URL of binderhub.

    """
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


@pytest.fixture(scope='session')
def cleanup_binder_pods(request):
    """Cleanup running binders.

    Fires at beginning and end of session
    """
    if not KUBERNETES_AVAILABLE:
        # kubernetes not available, nothing to do
        return
    kube = kubernetes.client.CoreV1Api()
    def cleanup():
        pods = kube.list_namespaced_pod(HUB_NAMESPACE).items
        pods = [
            pod for pod in pods
            if pod.metadata.labels.get('component') == 'singleuser-server'
        ]
        for pod in pods:
            print('deleting', pod.metadata.name, pod.metadata.labels)
            try:
                kube.delete_namespaced_pod(
                    pod.metadata.name,
                    HUB_NAMESPACE,
                    kubernetes.client.V1DeleteOptions(grace_period_seconds=0),
                )
            except kubernetes.client.rest.ApiException as e:
                # ignore 404, 409: already gone
                if e.status not in (404, 409):
                    raise
        while pods:
            print(f"Waiting for {len(pods)} binder pods to exit")
            time.sleep(1)

            pods = kube.list_namespaced_pod(HUB_NAMESPACE).items
            pods = [
                pod for pod in pods
                if pod.metadata.labels.get('component') == 'singleuser-server'
            ]
    cleanup()
    request.addfinalizer(cleanup)


@pytest.fixture
def needs_launch(app, cleanup_binder_pods):
    """Fixture to skip tests if launch is unavailable"""
    if not app.hub_url:
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

    def cleanup():
        pods = kube.list_namespaced_pod(BUILD_NAMESPACE).items
        for pod in pods:
            print('deleting', pod.metadata.name, pod.metadata.labels)
            try:
                kube.delete_namespaced_pod(
                    pod.metadata.name,
                    BUILD_NAMESPACE,
                    kubernetes.client.V1DeleteOptions(grace_period_seconds=0),
                )
            except kubernetes.client.rest.ApiException as e:
                # ignore 404, 409: already gone
                if e.status not in (404, 409):
                    raise
        while pods:
            print(f"Waiting for {len(pods)} build pods to exit")
            time.sleep(1)
            pods = kube.list_namespaced_pod(BUILD_NAMESPACE).items
    cleanup()
    request.addfinalizer(cleanup)


@pytest.fixture
def needs_build(app, cleanup_build_pods):
    """Fixture to skip tests if build is unavailable"""
    if not app.builder_required:
        raise pytest.skip("test requires builder (kubernetes)")


@pytest.fixture
def always_build(app, request):
    """Fixture to ensure checks for cached build return False

    by giving the build slug a random prefix
    """
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
