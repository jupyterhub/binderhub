from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.iostream import StreamClosedError
from kubernetes import client, config, watch
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


    @gen.coroutine
    def get(self, user, repo, ref):
        ref_info = yield self.resolve_ref(user, repo, ref)
        sha = ref_info['sha']

        # TODO: Truncate individual bits so we are still unique but < 63chars
        build_name = '{user}-{repo}-{ref}'.format(
            user=user, repo=repo, ref=sha[:6]
        ).replace('_', '-')

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

        while True:
            try:
                progress = q.get_nowait()
            except Empty:
                yield gen.sleep(0.5)
                continue

            try:
                self.write(json.dumps(progress))
                q.task_done()
            except StreamClosedError:
                # Client has gone away!
                break

            if progress['kind'] == 'pod.phasechange':
                if progress['payload'] == 'Running':
                    log_thread.start()
                elif progress['payload'] == 'Succeeded' or progress['payload'] == 'Failed':
                    # TODO: Wait to cleanup the two threads?
                    break
            yield self.flush()
