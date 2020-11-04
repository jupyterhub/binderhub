"""Test main handlers"""

from urllib.parse import urlparse

from bs4 import BeautifulSoup
import pytest

from binderhub import __version__ as binder_version

from .utils import async_requests


@pytest.mark.parametrize(
    "old_url, new_url", [
        ("/repo/binderhub-ci-repos/requirements", "/v2/gh/binderhub-ci-repos/requirements/master"),
        ("/repo/binderhub-ci-repos/requirements/", "/v2/gh/binderhub-ci-repos/requirements/master"),
        (
            "/repo/binderhub-ci-repos/requirements/notebooks/index.ipynb",
            "/v2/gh/binderhub-ci-repos/requirements/master?urlpath=%2Fnotebooks%2Findex.ipynb",
        ),
    ]
)
async def test_legacy_redirect(app, old_url, new_url):
    r = await async_requests.get(app.url + old_url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers['location'] == new_url


def _resolve_url(page_url, url):
    """Resolve a URL relative to a page"""

    # full URL, nothing to resolve
    if '://' in url:
        return url

    parsed = urlparse(page_url)

    if url.startswith('/'):
        # absolute path
        return f"{parsed.scheme}://{parsed.netloc}{url}"

    # relative path URL

    if page_url.endswith('/'):
        # URL is a directory, resolve relative to dir
        path = parsed.path
    else:
        # URL is not a directory, resolve relative to parent
        path = parsed.path.rsplit('/', 1)[0] + '/'

    return f"{parsed.scheme}://{parsed.netloc}{path}{url}"


@pytest.mark.remote
async def test_main_page(app):
    """Check the main page and any links on it"""
    r = await async_requests.get(app.url)
    assert r.status_code == 200
    soup = BeautifulSoup(r.text, 'html5lib')

    # check src links (style, images)
    for el in soup.find_all(src=True):
        url = _resolve_url(app.url, el['src'])
        r = await async_requests.get(url)
        assert r.status_code == 200, f"{r.status_code} {url}"

    # check hrefs
    for el in soup.find_all(href=True):
        href = el['href']
        if href.startswith('#'):
            continue
        url = _resolve_url(app.url, href)
        r = await async_requests.get(url)
        assert r.status_code == 200, f"{r.status_code} {url}"


@pytest.mark.remote
async def test_about_handler(app):
    # Check that the about page loads
    r = await async_requests.get(app.url + "/about")
    assert r.status_code == 200
    assert "This website is powered by" in r.text
    assert binder_version.split("+")[0] in r.text


@pytest.mark.remote
async def test_versions_handler(app):
    # Check that the about page loads
    r = await async_requests.get(app.url + "/versions")
    assert r.status_code == 200

    data = r.json()
    assert data['builder'] == app.build_image
    assert data['binderhub'].split("+")[0] == binder_version.split("+")[0]


@pytest.mark.parametrize(
    'provider_prefix,repo,ref,path,path_type,status_code',
    [
        ('gh', 'binderhub-ci-repos/requirements', 'master', '', '', 200),
        ('gh', 'binderhub-ci-repos%2Frequirements', 'master', '', '', 400),
        ('gh', 'binderhub-ci-repos/requirements', 'master/', '', '', 200),

        ('gh', 'binderhub-ci-repos/requirements', '20c4fe55a9b2c5011d228545e821b1c7b1723652', 'index.ipynb', 'file', 200),
        ('gh', 'binderhub-ci-repos/requirements', '20c4fe55a9b2c5011d228545e821b1c7b1723652', '%2Fnotebooks%2Findex.ipynb', 'url', 200),

        ('gh', 'binderhub-ci-repos/requirements', 'master', 'has%20space', 'file', 200),
        ('gh', 'binderhub-ci-repos/requirements', 'master/', '%2Fhas%20space%2F', 'file', 200),
        ('gh', 'binderhub-ci-repos/requirements', 'master', '%2Fhas%20space%2F%C3%BCnicode.ipynb', 'file', 200),
    ]
)
async def test_loading_page(app, provider_prefix, repo, ref, path, path_type, status_code):
    # repo = f'{org}/{repo_name}'
    spec = f'{repo}/{ref}'
    provider_spec = f'{provider_prefix}/{spec}'
    query = f'{path_type}path={path}' if path else ''
    uri = f'/v2/{provider_spec}?{query}'
    r = await async_requests.get(app.url + uri)
    assert r.status_code == status_code, f"{r.status_code} {uri}"
    if status_code == 200:
        soup = BeautifulSoup(r.text, 'html5lib')
        assert soup.find(id='log-container')
        nbviewer_url = soup.find(id='nbviewer-preview').find('iframe').attrs['src']
        r = await async_requests.get(nbviewer_url)
        assert r.status_code == 200, f"{r.status_code} {nbviewer_url}"
