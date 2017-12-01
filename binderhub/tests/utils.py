from traitlets import Integer

# async-request utility from jupyterhub.tests.utils v0.8.1
# used under BSD license

from concurrent.futures import ThreadPoolExecutor
import requests

class _AsyncRequests:
    """Wrapper around requests to return a Future from request methods

    A single thread is allocated to avoid blocking the IOLoop thread.
    """
    def __init__(self):
        self.executor = ThreadPoolExecutor(1)

    def __getattr__(self, name):
        requests_method = getattr(requests, name)
        return lambda *args, **kwargs: self.executor.submit(requests_method, *args, **kwargs)

    def iter_lines(self, response):
        """Asynchronously iterate through the lines of a response"""
        it = response.iter_lines()
        while True:
            yield self.executor.submit(lambda : next(it))



# async_requests.get = requests.get returning a Future, etc.
async_requests = _AsyncRequests()


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
