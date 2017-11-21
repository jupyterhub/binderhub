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


@pytest.mark.gen_test
def test_parametrized_page(app):
    sha = 'b8259dac9eb4aa5f2d65d8881f2da94a4952a195'
    r = yield async_requests.get(app.url + f'/v2/gh/minrk/ligo-binder/{sha}?filepath=index.ipynb')
    assert r.status_code == 200
    soup = BeautifulSoup(r.text, 'html5lib')
    assert soup.find(id='repository')['value'] == 'https://github.com/minrk/ligo-binder'
    assert soup.find(id='ref')['value'] == sha
    assert soup.find(id='filepath')['value'] == 'index.ipynb'
