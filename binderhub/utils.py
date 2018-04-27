from traitlets import Integer, TraitError


class ByteSpecification(Integer):
    """
    Allow easily specifying bytes in units of 1024 with suffixes

    Suffixes allowed are:
      - K -> Kilobyte
      - M -> Megabyte
      - G -> Gigabyte
      - T -> Terabyte

    Stolen from JupyterHub
    """

    UNIT_SUFFIXES = {
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
        'T': 1024 * 1024 * 1024 * 1024,
    }

    # Default to allowing None as a value
    allow_none = True

    def validate(self, obj, value):
        """
        Validate that the passed in value is a valid memory specification

        It could either be a pure int, when it is taken as a byte value.
        If it has one of the suffixes, it is converted into the appropriate
        pure byte value.
        """
        if isinstance(value, (int, float)):
            return int(value)

        try:
            num = float(value[:-1])
        except ValueError:
            raise TraitError('{val} is not a valid memory specification. Must be an int or a string with suffix K, M, G, T'.format(val=value))
        suffix = value[-1]
        if suffix not in self.UNIT_SUFFIXES:
            raise TraitError('{val} is not a valid memory specification. Must be an int or a string with suffix K, M, G, T'.format(val=value))
        else:
            return int(float(num) * self.UNIT_SUFFIXES[suffix])


def url_path_join(*pieces):
    """Join components of url into a relative url.

    Use to prevent double slash when joining subpath. This will leave the
    initial and final / in place.

    Copied from `notebook.utils.url_path_join`.
    """
    initial = pieces[0].startswith('/')
    final = pieces[-1].endswith('/')
    stripped = [ s.strip('/') for s in pieces ]
    result = '/'.join(s for s in stripped if s)

    if initial:
        result = '/' + result
    if final:
        result = result + '/'
    if result == '//':
        result = '/'

    return result


# FIXME: remove when instantiating a kubernetes client
# doesn't create N-CPUs threads unconditionally.
# monkeypatch threadpool in kubernetes api_client
# to avoid instantiating ThreadPools.
# This is known to work for kubernetes-4.0
# and may need updating with later kubernetes clients

from unittest.mock import Mock
from kubernetes.client import api_client

_dummy_pool = Mock()
api_client.ThreadPool = lambda *args, **kwargs: _dummy_pool
