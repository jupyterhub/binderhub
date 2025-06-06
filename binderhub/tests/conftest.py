"""pytest fixtures for binderhub"""

import inspect
import json
import os
import secrets
import subprocess
import time
from collections import defaultdict
from unittest import mock
from urllib.parse import urlparse

import kubernetes.client
import kubernetes.config
import pytest
import requests
from tornado.httpclient import AsyncHTTPClient
from tornado.platform.asyncio import AsyncIOMainLoop
from traitlets.config import Config
from traitlets.config.loader import PyFileConfigLoader

from ..app import BinderHub
from .utils import MockAsyncHTTPClient

here = os.path.abspath(os.path.dirname(__file__))
root = os.path.join(here, os.pardir, os.pardir)
binderhub_config_path = os.path.join(
    root, "testing/local-binder-k8s-hub/binderhub_config.py"
)
binderhub_config_auth_additions_path = os.path.join(
    root, "testing/local-binder-k8s-hub/binderhub_config_auth_additions.py"
)

# These are automatically determined
K8S_AVAILABLE = False
K8S_NAMESPACE = None

# set BINDER_URL to run tests against an already-running binderhub
# this will skip launching BinderHub internally in the app fixture
BINDER_URL = os.environ.get("BINDER_URL")
REMOTE_BINDER = bool(BINDER_URL)


def pytest_configure(config):
    """
    Configure plugins and custom markers

    This function is called by pytest after command line arguments have
    been parsed. See https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_configure
    for more information.
    """
    # register our custom markers
    config.addinivalue_line(
        "markers", "auth: mark test to run only on auth environments"
    )
    config.addinivalue_line(
        "markers", "github_api: mark test to run only with GitHub API credentials"
    )
    config.addinivalue_line(
        "markers", "remote: mark test for when BinderHub is already running somewhere."
    )
    config.addinivalue_line(
        "markers",
        "helm: mark test to only run when BinderHub is launched with our k8s-binderhub test config.",
    )


def pytest_runtest_setup(item):
    is_helm_test = any(mark for mark in item.iter_markers(name="helm"))
    if not item.config.getoption("--helm"):
        if is_helm_test:
            pytest.skip("Skipping test marked as 'helm'")


def pytest_terminal_summary(terminalreporter, exitstatus):
    """This function has meaning to pytest, for more information, see:
    https://docs.pytest.org/en/stable/reference.html#pytest.hookspec.pytest_terminal_summary
    """
    if not MockAsyncHTTPClient.records:
        return
    hosts = defaultdict(dict)
    # group records by host
    for url, response in MockAsyncHTTPClient.records.items():
        host = urlparse(url).hostname
        hosts[host][url] = response
    # save records to files
    for host, records in hosts.items():
        fname = f"http-record.{host}.json"
        print(f"Recorded http responses for {host} in {fname}")
        print(
            "To update the recordings used by the tests you will have"
            " to move or merge the newly created recordings with existing"
            f" recordings in {here}."
        )

        # Always store newly created recordings in the root directory
        # and ask a human to decide if they want to overwrite or merge
        # them with existing recordings
        with open(os.path.join(root, fname), "w") as f:
            json.dump(records, f, sort_keys=True, indent=1)


def load_mock_responses(file_name):
    file_path = os.path.join(here, file_name)
    with open(file_path) as f:
        records = json.load(f)
    MockAsyncHTTPClient.mocks.update(records)


def pytest_collection_modifyitems(items):
    """add asyncio marker to all async tests"""
    for item in items:
        if inspect.iscoroutinefunction(item.obj):
            item.add_marker("asyncio")


@pytest.fixture(autouse=True, scope="session")
def mock_asynchttpclient(request):
    """mock AsyncHTTPClient for recording responses"""
    AsyncHTTPClient.configure(MockAsyncHTTPClient)

    # We have to explicitly load the mock responses we want to use
    # We should use as few mocked responses as possible because it means
    # we won't notice changes in the responses from the host that we are
    # mocking and our mock responses don't simulate every and all behavior
    load_mock_responses("http-record.www.hydroshare.org.json")

    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        load_mock_responses("http-record.api.github.com.json")
        load_mock_responses("http-record.zenodo.org.json")
    if token and token.startswith("ghs_"):
        # The GitHub Actions provided temporary token (secrets.github_token)
        # does not have access to api.github.com/gists. Due to this, we mock
        # such requests even if such token is provided. We recognize them by
        # being a server-to-server token with a ghs_ prefix as compared to for
        # example a personal access token.
        #
        # More about github token prefixes:
        # https://github.blog/2021-04-05-behind-githubs-new-authentication-token-formats/#identifiable-prefixes
        #
        load_mock_responses("http-record.api.github.com.gists.json")


@pytest.fixture
async def io_loop(event_loop, request):
    """Same as pytest-tornado.io_loop, but runs with pytest-asyncio"""
    io_loop = AsyncIOMainLoop()
    assert io_loop.asyncio_loop is event_loop

    def _close():
        io_loop.close(all_fds=True)

    request.addfinalizer(_close)
    return io_loop


