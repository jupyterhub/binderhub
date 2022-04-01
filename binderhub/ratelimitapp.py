"""Application for external managing of rate limits

Use in combination with BinderHub.rate_limit_url
and BinderHub.rate_limit_token
"""

import json
import logging
import os
import re
from http.client import responses

import tornado.log
import tornado.options
from tornado import ioloop, web
from traitlets import Integer, Set, Unicode, default
from traitlets.config import Application

from .base import BaseHandler
from .ratelimit import RateLimitExceeded, RepoRateLimiter, RequestRateLimiter

_auth_header_pat = re.compile(r"^(?:token|bearer)\s+([^\s]+)$", flags=re.IGNORECASE)


class RateLimitHandler(BaseHandler):
    """API endpoint for external storage of rate limits"""

    def initialize(self, tokens, rate_limiters):
        self.rate_limit_tokens = tokens
        self.rate_limiters = rate_limiters
        self.log = tornado.log.app_log

    def get_current_user(self):
        """Authenticate rate limit requests with tokens"""
        auth_header = self.request.headers.get("Authorization")
        if not auth_header:
            return
        match = _auth_header_pat.match(auth_header)
        if not match:
            return None
        token = match.group(1)
        return f"token-{token[:3]}..."

    def set_default_headers(self):
        super().set_default_headers()
        self.set_header("Content-Type", "application/json")

    def write_error(self, status_code, **kwargs):
        exc_info = kwargs.get("exc_info")
        message = ""
        status_message = responses.get(status_code, "Unknown HTTP Error")
        if exc_info:
            message = self.extract_message(exc_info)
        if not message:
            message = status_message
        self.write(json.dumps({"message": message}))

    @web.authenticated
    def post(self, which, key):
        """Increment rate limit of kind `which` for key `key`"""
        initial_limit = None
        if self.request.body:
            try:
                body = json.loads(self.request.body)
                initial_limit = body.get("limit", None)
            except Exception:
                raise web.HTTPError(
                    400,
                    f"Rate limit body must be a dict with a 'limit' key, got {self.request.body}",
                )
            if not (initial_limit is None or isinstance(initial_limit, int)):
                raise web.HTTPError(
                    400, f"limit must be null or a number, not {initial_limit}"
                )

        try:
            rate_limiter = self.rate_limiters[which]
        except KeyError:
            raise web.HTTPError(404, f"No such rate limit: {which}")

        if rate_limiter.limit == 0:
            # no limit
            self.write(
                json.dumps(
                    {
                        "limit": {
                            "limit": 0,
                            "remaining": 0,
                            "reset": 0,
                            "reset_in": 0,
                        }
                    }
                )
            )
            return

        try:
            limit = rate_limiter.increment(key, initial_limit)
        except RateLimitExceeded as e:
            raise web.HTTPError(429, str(e))

        self.log.debug(f"Rate limit for {which}/{key}: {limit}")

        self.write(json.dumps({"limit": limit}))


aliases = {}
aliases.update(Application.aliases)
aliases.update(
    {
        "ip": "RateLimitApp.ip",
        "port": "RateLimitApp.port",
    }
)


class RateLimitApp(Application):
    # load the same config files as binderhub itself
    name = "binderhub"

    aliases = aliases
    classes = [RepoRateLimiter, RequestRateLimiter]

    ip = Unicode("", config=True)
    port = Integer(8888, config=True)

    tokens = Set(config=True)

    @default("tokens")
    def _default_tokens(self):
        tokens = set(os.environ.get("RATE_LIMIT_TOKENS", "").strip().split(";"))
        tokens.discard("")
        return tokens

    def initialize(self, argv=None):
        super().initialize(argv)
        # hook up tornado logging
        tornado.options.options.logging = logging.getLevelName(self.log_level)
        tornado.log.enable_pretty_logging()
        self.log = tornado.log.app_log

        self.rate_limiters = {
            "repo": RepoRateLimiter(parent=self),
            "request": RequestRateLimiter(parent=self),
        }

    def start(self, run_loop=True):
        if not self.tokens:
            self.exit("Need to set one of $RATE_LIMIT_TOKENS or c.RateLimitApp.tokens.")
        web_app = web.Application(
            [
                (
                    "/([^/]+)/(.+)",
                    RateLimitHandler,
                    {
                        "tokens": self.tokens,
                        "rate_limiters": self.rate_limiters,
                    },
                )
            ]
        )
        self.http_server = web.HTTPServer(
            web_app,
            xheaders=True,
        )
        self.log.info(f"Rate limiter listening on {self.ip}:{self.port}")
        self.http_server.listen(self.port, self.ip)
        if run_loop:
            ioloop.IOLoop.current().start()


main = RateLimitApp.launch_instance

if __name__ == "__main__":
    main()
