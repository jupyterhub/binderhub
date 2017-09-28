"""
Launch an image with a temporary user via JupyterHub
"""
import base64
import json
import random
import string
import uuid

from tornado.log import app_log
from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from traitlets.config import LoggingConfigurable
from traitlets import Unicode

# Add a random lowercase alphanumeric suffix to usernames to avoid collisions
# Set of characters from which to generate a suffix
SUFFIX_CHARS = string.ascii_lowercase + string.digits
# Set length of suffix. Number of combinations = SUFFIX_CHARS**SUFFIX_LENGTH = 36**8 ~= 2**41
SUFFIX_LENGTH = 8

class Launcher(LoggingConfigurable):
    """Object for encapsulating launching an image for a user"""

    hub_api_token = Unicode(help="The API token for the Hub")
    hub_url = Unicode(help="The URL of the Hub")

    async def api_request(self, url, *args, **kwargs):
        """Make an API request to JupyterHub"""
        headers = kwargs.setdefault('headers', {})
        headers.update({'Authorization': 'token %s' % self.hub_api_token})
        req = HTTPRequest(self.hub_url + 'hub/api/' + url, *args, **kwargs)
        resp = await AsyncHTTPClient().fetch(req)
        # TODO: handle errors
        return resp

    def username_from_image(self, image):
        """Generate a username for an image

        e.g. minrk-binder-example-abc123
        from gcr.io/minrk-binder-example:sha...
        """
        # use image for first part of the username
        prefix = image.split(':')[0]
        if '/' in prefix:
            # Strip 'docker-repo/' off because it's an implementation detail.
            # Only keep the image name, which has source repo info.
            prefix = prefix.split('/')[1]
        if len(prefix) > 32:
            # if it's long, truncate
            prefix = '{}-{}'.format(prefix[:15], prefix[-15:])
        # add a random suffix to avoid collisions for users on the same image
        return '{}-{}'.format(prefix, ''.join(random.choices(SUFFIX_CHARS, k=SUFFIX_LENGTH)))

    async def launch(self, image):
        """Launch a server for a given image


        - creates the user on the Hub
        - spawns a server for that user
        - generates a token
        - returns a dict containing:
          - `url`: the URL of the server
          - `token`: the token for the server
        """
        # TODO: validate the image argument?

        username = self.username_from_image(image)

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

        # generate a token
        token = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=\n')

        # start server
        app_log.info("Starting server for user %s with image %s", username, image)
        try:
            resp = await self.api_request(
                'users/%s/server' % username,
                method='POST',
                body=json.dumps({
                    'token': token,
                    'image': image,
                }).encode('utf8'),
            )
            if resp.code == 202:
                # Server hasn't actually started yet
                # We wait for it!
                for i in range(10):
                    resp = await self.api_request(
                        'users/%s' % username,
                        method='GET',
                    )

                    body = json.loads(resp.body.decode('utf-8'))
                    if body['server']:
                        break
                    # FIXME: make this configurable
                    # FIXME: Measure how long it takes for servers to start
                    # and tune this appropriately
                    await gen.sleep(1.4 ** i)
                else:
                    raise web.HTTPError(500, "Image %s for user %s took too long to launch" % (image, username))

        except HTTPError as e:
            if e.response:
                body = e.response.body
            else:
                body = ''

            app_log.error("Error starting server for %s: %s\n%s",
                username, e, body,
            )
            raise web.HTTPError(500, "Failed to launch image %s" % image)

        url = self.hub_url + 'user/%s/' % username

        return {
            'url': url,
            'token': token,
        }
