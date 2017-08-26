"""
Handler for URL redirection
"""
from tornado import web, gen

from .base import BaseHandler


class RedirectHandler(BaseHandler):
    """Handler for URL redirects."""

    def get(self):
        url = self.settings['hub_login_url'] + '?' + self.request.query
        self.redirect(url)
