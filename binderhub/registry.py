"""
Interaction with the Docker Registry
"""
import base64
import json
import os

from tornado import gen, httpclient
from tornado.httputil import url_concat


class DockerRegistry:
    def __init__(self, auth_host, auth_token_url, registry_host):
        with open(os.path.expanduser('~/.docker/config.json')) as f:
            raw_auths = json.load(f)['auths']

        self.username, self.password = base64.b64decode(
            raw_auths[auth_host]['auth'].encode('utf-8')
        ).decode('utf-8').split(':', 1)

        self.auth_token_url = auth_token_url
        self.registry_host = registry_host

    @gen.coroutine
    def get_image_manifest(self, image, tag):
        client = httpclient.AsyncHTTPClient()
        # first, get a token to perform the manifest request
        auth_req = httpclient.HTTPRequest(
            url_concat(self.auth_token_url,
                       {'scope': 'repository:{}:pull'.format(image)}),
            auth_username=self.username,
            auth_password=self.password,
        )
        auth_resp = yield client.fetch(auth_req)
        token = json.loads(auth_resp.body.decode('utf-8', 'replace'))['token']

        req = httpclient.HTTPRequest(
            '{}/v2/{}/manifests/{}'.format(self.registry_host, image, tag),
            headers={'Authorization': 'Bearer {}'.format(token)},
        )
        try:
            resp = yield client.fetch(req)
        except httpclient.HTTPError as e:
            if e.code == 404:
                # 404 means it doesn't exist
                return None
            else:
                raise
        else:
            return json.loads(resp.body.decode('utf-8'))
