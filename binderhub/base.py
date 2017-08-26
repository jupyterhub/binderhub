"""Base classes for request handlers"""

from http.client import responses
from tornado import web


class BaseHandler(web.RequestHandler):
    @property
    def template_namespace(self):
        return dict(static_url=self.static_url, )

    def render_template(self, name, **extra_ns):
        ns = {}
        ns.update(self.template_namespace)
        ns.update(extra_ns)
        template = self.settings['jinja2_env'].get_template(name)
        html = template.render(**ns)
        self.write(html)

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

        self.render_template(
            'error.html',
            status_code=status_code,
            status_message=status_message,
            message=message,
        )


class Custom404(BaseHandler):
    """Raise a 404 error, rendering the error.html template"""

    def prepare(self):
        raise web.HTTPError(404)
