"""
Handler for URL redirection
"""
import base64
import json
import random
import string
import uuid
from urllib.parse import quote

from tornado.log import app_log
from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.httputil import url_concat

from .base import BaseHandler

# Add a random lowercase alphanumeric suffix to usernames to avoid collisions
# Set of characters from which to generate a suffix
SUFFIX_CHARS = string.ascii_lowercase + string.digits
# Set length of suffix. Number of combinations = SUFFIX_CHARS**SUFFIX_LENGTH = 36**8 ~= 2**41
SUFFIX_LENGTH = 8

class RedirectHandler(BaseHandler):
    """Handler for URL redirects."""
    async def api_request(self, url, *args, **kwargs):
        """Make an API request to JupyterHub"""
        headers = kwargs.setdefault('headers', {})
        headers.update({'Authorization': 'token %s' % self.settings['hub_api_token']})
        req = HTTPRequest(self.settings['hub_url'] + 'hub/api/' + url, *args, **kwargs)
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

    async def get(self):
        image = self.get_argument('image')
        filepath = self.get_argument('filepath')
        if not image:
            raise web.HTTPError(400, "image argument is required")

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

        url = self.settings['hub_url'] + 'user/%s/' % username
        if filepath:
            url = url + 'tree/%s' % quote(filepath)

        app_log.info("Redirecting to %s", url)
        # redirect with token
        self.redirect(url_concat(url, {'token': token}))

