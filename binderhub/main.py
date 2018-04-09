"""
Main handler classes for requests
"""
from tornado import web
from tornado.httputil import url_concat
from tornado.log import app_log

from .base import BaseHandler


class MainHandler(BaseHandler):
    """Main handler for requests"""

    def get(self):
        self.render_template(
            "index.html",
            base_url=self.settings['base_url'],
            submit=False,
            google_analytics_code=self.settings['google_analytics_code'],
            google_analytics_domain=self.settings['google_analytics_domain'],
        )


class ParameterizedMainHandler(BaseHandler):
    """Main handler that allows different parameter settings"""

    def get(self, provider_prefix, _unescaped_spec):
        # re-extract spec from request.path
        # get the original, raw spec, without tornado's unquoting
        # this is needed because tornado converts 'foo%2Fbar/ref' to 'foo/bar/ref'
        prefix = '/v2/' + provider_prefix
        idx = self.request.path.index(prefix)
        spec = self.request.path[idx + len(prefix) + 1:]
        try:
            self.get_provider(provider_prefix, spec=spec)
        except web.HTTPError:
            raise
        except Exception as e:
            app_log.error(
                "Failed to construct provider for %s/%s",
                provider_prefix, spec,
            )
            # FIXME: 400 assumes it's the user's fault (?)
            # maybe we should catch a special InvalidSpecError here
            raise web.HTTPError(400, str(e))

        self.render_template(
            "loading.html",
            base_url=self.settings['base_url'],
            provider_spec='{}/{}'.format(provider_prefix, spec),
            filepath=self.get_argument('filepath', None),
            urlpath=self.get_argument('urlpath', None),
            submit=True,
            google_analytics_code=self.settings['google_analytics_code'],
            google_analytics_domain=self.settings['google_analytics_domain'],
        )


class LegacyRedirectHandler(BaseHandler):
    """Redirect handler from legacy Binder"""

    def get(self, user, repo, urlpath=None):
        url = '/v2/gh/{user}/{repo}/master'.format(user=user, repo=repo)
        if urlpath is not None and urlpath.strip('/'):
            url = url_concat(url, dict(urlpath=urlpath))
        self.redirect(url)
