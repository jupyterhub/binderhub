"""
Main handler classes for requests
"""
from tornado import web
from tornado.httputil import url_concat
from tornado.log import app_log

from .base import BaseHandler

from tornado.escape import url_escape, url_unescape
import json

class BinderHandler(BaseHandler):
    """
    Base class with utility methods to set and get a json cookie.

    """


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
        default_binders_list = self.settings['default_binders_list']
        new_cookie = {}
        if self.settings['list_cookie_set_binders']:
            cookie_listed = cookie.get('known', [portal_address])
        else:
            cookie_listed = []
        new_cookie['known'] = list(sorted(set( cookie_listed + [portal_address] + default_binders_list)))
        default = cookie.get('default', portal_address)
        if default not in new_cookie['known']:
            default = portal_address

        new_cookie['default'] = default
        return new_cookie

    def set_json_cookie(self, name, value, *args, **kwargs):
        self.set_cookie(name, url_escape(json.dumps(value)), *args, **kwargs)

    def get_json_cookie(self, name, *args, **kwargs):
        cookie = self.get_cookie(name, *args, **kwargs)
        if not cookie:
            return self._normalize_cookie({})
        return self._normalize_cookie(json.loads(url_unescape(cookie)))


class ExposeHandler(BaseHandler):
    """Main handler for requests"""

    def get(self):
        self.render_template(
            "expose.html",
            escaped_adresse=url_escape(self.settings['cannonical_address']),
            google_analytics_code=self.settings['google_analytics_code']
        )


class MainHandler(BaseHandler):
    """Main handler for requests"""

    def get(self):
        self.render_template(
            "index.html",
            base_url=self.settings['base_url'],
            url=None,
            ref='',
            filepath=None,
            submit=False,
            google_analytics_code=self.settings['google_analytics_code'],
            google_analytics_domain=self.settings['google_analytics_domain'],
        )


class ParameterizedMainHandler(BinderHandler):
    """Main handler that allows different parameter settings"""

    def get(self, provider_prefix, spec):
        # http://localhost:8585/v2/gh/binder-examples/dockerfile-rstudio/master
        if self.settings['use_as_federation_portal']:
            default = self.get_json_cookie('known_binders')['default']
            if default: 
            #    ## todo don't trigger if self !
                self.redirect(f'{default}/v2/{provider_prefix}/{spec}')
                return
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
            "loading.html",
            base_url=self.settings['base_url'],
            url=provider.get_repo_url(),
            ref=provider.unresolved_ref,
            filepath=self.get_argument('filepath', None),
            urlpath=self.get_argument('urlpath', None),
            submit=True,
            google_analytics_code=self.settings['google_analytics_code'],
            google_analytics_domain=self.settings['google_analytics_domain'],
        )



class SettingsHandler(BinderHandler):
    """
    This shows the settings page, mostly get the know binder for current user
    from a cookie, and display it as a list. Also get the default binder
    selected by the user and mark it as such in the settings UI.
    """

    def get(self, arg):
        return self._get()
    
    def _get(self, cookie=None):
        binders = cookie or self.get_json_cookie('known_binders')
        self.add_header('X-Frame-Options','DENY')
        self.render_template(
            "settings.html", 
            binders=binders['known'],
            default_binder= binders['default'],
            raw=json.dumps(binders, indent=2),
            use_as_federation_portal=self.settings['use_as_federation_portal'],
            google_analytics_code=self.settings['google_analytics_code']
        )

    def post(self, arg):
        nd = self.get_body_argument('default')
        cookie = self.get_json_cookie('known_binders')
        cookie['default'] = nd
        cookie = self._normalize_cookie(cookie)
        self.set_json_cookie('known_binders', cookie)
        return self._get(cookie)


class RegisterHandler(BinderHandler):
    """
    This allows a third party binder to register an
    available binder for to a federation portal (typically mybinder.org).

    This is done as follow:

        Redirect user to `/register/<url of new binder>`.

    This URL is stored the user cookie, and the user is redirect on the setting
    page where they can select which default binder to use. 

    We do not set that by default (or that could be used by services to use
    federation porta as a DoS machine, or make it unavailable.
    """


    def get(self, url):
        self.add_header('X-Frame-Options','DENY')
        binders = self.get_json_cookie('known_binders', '{}')
        binders['known'].append(url_unescape(url))
        self.set_json_cookie('known_binders', binders)
        print('set to', binders)
        self.redirect('/settings/')



class LegacyRedirectHandler(BaseHandler):
    """Redirect handler from legacy Binder"""

    def get(self, user, repo, urlpath=None):
        url = '/v2/gh/{user}/{repo}/master'.format(user=user, repo=repo)
        if urlpath is not None and urlpath.strip('/'):
            url = url_concat(url, dict(urlpath=urlpath))
        self.redirect(url)
