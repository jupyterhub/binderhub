"""
Integration tests using playwright
"""

import asyncio
import subprocess
import sys

import pytest
import requests
import requests.exceptions
from playwright.sync_api import Page

from binderhub import __version__ as binder_version
from binderhub.tests.utils import async_requests, random_port


@pytest.fixture(scope="module")
async def local_hub_local_binder(request):
    """
    Set up a local docker based binder based on testing/local-binder-local-hub

    Requires docker to be installed and available
    """
    port = random_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "jupyterhub",
            "--config",
            "testing/local-binder-local-hub/jupyterhub_config.py",
            f"--port={port}",
        ]
    )

    url = f"http://127.0.0.1:{port}/services/binder/"
    for i in range(60):
        await asyncio.sleep(1)
        try:
            resp = await async_requests.get(url)
            if resp.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
    else:
        raise RuntimeError("BinderHub server did NOT start in 60 seconds!")
    yield url

    proc.terminate()
    proc.wait()


@pytest.mark.parametrize(
    ("provider_prefix", "repo", "ref", "path", "path_type", "status_code"),
    [
        ("gh", "binderhub-ci-repos/requirements", "master", "", "", 200),
        ("gh", "binderhub-ci-repos/requirements", "master/", "", "", 200),
        (
            "gh",
            "binderhub-ci-repos/requirements",
            "20c4fe55a9b2c5011d228545e821b1c7b1723652",
            "index.ipynb",
            "file",
            200,
        ),
        (
            "gh",
            "binderhub-ci-repos/requirements",
            "20c4fe55a9b2c5011d228545e821b1c7b1723652",
            "%2Fnotebooks%2Findex.ipynb",
            "url",
            200,
        ),
        ("gh", "binderhub-ci-repos/requirements", "master", "has%20space", "file", 200),
        (
            "gh",
            "binderhub-ci-repos/requirements",
            "master/",
            "%2Fhas%20space%2F",
            "file",
            200,
        ),
        (
            "gh",
            "binderhub-ci-repos/requirements",
            "master",
            "%2Fhas%20space%2F%C3%BCnicode.ipynb",
            "file",
            200,
        ),
    ],
)
async def test_loading_page(
    local_hub_local_binder,
    provider_prefix,
    repo,
    ref,
    path,
    path_type,
    status_code,
    page: Page,
):
    spec = f"{repo}/{ref}"
    provider_spec = f"{provider_prefix}/{spec}"
    query = f"{path_type}path={path}" if path else ""
    uri = f"{local_hub_local_binder}v2/{provider_spec}?{query}"
    r = page.goto(uri)
    assert r.status == status_code, f"{r.status} {uri}"
    if status_code == 200:
        nbviewer_url = page.get_by_test_id("nbviewer-iframe").get_attribute("src")
        expected_url = (
            f"https://nbviewer.jupyter.org/github/{repo}/tree/{ref.replace('/', '')}"
        )
        assert nbviewer_url == expected_url


@pytest.mark.parametrize(
    ("repo", "ref", "path", "path_type", "shared_url"),
    [
        (
            "binder-examples/requirements",
            "",
            "",
            "",
            "v2/gh/binder-examples/requirements/HEAD",
        ),
        (
            "binder-examples/requirements",
            "master",
            "",
            "",
            "v2/gh/binder-examples/requirements/master",
        ),
        (
            "binder-examples/requirements",
            "master",
            "some file with spaces.ipynb",
            "file",
            "v2/gh/binder-examples/requirements/master?urlpath=%2Fdoc%2Ftree%2Fsome+file+with+spaces.ipynb",
        ),
        (
            "binder-examples/requirements",
            "master",
            "/some url with spaces?query=something",
            "url",
            "v2/gh/binder-examples/requirements/master?urlpath=%2Fsome+url+with+spaces%3Fquery%3Dsomething",
        ),
    ],
)
async def test_main_page(
    local_hub_local_binder, page: Page, repo, ref, path, path_type, shared_url
):
    resp = page.goto(local_hub_local_binder)
    assert resp.status == 200

    page.locator("[name='repository']").type(repo)

    if ref:
        page.locator("[name='ref']").type(ref)

    if path_type:
        page.get_by_role("button", name="File").click()
        if path_type == "file":
            pass
        elif path_type == "url":
            page.get_by_role("button", name="URL").click()
        else:
            raise ValueError(f"Unknown path_type {path_type}")
    if path:
        page.locator("[name='path']").type(path)

    assert (
        page.get_by_test_id("launch-url").inner_text()
        == f"{local_hub_local_binder}{shared_url}"
    )


async def test_about_page(local_hub_local_binder, page: Page):
    r = page.goto(f"{local_hub_local_binder}about")

    assert r.status == 200

    assert "This website is powered by" in page.content()
    assert binder_version.split("+")[0] in page.content()
