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

    @gen.coroutine
    def resolve_spec(self, spec):
        """
        Takes a spec of build parameters and parses it into info we can use.

        Should return a dict with at least 3 options:
           - repo: URL to git repo that can be passed to 'git clone'
           - ref: The git ref to check out before building
           - repo_build_slug: A build slug that together with the ref can be used to fully
                              specify this particular repository. Used in image and build names.
        """
        raise NotImplementedError('Must implement this in a subclass ')


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

    @gen.coroutine
    def resolve_spec(self, spec):
        """
        Parses a URL spec and returns a git URL + ref to check out
        """
        # We want spec to be user/repo/branch
        spec_parts = spec.split('/')
        if len(spec_parts) != 3:
            raise ValueError('Spec is not of form username/repo/branch')

        user, repo, ref = spec_parts

        repo_url = "https://github.com/{user}/{repo}.git".format(user=user, repo=repo)

        client = AsyncHTTPClient()
        api_url = "https://api.github.com/repos/{user}/{repo}/commits/{ref}".format(
            user=user, repo=repo, ref=ref
        )

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
            return None

        ref = ref_info['sha']

        repo_build_slug = '{user}-{repo}'.format(
            user=user, repo=repo
        )

        return {
            'repo': repo_url,
            'ref': ref_info['sha'],
            'repo_build_slug': repo_build_slug
        }
