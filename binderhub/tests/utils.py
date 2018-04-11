
import io
import pprint

from tornado.httpclient import HTTPRequest, HTTPResponse, AsyncHTTPClient


class MockAsyncHTTPClient(AsyncHTTPClient.configurable_default()):
    mocks = {}
    records = {}

    def fetch_mock(self, req):
        mock_data = self.mocks[req.url]
        response = HTTPResponse(req, mock_data.get('code', 200))
        response.buffer = io.BytesIO(mock_data['body'].encode('utf8'))
        return response

    async def fetch(self, req_or_url, *args, **kwargs):
        if isinstance(req_or_url, HTTPRequest):
            req = req_or_url
        else:
            req = HTTPRequest(req_or_url, *args, **kwargs)

        if req.url in self.mocks:
            return self.fetch_mock(req)
        else:
            resp = await super().fetch(req)
            # record the response
            self.records[req.url] = {
                'code': resp.code,
                'body': resp.body.decode('utf8'),
            }
            return resp


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
