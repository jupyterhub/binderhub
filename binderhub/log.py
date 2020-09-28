"""logging utilities"""

# copied from jupyterhub 1.1.0
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import traceback
from http.cookies import SimpleCookie
from urllib.parse import urlparse
from urllib.parse import urlunparse

from tornado.log import access_log
from tornado.log import LogFormatter
from tornado.web import HTTPError
from tornado.web import StaticFileHandler


# url params to be scrubbed if seen
# any url param that *contains* one of these
# will be scrubbed from logs
SCRUB_PARAM_KEYS = ("token", "auth", "key", "code", "state")


def _scrub_uri(uri):
    """scrub auth info from uri"""
    parsed = urlparse(uri)
    if parsed.query:
        # check for potentially sensitive url params
        # use manual list + split rather than parsing
        # to minimally perturb original
        parts = parsed.query.split("&")
        changed = False
        for i, s in enumerate(parts):
            if "=" in s:
                key, value = s.split("=", 1)
                for substring in SCRUB_PARAM_KEYS:
                    if substring in key:
                        parts[i] = key + "=[secret]"
                        changed = True
        if changed:
            parsed = parsed._replace(query="&".join(parts))
            return urlunparse(parsed)
    return uri


def _scrub_headers(headers):
    """scrub auth info from headers"""
    headers = dict(headers)
    if "Authorization" in headers:
        auth = headers["Authorization"]
        if " " in auth:
            auth_type = auth.split(" ", 1)[0]
        else:
            # no space, hide the whole thing in case there was a mistake
            auth_type = ""
        headers["Authorization"] = "{} [secret]".format(auth_type)
    if "Cookie" in headers:
        c = SimpleCookie(headers["Cookie"])
        redacted = []
        for name in c.keys():
            redacted.append("{}=[secret]".format(name))
        headers["Cookie"] = "; ".join(redacted)
    return headers


# log_request adapted from IPython (BSD)


def log_request(handler):
    """log a bit more information about each request than tornado's default

    - move static file get success to debug-level (reduces noise)
    - get proxied IP instead of proxy IP
    - log referer for redirect and failed requests
    - log user-agent for failed requests
    - record per-request metrics in prometheus
    """
    status = handler.get_status()
    request = handler.request
    if status == 304 or (
        status < 300
        and (
            isinstance(handler, StaticFileHandler)
            or getattr(handler, "log_success_debug", False)
        )
    ):
        # static-file success and 304 Found are debug-level
        log_method = access_log.debug
    elif status < 400:
        log_method = access_log.info
    elif status < 500:
        log_method = access_log.warning
    else:
        log_method = access_log.error

    uri = _scrub_uri(request.uri)
    headers = _scrub_headers(request.headers)

    request_time = 1000.0 * handler.request.request_time()

    try:
        user = handler.current_user
    except (HTTPError, RuntimeError):
        username = ""
    else:
        if user is None:
            username = ""
        elif isinstance(user, str):
            username = user
        elif isinstance(user, dict):
            username = user.get("name", "unknown")
        else:
            username = "unknown"

    ns = dict(
        status=status,
        method=request.method,
        ip=request.remote_ip,
        uri=uri,
        request_time=request_time,
        user=username,
        location="",
    )
    msg = "{status} {method} {uri}{location} ({user}@{ip}) {request_time:.2f}ms"
    if status >= 500 and status not in {502, 503}:
        log_method(json.dumps(headers, indent=2))
    elif status in {301, 302}:
        # log redirect targets
        # FIXME: _headers is private, but there doesn't appear to be a public way
        # to get headers from tornado
        location = handler._headers.get("Location")
        if location:
            ns["location"] = " -> {}".format(_scrub_uri(location))
    log_method(msg.format(**ns))
