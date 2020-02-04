from ..base import BaseHandler


class V2BuildHandler(BaseHandler):
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
        events_url: opaque url,

    }
    """

    def post(self, provider, spec):
        # generate username
        # check for image
        # trigger build (if needed)
        # reply with:
        pass


class V2EventsHandler(BaseHandler):
    """GET /v2/events/:token logs"""

    def get(self, token):
        # decode_jwt to get build-id, image
        # get/relay build logs
        pass


class V2LaunchHandler(BaseHandler):
    def post(self, token):
        # decode_jwt to get username, servername, image
        # validate???
        # request launch
        # redirect to launch URL
        pass
