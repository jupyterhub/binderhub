"""
Contains build of a docker image from a git repository.
"""

import base64
import json
import random
import re
import string
from urllib.parse import urlparse
import uuid

from kubernetes import client, watch
from tornado.ioloop import IOLoop
from tornado.log import app_log
from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError

_ssh_url_pat = re.compile(r'.*@.*\:')

# Add a random lowercase alphanumeric suffix to usernames to avoid collisions
# Set of characters from which to generate a suffix
SUFFIX_CHARS = string.ascii_lowercase + string.digits
# Set length of suffix. Number of combinations = SUFFIX_CHARS**SUFFIX_LENGTH = 36**8 ~= 2**41
SUFFIX_LENGTH = 8


class Build:
    """Represents a build of a git repository into a docker image.

    This ultimately maps to a single pod on a kubernetes cluster. Many
    different build objects can point to this single pod and perform
    operations on the pod. The code in this class needs to be careful and take
    this into account.

    For example, operations a Build object tries might not succeed because
    another Build object pointing to the same pod might have done something
    else. This should be handled gracefully, and the build object should
    reflect the state of the pod as quickly as possible.

    ``name``
        The ``name`` should be unique and immutable since it is used to
        sync to the pod. The ``name`` should be unique for a
        ``(git_url, ref)`` tuple, and the same tuple should correspond
        to the same ``name``. This allows use of the locking provided by k8s
        API instead of having to invent our own locking code.

    """
    def __init__(self, q, api, name, namespace, git_url, ref, builder_image,
                 image_name, push_secret, hub_url, hub_api_token):
        self.q = q
        self.api = api
        self.git_url = git_url
        self.ref = ref
        self.name = name
        self.namespace = namespace
        self.image_name = image_name
        self.push_secret = push_secret
        self.builder_image = builder_image
        self.hub_url = hub_url
        self.hub_api_token = hub_api_token
        self.username = self._username_from_repo(git_url)

    def _username_from_repo(self, repo):
        """Generate a username for a git repo url

        e.g. minrk-binder-example-abc123
        from https://github.com/minrk/binder-example.git
        """
        # start with url path
        if '://' not in repo and _ssh_url_pat.match(repo):
            # ssh url
            path = repo.split(':', 1)[1]
        else:
            path = urlparse(repo).path

        prefix = path.strip('/').replace('/', '-')

        if prefix.endswith('.git'):
            # strip trailing .git
            prefix = prefix[:-4]

        if len(prefix) > 32:
            # if it's long, truncate
            prefix = '{}-{}'.format(prefix[:15], prefix[-15:])

        # add a random suffix to avoid collisions for users on the same image
        return '{}-{}'.format(prefix, ''.join(random.choices(SUFFIX_CHARS, k=SUFFIX_LENGTH)))

    def get_cmd(self):
        """Get the cmd to run to build the image"""
        cmd = [
            'jupyter-repo2docker',
            self.git_url,
            '--ref', self.ref,
            '--image', self.image_name,
            '--no-clean', '--no-run', '--json-logs',
        ]

        if self.push_secret:
            cmd.append('--push')

        return cmd

    def progress(self, kind, obj):
        """Put the current action item into the queue for execution."""
        IOLoop.instance().add_callback(self.q.put, {'kind': kind, 'payload': obj})

    def submit(self):
        """Submit a image spec to openshift's s2i and wait for completion """
        volume_mounts = [
            client.V1VolumeMount(mount_path="/var/run/docker.sock", name="docker-socket")
        ]
        volumes = [client.V1Volume(
            name="docker-socket",
            host_path=client.V1HostPathVolumeSource(path="/var/run/docker.sock")
        )]

        if self.push_secret:
            volume_mounts.append(client.V1VolumeMount(mount_path="/root/.docker", name='docker-push-secret'))
            volumes.append(client.V1Volume(
                name='docker-push-secret',
                secret=client.V1SecretVolumeSource(secret_name=self.push_secret)
            ))

        self.pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=self.name,
                labels={"name": self.name}
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        image=self.builder_image,
                        name="builder",
                        args=self.get_cmd(),
                        image_pull_policy='Always',
                        volume_mounts=volume_mounts,
                    )
                ],
                volumes=volumes,
                restart_policy="Never"
            )
        )

        try:
            ret = self.api.create_namespaced_pod(self.namespace, self.pod)
        except client.rest.ApiException as e:
            if e.status == 409:
                # Someone else created it!
                pass
            else:
                raise

        w = watch.Watch()
        try:
            for f in w.stream(
                    self.api.list_namespaced_pod,
                    self.namespace,
                    label_selector="name={}".format(self.name)):
                if f['type'] == 'DELETED':
                    self.progress('pod.phasechange', 'Deleted')
                    return
                self.pod = f['object']
                self.progress('pod.phasechange', self.pod.status.phase)
                if self.pod.status.phase == 'Succeeded':
                    self.cleanup()
                elif self.pod.status.phase == 'Failed':
                    self.cleanup()
        finally:
            w.stop()

    def stream_logs(self):
        """Stream a pod's log."""
        for line in self.api.read_namespaced_pod_log(
                self.name,
                self.namespace,
                follow=True,
                _preload_content=False):

            self.progress('log', line.decode('utf-8'))

    def cleanup(self):
        """Delete a kubernetes pod."""
        try:
            self.api.delete_namespaced_pod(
                name=self.name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(grace_period_seconds=0))
        except client.rest.ApiException as e:
            if e.status == 404:
                # Is ok, someone else has already deleted it
                pass
            else:
                raise

    # launch-related methods

    async def hub_api_request(self, url, *args, **kwargs):
        """Make an API request to JupyterHub"""
        headers = kwargs.setdefault('headers', {})
        headers.update({'Authorization': 'token %s' % self.hub_api_token})
        req = HTTPRequest(self.hub_url + 'hub/api/' + url, *args, **kwargs)
        resp = await AsyncHTTPClient().fetch(req)
        # TODO: handle errors
        return resp

    async def launch(self):
        """Launch a server for a given image

        - creates the user on the Hub
        - spawns a server for that user
        - generates a token
        - returns a dict containing:
          - `url`: the URL of the server
          - `token`: the token for the server
        """

        username = self.username
        image = self.image_name
        request_id = self.git_url

        # create a new user
        app_log.info("Creating user %s for %s", username, self.git_url)
        try:
            await self.hub_api_request('users/%s' % username, body=b'', method='POST')
        except HTTPError as e:
            if e.response:
                body = e.response.body
            else:
                body = ''
            app_log.error("Error creating user %s: %s\n%s",
                username, e, body,
            )
            raise web.HTTPError(500, "Failed to create temporary user for %s" % request_id)

        # generate a token
        token = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=\n')

        # start server
        app_log.info("Starting server for user %s with image %s", username, image)
        try:
            resp = await self.hub_api_request(
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
                    resp = await self.hub_api_request(
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
