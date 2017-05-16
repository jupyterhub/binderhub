"""Handler for working with GitHub for builds."""

import hashlib
import json
from queue import Queue, Empty
import threading

from kubernetes import client, config, watch
from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.iostream import StreamClosedError

from .build import Build


class GitHubBuildHandler(web.RequestHandler):
    """A handler for working with GitHub."""
    @gen.coroutine
    def emit(self, data):
        if type(data) is not str:
            serialized_data = json.dumps(data)
        else:
            serialized_data = data
        self.write('data: {}\n\n'.format(serialized_data))
        yield self.flush()

    @gen.coroutine
    def resolve_ref(self, user, repo, ref):
        """
        Resolve a given ref in a GitHub repo into a commit object.

        Parameters
        ----------
        `ref` -- a commit sha or a branch / tag name.

        Returns
        -------
        None, if ref isn't found.
        """
        client = AsyncHTTPClient()
        url = "https://api.github.com/repos/{user}/{repo}/commits/{ref}".format(
            user=user, repo=repo, ref=ref
        )
        if self.settings['github_auth_token']:
            auth = {
                'auth_username': 'yuvipanda',
                'auth_password': self.settings['github_auth_token']
            }
        else:
            auth = {}

        try:
            resp = yield client.fetch(url, user_agent="JupyterHub Image Builder v0.1", **auth)
        except HTTPError as e:
            if e.code == 404:
                return None
            else:
                raise

        ref_info = json.loads(resp.body.decode('utf-8'))
        return ref_info


    def _generate_build_name(self, user, repo, ref, limit=63, hash_length=6, ref_length=6):
        """
        Generate a unique build name that is within limited number of characters.

        Guaranteed (to acceptable level) to be unique for a given user, repo,
        and ref.

        We really, *really* care that we always end up with the same
        'build_name' for a particular repo + ref, but the default max
        character limit for build names is 63. To meet this constraint, we
        include a prefixed hash of the user / repo in all build names and do
        some length limiting :)

        Note that 'build' names only need to be unique over a shorter period
        of time, while 'image' names need to be unique for longer. Hence,
        different strategies are used.

        TODO: Make sure that the returned value matches the k8s name
        validation regex, which is:
        [a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*
        """
        user_repo_name = '{user}-{repo}'.format(user=user, repo=repo)

        user_repo_hash = hashlib.sha256(user_repo_name.encode('utf-8')).hexdigest()

        return '{name}-{hash}-{ref}'.format(
            name=user_repo_name[:limit - hash_length - ref_length - 2],
            hash=user_repo_hash[:hash_length],
            ref=ref[:ref_length]
        ).lower()

    @gen.coroutine
    def get(self, user, repo, ref):
        """Get a built image for a given GitHub user, repo, and ref."""
        ref_info = yield self.resolve_ref(user, repo, ref)

        sha = ref_info['sha']
        build_name = self._generate_build_name(user, repo, sha).replace('_', '-')

        # FIXME: EnforceMax of 255 before image and 128 for tag
        image_name = '{prefix}{user}-{repo}:{ref}'.format(
            prefix=self.settings['docker_image_prefix'],
            user=user, repo=repo, ref=sha
        ).replace('_', '-').lower()

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        api = client.CoreV1Api()

        q = Queue()
        github_url = "https://github.com/{user}/{repo}".format(user=user, repo=repo)

        build = Build(
            q=q,
            api=api,
            name=build_name,
            namespace=self.settings["build_namespace"],
            git_url=github_url,
            ref=sha,
            image_name=image_name,
            push_secret=self.settings['docker_push_secret']
        )

        build_thread = threading.Thread(target=build.submit)
        log_thread = threading.Thread(target=build.stream_logs)

        build_thread.start()

        # We gonna send out event streams!
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

        done = False

        while True:
            try:
                progress = q.get_nowait()
            except Empty:
                yield gen.sleep(0.5)
                continue


            if progress['kind'] == 'pod.phasechange':
                if progress['payload'] == 'Pending':
                    event = {'message': 'Waiting for build to start...', 'phase': 'waiting'}
                elif progress['payload'] == 'Deleted':
                    event = {'phase': 'completed', 'message': 'Build completed, launching...', 'imageName': image_name}
                    done = True
                elif progress['payload'] == 'Running':
                    if not log_thread.is_alive():
                        log_thread.start()
                    continue
                elif progress['payload'] == 'Succeeded':
                    # Do nothing, is ok!
                    continue
                else:
                    event = {'phase': progress['payload']}
            elif progress['kind'] == 'log':
                # We expect logs to be already JSON structured anyway
                event = progress['payload']

            try:
                yield self.emit(event)
                q.task_done()
                if done:
                    break
            except StreamClosedError:
                # Client has gone away!
                break
