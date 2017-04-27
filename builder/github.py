from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.iostream import StreamClosedError
from kubernetes import client, config, watch
import hashlib
import threading
import json
from .build import Build
from queue import Queue, Empty


class GitHubBuildHandler(web.RequestHandler):
    @gen.coroutine
    def resolve_ref(self, user, repo, ref):
        """
        Resolve a given ref in a github repo into a commit object.

        Returns None if ref isn't found.

        `ref` can be a commit sha or a branch / tag name.
        """
        client = AsyncHTTPClient()
        url = "https://api.github.com/repos/{user}/{repo}/commits/{ref}".format(
            user=user, repo=repo, ref=ref
        )
        try:
            resp = yield client.fetch(url, user_agent="JupyterHub Image Builder v0.1")
        except HTTPError as e:
            if e.code == 404:
                return None

        ref_info = json.loads(resp.body.decode('utf-8'))
        return ref_info


    def _generate_build_name(self, user, repo, ref, limit=63, hash_length=6, ref_length=6):
        """
        Generate a unique build name that is within limit characters

        Is guaranteed (to acceptable level) to be unique for a given user, repo and ref.

        We really, *really* care that we always end up with the same build_name for any
        particular repo + ref, but max limit for build names is 63. So we include a prefixed
        hash of the user / repo in all build names and do some length limiting :)

        Note that build names only need to be unique over a shorter period of time, while
        image names need to be unique for longer - hence different strategies.

        TODO: Make sure that the returned value matches the k8s name validation regex,
        which is [a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*
        """
        user_repo_name = '{user}-{repo}'.format(user=user, repo=repo)

        user_repo_hash = hashlib.sha256(user_repo_name.encode('utf-8')).hexdigest()

        return '{name}-{hash}-{ref}'.format(
            name=user_repo_name[:limit - hash_length - ref_length - 2],
            hash=user_repo_hash[:hash_length],
            ref=ref[:ref_length]
        )

    @gen.coroutine
    def get(self, user, repo, ref):
        ref_info = yield self.resolve_ref(user, repo, ref)

        sha = ref_info['sha']
        build_name = self._generate_build_name(user, repo, sha).replace('_', '-')

        # FIXME: EnforceMax of 255 before image and 128 for tag
        image_name = '{prefix}{user}-{repo}:{ref}'.format(
            prefix=self.settings['docker_image_prefix'],
            user=user, repo=repo, ref=sha
        ).replace('_', '-')

        config.load_kube_config()

        api = client.CoreV1Api()

        q = Queue()
        github_url = "https://github.com/{user}/{repo}".format(user=user, repo=repo)

        build = Build(
            q=q,
            api=api,
            name=build_name,
            namespace="default",
            git_url=github_url,
            ref=sha,
            builder_image="jupyterhub/singleuser-builder:v0.1.1",
            image_name=image_name,
            push_secret=self.settings['docker_push_secret']
        )

        build_thread = threading.Thread(target=build.submit)
        log_thread = threading.Thread(target=build.stream_logs)

        build_thread.start()

        # We gonna send out event streams!
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')

        while True:
            try:
                progress = q.get_nowait()
            except Empty:
                yield gen.sleep(0.5)
                continue

            try:
                self.write('data: {}\n\n'.format(json.dumps(progress)))
                q.task_done()
            except StreamClosedError:
                # Client has gone away!
                break

            if progress['kind'] == 'pod.phasechange':
                if progress['payload'] == 'Running':
                    log_thread.start()
                elif progress['payload'] == 'Succeeded' or progress['payload'] == 'Failed':
                    # TODO: Wait to cleanup the two threads? A simple join will block, unfortunately
                    break
            yield self.flush()
