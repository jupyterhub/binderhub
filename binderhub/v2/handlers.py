from ..base import BaseHandler


class BuildHandler(BaseHandler):
    """POST /v2/build/:provider/:spec triggers a build,

    responding with a JWT token containing info

    JWT contents:

    {
        username: Hub user name
        servername: Hub server name (usually '')
        image: The image to be launched
        build-id: The build id for logging
    }

    Response (JSON):

    {
        launch_token: opaque token,
        events_url: opaque url with token,
    }
    """

    path = r"/v2/build/([^/]+)/(.+)"

    def post(self, provider, spec):
        # generate username
        # check for image
        # trigger build (if needed)
        # reply with event url, containing jwt token
        pass


class EventsHandler(BaseHandler):
    """GET /v2/events/:token streams logs

    No transactions should occur as a result of making this request.
    Reconnects should always be stateless and harmless.
    """

    path = r"/v2/events/([^/]+)"

    def get(self, token):
        # decode_jwt to get build-id, image
        # get/relay build logs
        # final event sends to the launch url
        pass


class LaunchHandler(BaseHandler):
    """POST /v2/launch/:token triggers the actual launch"""
    path = r"/v2/launch/([^/]+)"

    def post(self, token):
        # decode_jwt to get username, servername, image
        # validate???
        # request launch
        # redirect to launch URL
        pass


default_handlers = [BuildHandler, EventsHandler, LaunchHandler]
