"""
Launch an image with a temporary user via JupyterHub
"""
import asyncio
import base64
import json
import random
import re
import string
from urllib.parse import urlparse, quote
import uuid
import os
from datetime import timedelta

from tornado.log import app_log
from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from traitlets.config import LoggingConfigurable
from traitlets import Integer, Unicode, Bool, default
from jupyterhub.traitlets import Callable
from jupyterhub.utils import maybe_future

from .utils import url_path_join

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
    hub_url_local = Unicode(help="The internal URL of the Hub if different")
    @default('hub_url_local')
    def _default_hub_url_local(self):
        return self.hub_url
    create_user = Bool(True, help="Create a new Hub user")
    allow_named_servers = Bool(
        os.getenv('JUPYTERHUB_ALLOW_NAMED_SERVERS', "false") == "true",
        config=True,
        help="Named user servers are allowed. This is used only when authentication is enabled and "
             "to set unique names for user servers."
    )
    named_server_limit_per_user = Integer(
        int(os.getenv('JUPYTERHUB_NAMED_SERVER_LIMIT_PER_USER', 0)),
        config=True,
        help="""Maximum number of concurrent named servers that can be created by a user."""
    )
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
    pre_launch_hook = Callable(
        None,
        config=True,
        allow_none=True,
        help="""
        An optional hook function that you can use to implement checks before starting a user's server.
        For example if you have a non-standard BinderHub deployment,
        in this hook you can check if the current user has right to launch a new repo.

        Receives 5 parameters: launcher, image, username, server_name, repo_url
        """
    )
    launch_timeout = Integer(
        600,
        config=True,
        help="""
        Wait this many seconds until server is ready, raise TimeoutError otherwise.
        """,
    )

    async def api_request(self, url, *args, **kwargs):
        """Make an API request to JupyterHub"""
        headers = kwargs.setdefault('headers', {})
        headers.update({'Authorization': f'token {self.hub_api_token}'})
        hub_api_url = os.getenv('JUPYTERHUB_API_URL', '') or self.hub_url_local + 'hub/api/'
        if not hub_api_url.endswith('/'):
            hub_api_url += '/'
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
            f'users/{username}',
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

    async def launch(
        self,
        image,
        username,
        server_name="",
        repo_url="",
        extra_args=None,
        event_callback=None,
    ):
        """Launch a server for a given image

        - creates a temporary user on the Hub if authentication is not enabled
        - spawns a server for temporary/authenticated user
        - generates a token
        - returns a dict containing:
          - `url`: the URL of the server
          - `image`: image spec
          - `repo_url`: the url of the repo
          - `extra_args`: Dictionary of extra arguments passed to the server
          - `token`: the token for the server
        """
        # TODO: validate the image argument?

        # Matches the escaping that JupyterHub does https://github.com/jupyterhub/jupyterhub/blob/c00c3fa28703669b932eb84549654238ff8995dc/jupyterhub/user.py#L427
        escaped_username = quote(username, safe='@~')
        if self.create_user:
            # create a new user
            app_log.info("Creating user %s for image %s", username, image)
            try:
                await self.api_request(f'users/{escaped_username}', body=b'', method='POST')
            except HTTPError as e:
                if e.response:
                    body = e.response.body
                else:
                    body = ''
                app_log.error("Error creating user %s: %s\n%s",
                    username, e, body,
                )
                raise web.HTTPError(500, f"Failed to create temporary user for {image}")
        elif server_name == '':
            # authentication is enabled but not named servers
            # check if user has a running server ('')
            user_data = await self.get_user_data(escaped_username)
            if server_name in user_data['servers']:
                raise web.HTTPError(409, f"User {username} already has a running server.")
        elif self.named_server_limit_per_user > 0:
            # authentication is enabled with named servers
            # check if user has already reached to the limit of named servers
            user_data = await self.get_user_data(escaped_username)
            len_named_spawners = len([s for s in user_data['servers'] if s != ''])
            if self.named_server_limit_per_user <= len_named_spawners:
                raise web.HTTPError(
                    409,
                    "User {} already has the maximum of {} named servers."
                    "  One must be deleted before a new server can be created".format(
                        username, self.named_server_limit_per_user
                    ),
                )

        if self.pre_launch_hook:
            await maybe_future(self.pre_launch_hook(self, image, username, server_name, repo_url))

        # data to be passed into spawner's user_options during launch
        # and also to be returned into 'ready' state
        data = {'image': image,
                'repo_url': repo_url,
                'token': base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=\n')}
        if extra_args:
            data.update(extra_args)

        # server name to be used in logs
        _server_name = " {}".format(server_name) if server_name else ''

        # start server
        app_log.info(f"Starting server{_server_name} for user {username} with image {image}")
        ready_event_future = asyncio.Future()

        def _cancel_ready_event(f=None):
            if not ready_event_future.done():
                if f and f.exception():
                    ready_event_future.set_exception(f.exception())
                else:
                    ready_event_future.cancel()
        try:
            resp = await self.api_request(
                'users/{}/servers/{}'.format(escaped_username, server_name),
                method='POST',
                body=json.dumps(data).encode('utf8'),
            )
            # listen for pending spawn (launch) events until server is ready
            # do this even if previous request finished!
            buffer_list = []

            async def handle_chunk(chunk):
                lines = b"".join(buffer_list + [chunk]).split(b"\n\n")
                # the last item in the list is usually an empty line ('')
                # but it can be the partial line after the last `\n\n`,
                # so put it back on the buffer to handle with the next chunk
                buffer_list[:] = [lines[-1]]
                for line in lines[:-1]:
                    if line:
                        line = line.decode("utf8", "replace")
                    if line and line.startswith("data:"):
                        event = json.loads(line.split(":", 1)[1])
                        if event_callback:
                            await event_callback(event)

                        # stream ends when server is ready or fails
                        if event.get("ready", False):
                            if not ready_event_future.done():
                                ready_event_future.set_result(event)
                        elif event.get("failed", False):
                            if not ready_event_future.done():
                                ready_event_future.set_exception(
                                    web.HTTPError(
                                        500, event.get("message", "unknown error")
                                    )
                                )

            url_parts = ["users", username]
            if server_name:
                url_parts.extend(["servers", server_name, "progress"])
            else:
                url_parts.extend(["server/progress"])
            progress_api_url = url_path_join(*url_parts)
            self.log.debug(f"Requesting progress for {username}: {progress_api_url}")
            resp_future = self.api_request(
                progress_api_url,
                streaming_callback=lambda chunk: asyncio.ensure_future(
                    handle_chunk(chunk)
                ),
                request_timeout=self.launch_timeout,
            )
            try:
                await gen.with_timeout(
                    timedelta(seconds=self.launch_timeout), resp_future
                )
            except (gen.TimeoutError, TimeoutError):
                _cancel_ready_event()
                raise web.HTTPError(
                    500,
                    f"Image {image} for user {username} took too long to launch",
                )

        except HTTPError as e:
            _cancel_ready_event()
            if e.response:
                body = e.response.body
            else:
                body = ''

            app_log.error(
                f"Error starting server{_server_name} for user {username}: {e}\n{body}"
            )
            raise web.HTTPError(500, f"Failed to launch image {image}")
        except Exception:
            _cancel_ready_event()
            raise

        # verify that the server is running!
        try:
            # this should already be done, but it's async so wait a finite time
            ready_event = await gen.with_timeout(
                timedelta(seconds=5), ready_event_future
            )
        except (gen.TimeoutError, TimeoutError):
            raise web.HTTPError(
                500, f"Image {image} for user {username} failed to launch"
            )

        data["url"] = self.hub_url + f"user/{escaped_username}/{server_name}"
        self.log.debug(data["url"])
        return data
