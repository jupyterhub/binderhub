"""Base classes for request handlers"""

from http.client import responses
from tornado import web
from jupyterhub.services.auth import HubAuthenticated, HubOAuth
import functools
from urllib.parse import urlencode


def authenticated(method):
    """Copied from tornado.web.authenticated and `auth_enabled` condition is added.
    If authentication in not enabled, this decorator doesn't do anything.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # get_current_user() will be called automatically the first time self.current_user is accessed
        if self.settings['auth_enabled'] and not self.current_user:
            if self.request.method in ("GET", "HEAD"):
                url = self.get_login_url()
                if "?" not in url:
                    # if urlparse.urlsplit(url).scheme:
                    #     # if login url is absolute, make next absolute too
                    #     next_url = self.request.full_url()
                    # else:
                    #     next_url = self.request.uri
                    # always have relative url
                    next_url = self.request.uri
                    url += "?" + urlencode(dict(next=next_url))
                self.redirect(url)
                return
            raise web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper


class BaseHandler(HubAuthenticated, web.RequestHandler):
    """HubAuthenticated by default allows all successfully identified users (see allow_all property)."""

    def initialize(self):
        super().initialize()
        if self.settings['auth_enabled'] and self.settings['use_oauth']:
            self.hub_auth_class = HubOAuth

    @property
    def template_namespace(self):
        return dict(static_url=self.static_url, **self.settings.get('template_variables', {}))

    def set_default_headers(self):
        headers = self.settings.get('headers', {})
        for header, value in headers.items():
            self.set_header(header, value)

    def get_provider(self, provider_prefix, spec):
        """Construct a provider object"""
        providers = self.settings['repo_providers']
        if provider_prefix not in providers:
            raise web.HTTPError(404, "No provider found for prefix %s" % provider_prefix)

        return providers[provider_prefix](
            config=self.settings['traitlets_config'], spec=spec)

    def render_template(self, name, **extra_ns):
        """Render an HTML page"""
        ns = {}
        ns.update(self.template_namespace)
        ns.update(extra_ns)
        template = self.settings['jinja2_env'].get_template(name)
        html = template.render(**ns)
        self.write(html)

    def extract_message(self, exc_info):
        """Return error message from exc_info"""
        exception = exc_info[1]
        # get the custom message, if defined
        try:
            return exception.log_message % exception.args
        except Exception:
            return ''

    def write_error(self, status_code, **kwargs):
        exc_info = kwargs.get('exc_info')
        message = ''
        status_message = responses.get(status_code, 'Unknown HTTP Error')
        if exc_info:
            message = self.extract_message(exc_info)

        self.render_template(
            'error.html',
            status_code=status_code,
            status_message=status_message,
            message=message,
        )

    def options(self, *args, **kwargs):
        pass


class Custom404(BaseHandler):
    """Raise a 404 error, rendering the error.html template"""

    def prepare(self):
        raise web.HTTPError(404)
