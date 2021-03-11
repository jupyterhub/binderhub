"""Exercise the binderhub entrypoint"""

from subprocess import check_output
import sys
import pytest

from binderhub.app import BinderHub


def test_help():
    check_output([sys.executable, '-m', 'binderhub', '-h'])

def test_help_all():
    check_output([sys.executable, '-m', 'binderhub', '--help-all'])

def test_image_prefix():
    b = BinderHub()

    prefixes = ["foo/bar", "foo-bar/baz", "foo/bar-", "localhost/foo", "localhost/foo/bar/baz",
                "localhost:8080/foo/bar/baz", "127.0.0.1/foo", "127.0.0.1:5000/foo/b",
                "f/o/o/b/a/r/b/a/z", "gcr.io/foo", "my.gcr.io:5000/foo", "foo_bar/baz-",
                "foo_ba.r/baz-", "localhost:32000/someprefix-"]
    for name in prefixes:
        b.image_prefix = name

    wrong_prefixes = ["foo/bar-baz:", "foo/bar-baz:", "foo/bar-baz:10", "foo/bar/", "/foo/bar", 
                      "http://localhost/foo/bar"]
    for name in wrong_prefixes:
        with pytest.raises(AttributeError):
            b.image_prefix = name
