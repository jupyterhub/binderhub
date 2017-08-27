"""
Handler for URL redirection
"""
from tornado import web, gen

from .base import BaseHandler


class RedirectHandler(BaseHandler):
    """Handler for URL redirects."""

    def get(self):
        if self.settings['hub_login_url'] is None:
            raise web.HTTPError(500, "No hub configured!")
        url = self.settings['hub_login_url'] + '?' + self.request.query
        self.redirect(url)
