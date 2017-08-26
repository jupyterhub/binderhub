"""Base classes for request handlers"""

from http.client import responses
from tornado import web


class BaseHandler(web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        exc_info = kwargs.get('exc_info')
        message = ''
        exception = None
        status_message = responses.get(status_code, 'Unknown HTTP Error')
        if exc_info:
            exception = exc_info[1]
            # get the custom message, if defined
            try:
                message = exception.log_message % exception.args
            except Exception:
                pass

        self.render(
            'error.html',
            status_code=status_code,
            status_message=status_message,
            message=message,
        )


class Custom404(BaseHandler):
    """Raise a 404 error, rendering the error.html template"""
    def prepare(self):
        raise web.HTTPError(404)
