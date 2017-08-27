"""
Classes for Repo providers

Subclass the base class, ``RepoProvider``, to support different version
control services and providers.

"""
import json

from tornado import gen, web
from tornado.httpclient import AsyncHTTPClient, HTTPError
from traitlets import Unicode
from traitlets.config import LoggingConfigurable


class RepoProvider(LoggingConfigurable):
    """Base class for a repo provider"""
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
    """Repo provider for the GitHub service"""
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
            msg = 'Spec is not of the form "user/repo/ref", provided: "{spec}".'.format(spec=self.spec)
            if len(spec_parts) == 2 and spec_parts[-1] != 'master':
                msg += ' Did you mean "{spec}/master"?'.format(spec=self.spec)
            raise ValueError(msg)

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
