import json
from tornado import gen

from traitlets import Unicode
from traitlets.config import LoggingConfigurable
from tornado.httpclient import AsyncHTTPClient, HTTPError


class RepoProvider(LoggingConfigurable):
    name = Unicode(
        None,
        help="""
        Descriptive human readable name of this repo provider.
        """
    )

    spec = Unicode(
        None,
        allow_none=True,
        help="""
        The spec for this builder to parse
        """
    )

    @gen.coroutine
    def get_resolved_ref(self):
        raise NotImplementedError("Must be overridden in child class")

    def get_repo_url(self):
        raise NotImplementedError("Must be overridden in the child class")

    def get_build_slug(self):
        raise NotImplementedError("Must be overriden in the child class")

class GitHubRepoProvider(RepoProvider):
    name = Unicode('GitHub')

    username = Unicode(
        None,
        allow_none=True,
        config=True,
        help="""
        The GitHub user name to use when making GitHub API calls.

        Set to None to not use authenticated API calls
        """
    )

    password = Unicode(
        None,
        allow_none=True,
        config=True,
        help="""
        The password to use to make GitHub API calls.

        Don't use an *actual* password - create a personal access token and use that!
        """
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        spec_parts = self.spec.split('/')
        if len(spec_parts) != 3:
            raise ValueError('Spec is not of form username/repo/branch, provided {spec}'.format(spec=spec))

        self.user, self.repo, self.unresolved_ref = spec_parts
        if self.repo.endswith('.git'):
            self.repo = self.repo[:len(self.repo) - 4]

    def get_repo_url(self):
        return "https://github.com/{user}/{repo}.git".format(user=self.user, repo=self.repo)

    @gen.coroutine
    def get_resolved_ref(self):
        if hasattr(self, 'resolved_ref'):
            return self.resolved_ref

        client = AsyncHTTPClient()
        api_url = "https://api.github.com/repos/{user}/{repo}/commits/{ref}".format(
            user=self.user, repo=self.repo, ref=self.unresolved_ref
        )
        print(api_url)

        if self.username and self.password:
            auth = {
                'auth_username': self.username,
                'auth_password': self.password
            }
        else:
            auth = {}

        try:
            resp = yield client.fetch(api_url, user_agent="BinderHub", **auth)
        except HTTPError as e:
            if e.code == 404:
                return None
            else:
                raise

        ref_info = json.loads(resp.body.decode('utf-8'))
        if 'sha' not in ref_info:
            # TODO: Figure out if we should raise an exception instead?
            return None
        self.resolved_ref = ref_info['sha']
        return self.resolved_ref


    def get_build_slug(self):
        return '{user}-{repo}'.format(user=self.user, repo=self.repo)
