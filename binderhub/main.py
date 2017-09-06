"""
Main handler classes for requests
"""
from tornado import web
from tornado.log import app_log

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
        try:
            provider = self.get_provider(provider_prefix, spec=spec)
        except web.HTTPError:
            raise
        except Exception as e:
            app_log.error("Failed to construct provider for %s/%s")
            # FIXME: 400 assumes it's the user's fault (?)
            # maybe we should catch a special InvalidSpecError here
            raise web.HTTPError(400, str(e))

        self.render_template(
            "index.html",
            url=provider.get_repo_url(),
            ref=provider.unresolved_ref,
            filepath=self.get_argument('filepath', None),
            submit=True,
            google_analytics_code=self.settings['google_analytics_code'],
        )


class LegacyRedirectHandler(BaseHandler):
    """Redirect handler from legacy Binder"""

    def get(self, user, repo):
        url = '/v2/gh/{user}/{repo}/master'.format(user=user, repo=repo)
        self.redirect(url)
