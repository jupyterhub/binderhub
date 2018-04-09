from unittest import TestCase

from urllib.parse import quote
import pytest
from tornado.ioloop import IOLoop

from binderhub.repoproviders import (
    tokenize_spec, strip_suffix, GitHubRepoProvider, GitRepoProvider, GitLabRepoProvider, GistRepoProvider
)


# General string processing
@pytest.mark.parametrize(
    'raw_text, suffix, clean_text', [
        ("foo.git", ".git", "foo"),
        ("foo.bar", ".git", "foo.bar"),
        ("foo.bar", ".bar", "foo")
    ]
)
def test_string_strip(raw_text, suffix, clean_text):
    assert strip_suffix(raw_text, suffix) == clean_text


# user/repo/reference
@pytest.mark.parametrize(
    'spec, raw_user, raw_repo, raw_ref', [
        ("user/repo/master", "user", "repo", "master"),
        ("user/repo/hotfix/squash-bug", "user", "repo", "hotfix/squash-bug"),
        ("user/repo/feature/save_world", "user", "repo", "feature/save_world")
    ]
)
def test_spec_processing(spec, raw_user, raw_repo, raw_ref):
    user, repo, unresolved_ref = tokenize_spec(spec)
    assert raw_user == user
    assert raw_repo == repo
    assert raw_ref == unresolved_ref


def test_github_ref():
    provider = GitHubRepoProvider(spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4')
    slug = provider.get_build_slug()
    assert slug == 'jupyterhub-zero-to-jupyterhub-k8s'
    full_url = provider.get_repo_url()
    assert full_url == 'https://github.com/jupyterhub/zero-to-jupyterhub-k8s'
    ref = IOLoop().run_sync(provider.get_resolved_ref)
    assert ref == 'f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603'


def test_not_banned():
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        banned_specs=[
            '^yuvipanda.*'
        ]
    )
    assert not provider.is_banned()


def test_banned():
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        banned_specs=[
            '^jupyterhub.*'
        ]
    )
    assert provider.is_banned()


@pytest.mark.parametrize('ban_spec', ['.*ddEEff.*', '.*ddEEFF.*'])
def test_ban_is_case_insensitive(ban_spec):
    provider = GitHubRepoProvider(
        spec='AABBCcc/DDeeFF/v0.4',
        banned_specs=[ban_spec]
    )
    assert provider.is_banned()


def test_github_missing_ref():
    provider = GitHubRepoProvider(spec='jupyterhub/zero-to-jupyterhub-k8s/v0.1.2.3.4.5.6')
    ref = IOLoop().run_sync(provider.get_resolved_ref)
    assert ref is None


class TestSpecErrorHandling(TestCase):

    def test_too_short_spec(self):
        spec = "nothing_to_split"
        with self.assertRaisesRegexp(ValueError, "Spec is not of the form"):
            user, repo, unresolved_ref = tokenize_spec(spec)

    def test_long_spec(self):
        # No specification is too long, extra slashes go to the "ref" property
        spec = "a/long/specification/with/many/slashes/to/split/on"
        spec_parts = tokenize_spec(spec)
        assert len(spec_parts) == 3

    def test_spec_with_no_suggestion(self):
        spec = "short/master"
        error = "^((?!Did you mean).)*$".format(spec)  # negative match
        with self.assertRaisesRegexp(ValueError, error):
            user, repo, unresolved_ref = tokenize_spec(spec)

    def test_spec_with_suggestion(self):
        spec = "short/suggestion"
        error = "Did you mean \"{}/master\"?".format(spec)
        with self.assertRaisesRegexp(ValueError, error):
            user, repo, unresolved_ref = tokenize_spec(spec)


def test_git_ref():
    spec = '{}/{}'.format(
        quote('https://github.com/jupyterhub/zero-to-jupyterhub-k8s', safe=''),
        quote('f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603')
    )

    provider = GitRepoProvider(spec=spec)
    slug = provider.get_build_slug()
    assert slug == 'https://github.com/jupyterhub/zero-to-jupyterhub-k8s'
    full_url = provider.get_repo_url()
    assert full_url == 'https://github.com/jupyterhub/zero-to-jupyterhub-k8s'
    ref = IOLoop().run_sync(provider.get_resolved_ref)
    assert ref == 'f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603'


def test_gitlab_ref():
    spec = '{}/{}'.format(
        quote('gitlab-org/gitlab-ce', safe=''),
        quote('v10.0.6')
    )
    provider = GitLabRepoProvider(spec=spec)
    slug = provider.get_build_slug()
    assert slug == 'gitlab_-org-gitlab_-ce'
    full_url = provider.get_repo_url()
    assert full_url == 'https://gitlab.com/gitlab-org/gitlab-ce.git'
    ref = IOLoop().run_sync(provider.get_resolved_ref)
    assert ref == 'b3344b7f17c335a817c5d7608c5e47fd7cabc023'


def test_gist_ref():
    spec = '{}/{}'.format('mariusvniekerk', '8a658f7f63b13768d1e75fa2464f5092')

    provider = GistRepoProvider(spec=spec)
    slug = provider.get_build_slug()
    assert slug == '8a658f7f63b13768d1e75fa2464f5092'
    full_url = provider.get_repo_url()
    assert full_url == 'https://gist.github.com/8a658f7f63b13768d1e75fa2464f5092.git'
    ref = IOLoop().run_sync(provider.get_resolved_ref)
    assert ref == '7daa381aae8409bfe28193e2ed8f767c26371237'


def test_gist_secret():
    spec = '{}/{}'.format('mariusvniekerk', 'bd01411ea4bf4eb8135893ef237398ba')

    provider = GistRepoProvider(spec=spec)
    with pytest.raises(ValueError):
        IOLoop().run_sync(provider.get_resolved_ref)

    provider = GistRepoProvider(spec=spec, allow_secret_gist=True)
    assert IOLoop().run_sync(provider.get_resolved_ref) is not None
