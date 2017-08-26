"""
Main handler classes for requests
"""
from tornado import web

from .base import BaseHandler


class MainHandler(BaseHandler):
    """Main handler for requests"""

    def get(self):
        self.render_template(
            "index.html",
            url=None,
            ref='master',
            filepath=None,
            submit=False,
            google_analytics_code=self.settings['google_analytics_code']
        )


class ParameterizedMainHandler(BaseHandler):
    """Main handler that allows different parameter settings"""

    def get(self, provider_prefix, spec):
        providers = self.settings['repo_providers']
        if provider_prefix not in self.settings['repo_providers']:
            raise web.HTTPError(404, "No provider found for prefix %s" % provider_prefix)
        provider = self.settings['repo_providers'][provider_prefix](config=self.settings['traitlets_config'], spec=spec)

        self.render_template(
            "index.html",
            url=provider.get_repo_url(),
            ref=provider.unresolved_ref,
            filepath=self.get_argument('filepath', None),
            submit=True,
            google_analytics_code=self.settings['google_analytics_code']
        )


class LegacyRedirectHandler(BaseHandler):
    """Redirect handler from legacy Binder"""

    def get(self, user, repo):
        url = '/v2/gh/{user}/{repo}/master'.format(user=user, repo=repo)
        self.redirect(url)
