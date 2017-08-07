"""
Interaction with the Docker Registry
"""
import base64
import json
import os

from tornado import gen, httpclient
from tornado.httputil import url_concat


class DockerRegistry:
    def __init__(self, registry):
        if not registry.startswith('https://'):
            registry = 'https://' + registry
        with open(os.path.expanduser('~/.docker/config.json')) as f:
            raw_auths = json.load(f)['auths']

        self.username, self.password = base64.b64decode(
            raw_auths[registry]['auth'].encode('utf-8')
        ).decode('utf-8').split(':', 1)

        self.registry = registry

    @gen.coroutine
    def get_image_manifest(self, image, tag):
        client = httpclient.AsyncHTTPClient()
        # first, get a token to perform the manifest request
        auth_req = httpclient.HTTPRequest(
            url_concat('{}/v2/token'.format(self.registry), {
                # HACK: This won't work for all registries!
                'service': self.registry.split('://', 1)[-1],
                'scope': 'repository:{}:pull'.format(image),
            }),
            auth_username=self.username,
            auth_password=self.password,
        )
        auth_resp = yield client.fetch(auth_req)
        token = json.loads(auth_resp.body.decode('utf-8', 'replace'))['token']

        req = httpclient.HTTPRequest(
            '{}/v2/{}/manifests/{}'.format(self.registry, image, tag),
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
