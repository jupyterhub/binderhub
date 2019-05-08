"""
Launch an image with a temporary user via JupyterHub
"""
import base64
import json
import random
import re
import string
from urllib.parse import urlparse
import uuid
import os

from tornado.log import app_log
from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from traitlets.config import LoggingConfigurable
from traitlets import Integer, Unicode, Bool

# pattern for checking if it's an ssh repo and not a URL
# used only after verifying that `://` is not present
_ssh_repo_pat = re.compile(r'.*@.*\:')

# Add a random lowercase alphanumeric suffix to usernames to avoid collisions
# Set of characters from which to generate a suffix
SUFFIX_CHARS = string.ascii_lowercase + string.digits
# Set length of suffix. Number of combinations = SUFFIX_CHARS**SUFFIX_LENGTH = 36**8 ~= 2**41
SUFFIX_LENGTH = 8


class Launcher(LoggingConfigurable):
    """Object for encapsulating launching an image for a user"""

    hub_api_token = Unicode(help="The API token for the Hub")
    hub_url = Unicode(help="The URL of the Hub")
    create_user = Bool(True, help="Create a new Hub user")
    retries = Integer(
        4,
        config=True,
        help="""Number of attempts to make on Hub API requests.

        Adds resiliency to intermittent Hub failures,
        most commonly due to Hub, proxy, or ingress interruptions.
        """
    )
    retry_delay = Integer(
        4,
        config=True,
        help="""
        Time (seconds) to wait between retries for Hub API requests.

        Time is scaled exponentially by the retry attempt (i.e. 2, 4, 8, 16 seconds)
        """
    )

    async def api_request(self, url, *args, **kwargs):
        """Make an API request to JupyterHub"""
        headers = kwargs.setdefault('headers', {})
        headers.update({'Authorization': 'token %s' % self.hub_api_token})
        hub_api_url = os.getenv('JUPYTERHUB_API_URL', '') or self.hub_url + 'hub/api/'
        request_url = hub_api_url + url
        req = HTTPRequest(request_url, *args, **kwargs)
        retry_delay = self.retry_delay
        for i in range(1, self.retries + 1):
            try:
                return await AsyncHTTPClient().fetch(req)
            except HTTPError as e:
                # swallow 409 errors on retry only (not first attempt)
                if i > 1 and e.code == 409 and e.response:
                    self.log.warning("Treating 409 conflict on retry as success")
                    return e.response
                # retry requests that fail with error codes greater than 500
                # because they are likely intermittent issues in the cluster
                # e.g. 502,504 due to ingress issues or Hub relocating,
                # 599 due to connection issues such as Hub restarting
                if e.code >= 500:
                    self.log.error("Error accessing Hub API (using %s): %s", request_url, e)
                    if i == self.retries:
                        # last api request failed, raise the exception
                        raise
                    await gen.sleep(retry_delay)
                    # exponential backoff for consecutive failures
                    retry_delay *= 2
                else:
                    raise

    async def get_user_data(self, username):
        resp = await self.api_request(
            'users/%s' % username,
            method='GET',
        )
        body = json.loads(resp.body.decode('utf-8'))
        return body

    def unique_name_from_repo(self, repo_url):
        """Generate a unique name for a git repo url

        e.g. minrk-binder-example-abc123
        from https://github.com/minrk/binder-example.git
        """
        # start with url path
        if '://' not in repo_url and _ssh_repo_pat.match(repo_url):
            # ssh url
            path = repo_url.split(':', 1)[1]
        else:
            path = urlparse(repo_url).path

        prefix = path.strip('/').replace('/', '-').lower()

        if prefix.endswith('.git'):
            # strip trailing .git
            prefix = prefix[:-4]

        if len(prefix) > 32:
            # if it's long, truncate
            prefix = '{}-{}'.format(prefix[:15], prefix[-15:])

        # add a random suffix to avoid collisions for users on the same image
        return '{}-{}'.format(prefix, ''.join(random.choices(SUFFIX_CHARS, k=SUFFIX_LENGTH)))

    async def launch(self, image, username, server_name='', repo_url='', user_options=None):
        """Launch a server for a given image

        - creates a temporary user on the Hub if authentication is not enabled
        - spawns a server for temporary/authenticated user with user options
        - generates a token
        - returns a dict containing:
          - `url`: the URL of the server
          - `token`: the token for the server
        """
        # TODO: validate the image argument?

        if self.create_user:
            # create a new user
            app_log.info("Creating user %s for image %s", username, image)
            try:
                await self.api_request('users/%s' % username, body=b'', method='POST')
            except HTTPError as e:
                if e.response:
                    body = e.response.body
                else:
                    body = ''
                app_log.error("Error creating user %s: %s\n%s",
                    username, e, body,
                )
                raise web.HTTPError(500, "Failed to create temporary user for %s" % image)
        elif server_name == '':
            # authentication is enabled but not named servers
            # check if user has a running server ('')
            user_data = await self.get_user_data(username)
            if server_name in user_data['servers']:
                raise web.HTTPError(409, "User %s already has a running server." % username)

        # data to be passed into spawner's user_options during launch
        _user_options = {'image': image,
                         'repo_url': repo_url,
                         'token': base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=\n')}
        if user_options is None:
            user_options = _user_options
        else:
            user_options.update(_user_options)

        # server name to be used in logs
        _server_name = " {}".format(server_name) if server_name else ''

        # start server
        app_log.info("Starting server%s for user %s with image %s", _server_name, username, image)
        try:
            resp = await self.api_request(
                'users/{}/servers/{}'.format(username, server_name),
                method='POST',
                body=json.dumps(user_options).encode('utf8'),
            )
            if resp.code == 202:
                # Server hasn't actually started yet
                # We wait for it!
                # NOTE: This ends up being about ten minutes
                for i in range(64):
                    user_data = await self.get_user_data(username)
                    if user_data['servers'][server_name]['ready']:
                        break
                    if not user_data['servers'][server_name]['pending']:
                        raise web.HTTPError(500, "Image %s for user %s failed to launch" % (image, username))
                    # FIXME: make this configurable
                    # FIXME: Measure how long it takes for servers to start
                    # and tune this appropriately
                    await gen.sleep(min(1.4 ** i, 10))
                else:
                    raise web.HTTPError(500, "Image %s for user %s took too long to launch" % (image, username))

        except HTTPError as e:
            if e.response:
                body = e.response.body
            else:
                body = ''

            app_log.error("Error starting server{} for user {}: {}\n{}".
                          format(_server_name, username, e, body))
            raise web.HTTPError(500, "Failed to launch image %s" % image)

        # data to be returned into 'ready' state
        data = {'url': self.hub_url + 'user/%s/%s' % (username, server_name),
                'token': user_options['token']}
        return data
