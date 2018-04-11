"""Testing utilities"""
import io

from tornado.httputil import HTTPHeaders
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest, HTTPResponse


class MockAsyncHTTPClient(AsyncHTTPClient.configurable_default()):
    mocks = {}
    records = {}

    def url_key(self, url):
        """cache key is url without query

        to avoid caching things like access tokens
        """
        return url.split('?')[0]


    def fetch_mock(self, req):
        mock_data = self.mocks[self.url_key(req.url)]
        code = mock_data.get('code', 200)
        headers = HTTPHeaders(mock_data.get('headers', {}))
        response = HTTPResponse(req, code, headers=headers)
        response.buffer = io.BytesIO(mock_data['body'].encode('utf8'))
        if code >= 400:
            raise HTTPError(mock_data['code'], response=response)

        return response

    async def fetch(self, req_or_url, *args, **kwargs):
        if isinstance(req_or_url, HTTPRequest):
            req = req_or_url
        else:
            req = HTTPRequest(req_or_url, *args, **kwargs)

        if self.url_key(req.url) in self.mocks:
            return self.fetch_mock(req)
        else:
            error = None
            try:
                resp = await super().fetch(req)
            except HTTPError as e:
                error = e
                resp = e.response

            # record the response
            self.records[self.url_key(req.url)] = {
                'code': resp.code,
                'headers': dict(resp.headers),
                'body': resp.body.decode('utf8'),
            }
            # return or raise the original result
            if error:
                raise error
            else:
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
