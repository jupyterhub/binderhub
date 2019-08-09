from unittest import TestCase

from urllib.parse import quote
import pytest
from tornado.ioloop import IOLoop

from binderhub.repoproviders import (
    tokenize_spec, strip_suffix, GitHubRepoProvider, GitRepoProvider,
    GitLabRepoProvider, GistRepoProvider, ZenodoProvider
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


async def test_zenodo():
    spec = '10.5281/zenodo.3242074'

    provider = ZenodoProvider(spec=spec)

    # have to resolve the ref first
    ref = await provider.get_resolved_ref()
    assert ref == '3242074'

    slug = provider.get_build_slug()
    assert slug == 'zenodo-3242074'
    repo_url = provider.get_repo_url()
    assert repo_url == spec


@pytest.mark.github_api
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


def test_higher_quota():
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        high_quota_specs=[
            '^yuvipanda.*'
        ]
    )
    assert not provider.has_higher_quota()

def test_custom_config():
    base_config = {
        "pattern": '^jupyterhub.*',
        "config": {
            "key1": "val1",
            "quota": 999
        }
    }
    settings = {"per_repo_quota": 10}

    # If the spec matches nothing, we should just keep defaults
    provider = GitHubRepoProvider(
        spec='totallynotjupyterhub/zero-to-jupyterhub-k8s/v0.4',
        spec_config=[base_config]
    )
    assert provider.repo_config(settings)['quota'] == 10

    # Updating should happen w/ the base config
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        spec_config=[base_config]
    )
    assert provider.repo_config(settings)['key1'] == "val1"
    assert provider.repo_config(settings)['quota'] == 999

    # Not giving a string for the pattern should raise an error
    config_err_pattern = base_config.copy()
    config_err_pattern['pattern'] = 100
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        spec_config=[config_err_pattern]
    )
    with pytest.raises(ValueError):
        provider.repo_config(settings)

    # Not giving a dictionary for configuration should raise an error
    config_err_config = base_config.copy()
    config_err_config['config'] = "not a dictionary"
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        spec_config=[config_err_config]
    )
    with pytest.raises(ValueError):
        provider.repo_config(settings)

    # Not providing one of `pattern` or `config` should raise an error
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        spec_config=[base_config, {"pattern": "mypattern"}]
    )
    with pytest.raises(ValueError):
        provider.repo_config(settings)

    # Two regexes that both match should result in the *last* one being in the config
    base_config_second = {
        "pattern": '^jupyterh.*',
        "config": {
            "key1": "newvalue",
        }
    }
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        spec_config=[base_config, base_config_second]
    )
    assert provider.repo_config(settings)['key1'] == "newvalue"
    assert provider.repo_config(settings)['quota'] == 999



def test_not_higher_quota():
    provider = GitHubRepoProvider(
        spec='jupyterhub/zero-to-jupyterhub-k8s/v0.4',
        high_quota_specs=[
            '^jupyterhub.*'
        ]
    )
    assert provider.has_higher_quota()


@pytest.mark.parametrize('ban_spec', ['.*ddEEff.*', '.*ddEEFF.*'])
def test_ban_is_case_insensitive(ban_spec):
    provider = GitHubRepoProvider(
        spec='AABBCcc/DDeeFF/v0.4',
        banned_specs=[ban_spec]
    )
    assert provider.is_banned()


@pytest.mark.github_api
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


@pytest.mark.parametrize('url,unresolved_ref,resolved_ref', [
    ['https://github.com/jupyterhub/zero-to-jupyterhub-k8s', 
     'f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603',
     'f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603'],
    ['https://github.com/jupyterhub/zero-to-jupyterhub-k8s', 
     '0.8.0',
     'ada2170a2181ae1760d85eab74e5264d0c6bb67f']
])
def test_git_ref(url, unresolved_ref, resolved_ref):
    spec = '{}/{}'.format(
        quote(url, safe=''),
        quote(unresolved_ref)
    )

    provider = GitRepoProvider(spec=spec)
    slug = provider.get_build_slug()
    assert slug == url
    full_url = provider.get_repo_url()
    assert full_url == url
    ref = IOLoop().run_sync(provider.get_resolved_ref)
    assert ref == resolved_ref


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


@pytest.mark.github_api
def test_gist_ref():
    spec = '{}/{}'.format('mariusvniekerk', '8a658f7f63b13768d1e75fa2464f5092')

    provider = GistRepoProvider(spec=spec)
    slug = provider.get_build_slug()
    assert slug == '8a658f7f63b13768d1e75fa2464f5092'
    full_url = provider.get_repo_url()
    assert full_url == 'https://gist.github.com/mariusvniekerk/8a658f7f63b13768d1e75fa2464f5092.git'
    ref = IOLoop().run_sync(provider.get_resolved_ref)
    assert ref == '7daa381aae8409bfe28193e2ed8f767c26371237'


@pytest.mark.github_api
def test_gist_secret():
    spec = '{}/{}'.format('mariusvniekerk', 'bd01411ea4bf4eb8135893ef237398ba')

    provider = GistRepoProvider(spec=spec)
    with pytest.raises(ValueError):
        IOLoop().run_sync(provider.get_resolved_ref)

    provider = GistRepoProvider(spec=spec, allow_secret_gist=True)
    assert IOLoop().run_sync(provider.get_resolved_ref) is not None
