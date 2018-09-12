"""Test main handlers"""

from urllib.parse import urlparse

from bs4 import BeautifulSoup
import pytest

from .utils import async_requests


@pytest.mark.parametrize(
    "old_url, new_url", [
        ("/repo/minrk/ligo-binder", "/v2/gh/minrk/ligo-binder/master"),
        ("/repo/minrk/ligo-binder/", "/v2/gh/minrk/ligo-binder/master"),
        (
            "/repo/minrk/ligo-binder/notebooks/index.ipynb",
            "/v2/gh/minrk/ligo-binder/master?urlpath=%2Fnotebooks%2Findex.ipynb",
        ),
    ]
)
@pytest.mark.gen_test
def test_legacy_redirect(app, old_url, new_url):
    r = yield async_requests.get(app.url + old_url, allow_redirects=False)
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


@pytest.mark.gen_test
@pytest.mark.remote
def test_main_page(app):
    """Check the main page and any links on it"""
    r = yield async_requests.get(app.url)
    assert r.status_code == 200
    soup = BeautifulSoup(r.text, 'html5lib')

    # check src links (style, images)
    for el in soup.find_all(src=True):
        url = _resolve_url(app.url, el['src'])
        r = yield async_requests.get(url)
        assert r.status_code == 200, f"{r.status_code} {url}"

    # check hrefs
    for el in soup.find_all(href=True):
        href = el['href']
        if href.startswith('#'):
            continue
        url = _resolve_url(app.url, href)
        r = yield async_requests.get(url)
        assert r.status_code == 200, f"{r.status_code} {url}"


@pytest.mark.parametrize(
    'provider_prefix,repo,ref,path,path_type,status_code',
    [
        ('gh', 'minrk/ligo-binder', 'master', '', '', 200),
        ('gh', 'minrk%2Fligo-binder', 'master', '', '', 400),
        ('gh', 'minrk/ligo-binder', 'master/', '', '', 200),

        ('gh', 'minrk/ligo-binder', 'b8259dac9eb4aa5f2d65d8881f2da94a4952a195', 'index.ipynb', 'file', 200),
        ('gh', 'minrk/ligo-binder', 'b8259dac9eb4aa5f2d65d8881f2da94a4952a195', '%2Fnotebooks%2Findex.ipynb', 'url', 200),

        ('gh', 'berndweiss/gesis-meta-analysis-2018', 'master', 'notebooks', 'file', 200),
        ('gh', 'berndweiss/gesis-meta-analysis-2018', 'master/', '%2Fnotebooks%2F', 'file', 200),
        ('gh', 'berndweiss/gesis-meta-analysis-2018', 'master', '%2Fnotebooks%2F0-0-index.ipynb', 'file', 200),
    ]
)
@pytest.mark.gen_test
def test_loading_page(app, provider_prefix, repo, ref, path, path_type, status_code):
    # repo = f'{user}/{repo_name}'
    spec = f'{repo}/{ref}'
    provider_spec = f'{provider_prefix}/{spec}'
    query = f'{path_type}path={path}' if path else ''
    uri = f'/v2/{provider_spec}?{query}'
    r = yield async_requests.get(app.url + uri)
    assert r.status_code == status_code, f"{r.status_code} {uri}"
    if status_code == 200:
        soup = BeautifulSoup(r.text, 'html5lib')
        assert soup.find(id='log-container')
        nbviewer_url = soup.find(id='nbviewer-preview').find('iframe').attrs['src']
        r = yield async_requests.get(nbviewer_url)
        assert r.status_code == 200, f"{r.status_code} {nbviewer_url}"
