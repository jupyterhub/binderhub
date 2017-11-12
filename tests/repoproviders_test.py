from unittest import TestCase

import pytest

from binderhub.repoproviders import GitHubRepoProvider


# General string processing
@pytest.mark.parametrize(
    'raw_text, suffix, clean_text', [
        ("foo.git", ".git", "foo"),
        ("foo.bar", ".git", "foo.bar"),
        ("foo.bar", ".bar", "foo")
    ]
)
def test_string_strip(raw_text, suffix, clean_text):
    assert GitHubRepoProvider.strip_suffix(raw_text, suffix) == clean_text


# user/repo/reference
@pytest.mark.parametrize(
    'spec, raw_user, raw_repo, raw_ref', [
        ("user/repo/master", "user", "repo", "master"),
        ("user/repo/hotfix/squash-bug", "user", "repo", "hotfix/squash-bug"),
        ("user/repo/feature/save_world", "user", "repo", "feature/save_world")
    ]
)
def test_spec_processing(spec, raw_user, raw_repo, raw_ref):
    user, repo, unresolved_ref = GitHubRepoProvider.process_spec(spec)
    assert raw_user == user
    assert raw_repo == repo
    assert raw_ref == unresolved_ref


class TestSpecErrorHandling(TestCase):

    def test_too_short_spec(self):
        spec = "nothing_to_split"
        with self.assertRaisesRegexp(ValueError, "Spec is not of the form"):
            user, repo, unresolved_ref = GitHubRepoProvider.process_spec(spec)

    def test_long_spec(self):
        # No specification is too long, extra slashes go to the "ref" property
        spec = "a/long/specification/with/many/slashes/to/split/on"
        spec_parts = GitHubRepoProvider.process_spec(spec)
        assert len(spec_parts) == 3

    def test_spec_with_no_suggestion(self):
        spec = "short/master"
        error = "^((?!Did you mean).)*$".format(spec)  # negative match
        with self.assertRaisesRegexp(ValueError, error):
            user, repo, unresolved_ref = GitHubRepoProvider.process_spec(spec)

    def test_spec_with_suggestion(self):
        spec = "short/suggestion"
        error = "Did you mean \"{}/master\"?".format(spec)
        with self.assertRaisesRegexp(ValueError, error):
            user, repo, unresolved_ref = GitHubRepoProvider.process_spec(spec)
