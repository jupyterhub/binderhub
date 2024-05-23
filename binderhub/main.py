"""
Main handler classes for requests
"""

from tornado.httputil import url_concat
from tornado.web import authenticated

from .base import BaseHandler


class MainHandler(BaseHandler):
    """Main handler for requests"""

    @authenticated
    def get(self):
        repoproviders_display_config = [
            repo_provider_class.display_config
            for repo_provider_class in self.settings["repo_providers"].values()
        ]
        page_config = {
            "baseUrl": self.settings["base_url"],
            "badgeBaseUrl": self.get_badge_base_url(),
            "logoUrl": self.static_url("logo.svg"),
            "logoWidth": "320px",
            "repoProviders": repoproviders_display_config,
        }
        self.render_template(
            "page.html",
            page_config=page_config,
            extra_footer_scripts=self.settings["extra_footer_scripts"],
        )


class LegacyRedirectHandler(BaseHandler):
    """Redirect handler from legacy Binder"""

    @authenticated
    def get(self, user, repo, urlpath=None):
        url = f"/v2/gh/{user}/{repo}/master"
        if urlpath is not None and urlpath.strip("/"):
            url = url_concat(url, dict(urlpath=urlpath))
        self.redirect(url)
