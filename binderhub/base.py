"""Base classes for request handlers"""

import json

from http.client import responses
from tornado.escape import url_escape, url_unescape
from tornado import web


class BaseHandler(web.RequestHandler):
    @property
    def template_namespace(self):
        return dict(static_url=self.static_url)

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

    def _normalize_cookie(self, cookie):
        """
        Make sure the json cookie is normalized to have a know schema:
        {
            'known': [list of unique strings]
            'default': [string found in known section]
        }

        We could (should ?) be stricter.

        """

        portal_address = self.settings['cannonical_address']
        default_binders = self.settings['default_binders']
        new_cookie = {}
        if self.settings['enable_federation_sites_cookie']:
            cookie_listed = cookie.get('known', [portal_address])
        else:
            cookie_listed = []
        new_cookie['known'] = list(sorted(set( cookie_listed + [portal_address] + default_binders)))
        default = cookie.get('default', portal_address)
        if default not in new_cookie['known']:
            default = portal_address

        new_cookie['default'] = default
        return new_cookie

    def set_json_cookie(self, name, value, *args, **kwargs):
        self.set_secure_cookie(name, url_escape(json.dumps(value)), *args, **kwargs)

    def get_json_cookie(self, name, *args, **kwargs):
        cookie = self.get_secure_cookie(name, *args, **kwargs)
        if not cookie:
            return self._normalize_cookie({})
        return self._normalize_cookie(json.loads(url_unescape(cookie)))




class Custom404(BaseHandler):
    """Raise a 404 error, rendering the error.html template"""

    def prepare(self):
        raise web.HTTPError(404)