@pytest.fixture(scope="session")
def _binderhub_config():
    """Load the binderhub configuration

    Currently separate from the app fixture
    so that it can have a different scope (only once per session).
    """
    cfg = PyFileConfigLoader(binderhub_config_path).load_config()
    global K8S_AVAILABLE
    global K8S_NAMESPACE
    try:
        kubernetes.config.load_kube_config()
    except Exception:
        cfg.BinderHub.builder_required = False
        K8S_AVAILABLE = False
        K8S_NAMESPACE = None
    else:
        K8S_AVAILABLE = True
        # get the current context's namespace or assume it is "default"
        K8S_NAMESPACE = (
            subprocess.check_output(
                [
                    "kubectl",
                    "config",
                    "view",
                    "--minify",
                    "--output",
                    "jsonpath={..namespace}",
                ],
                text=True,
            ).strip()
            or "default"
        )

    if REMOTE_BINDER:
        return

    # check if Hub is running and ready
    try:
        requests.get(cfg.BinderHub.hub_url, timeout=5, allow_redirects=False)
    except Exception as e:
        print(f"JupyterHub not available at {cfg.BinderHub.hub_url}: {e}")
        cfg.BinderHub.hub_url = ""
    else:
        print(f"JupyterHub available at {cfg.BinderHub.hub_url}")
    return cfg


class RemoteBinderHub:
    """Mock class for the app fixture when Binder is remote

    Has a URL for the binder location and a configured BinderHub instance
    so tests can look at the configuration of the hub.

    Note: this only gives back the default configuration. It could be that the
    remote hub is configured differently than what you see here. In our CI
    setup this will do the right thing though.
    """

    url = None
    _configured_bhub = None

    def __getattr__(self, name):
        return getattr(self._configured_bhub, name)


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
        app._configured_bhub = BinderHub(config=_binderhub_config)
        return app

    api_only_app = False
    if hasattr(request, "param"):
        if request.param == "app_with_auth_config":
            # load conf for auth test
            cfg = PyFileConfigLoader(binderhub_config_auth_additions_path).load_config()
            _binderhub_config.merge(cfg)
        elif request.param == "api_only_app":
            # load conf that sets BinderHub.enable_api_only_mode = True
            cfg = Config({"BinderHub": {"enable_api_only_mode": True}})
            _binderhub_config.merge(cfg)
            api_only_app = True

    if not api_only_app:
        # load conf that sets BinderHub.require_build_only = False
        # otherwise because _binderhub_config has a session scope,
        # any previous set of require_build_only to True will stick around
        cfg = Config({"BinderHub": {"enable_api_only_mode": False}})
        _binderhub_config.merge(cfg)

    bhub = BinderHub.instance(config=_binderhub_config)
    bhub.initialize([])
    bhub.start(run_loop=False)
    # instantiating binderhub configures this
    # override again
    AsyncHTTPClient.configure(MockAsyncHTTPClient)

    def cleanup():
        bhub.stop()
        BinderHub.clear_instance()

    request.addfinalizer(cleanup)
    # convenience for accessing binder in tests
    bhub.url = f"http://127.0.0.1:{bhub.port}{bhub.base_url}".rstrip("/")
    return bhub


def cleanup_pods(labels):
    """Cleanup pods in current namespace that match the given labels"""
    kube = kubernetes.client.CoreV1Api()

    def get_pods():
        """Return list of pods matching given labels"""
        return [
            pod
            for pod in kube.list_namespaced_pod(namespace=K8S_NAMESPACE).items
            if all(
                pod.metadata.labels.get(key) == value for key, value in labels.items()
            )
        ]

    all_pods = pods = get_pods()
    for pod in pods:
        print(f"deleting pod {pod.metadata.name}")
        try:
            kube.delete_namespaced_pod(
                namespace=K8S_NAMESPACE,
                name=pod.metadata.name,
                body=kubernetes.client.V1DeleteOptions(grace_period_seconds=0),
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
        pod_names = ",".join([pod.metadata.name for pod in all_pods])
        print(f"Deleted {len(all_pods)} pods: {pod_names}")


@pytest.fixture(scope="session")
def cleanup_binder_pods(request):
    """Cleanup running user sessions at the beginning and end of a session."""
    if not K8S_AVAILABLE:
        return

    def cleanup():
        return cleanup_pods({"component": "singleuser-server"})

    cleanup()
    request.addfinalizer(cleanup)


@pytest.fixture(scope="session")
def cleanup_build_pods(request):
    """Cleanup running build pods at the beginning and end of a session."""
    if not K8S_AVAILABLE:
        return

    def cleanup():
        return cleanup_pods({"component": "binderhub-build"})

    cleanup()
    request.addfinalizer(cleanup)


@pytest.fixture
def needs_launch(app, cleanup_binder_pods):
    """Fixture to skip tests if launch is unavailable"""
    if not BINDER_URL and not app.hub_url:
        raise pytest.skip("test requires launcher (jupyterhub)")


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
    session_id = secrets.token_hex(16)

    def patch_provider(Provider):
        original_slug = Provider.get_build_slug

        def patched_slug(self):
            slug = original_slug(self)
            return f"test-{session_id}-{slug}"

        return mock.patch.object(Provider, "get_build_slug", patched_slug)

    for Provider in app.repo_providers.values():
        patch = patch_provider(Provider)
        patch.start()
        request.addfinalizer(patch.stop)


# skip_remote mark for tests that require local binder
# e.g. patching config
skip_remote = pytest.mark.skipif(REMOTE_BINDER, reason="requires local binder")
