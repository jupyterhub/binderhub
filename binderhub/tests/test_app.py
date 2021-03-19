"""Exercise the binderhub entrypoint"""

from subprocess import check_output
import sys
import pytest

from traitlets import TraitError

from binderhub.app import BinderHub
from binderhub.repoproviders import (RepoProvider, GitLabRepoProvider, GitHubRepoProvider)


def test_help():
    check_output([sys.executable, '-m', 'binderhub', '-h'])

def test_help_all():
    check_output([sys.executable, '-m', 'binderhub', '--help-all'])

def test_repo_providers():
    # Check that repo_providers property is validated by traitlets.validate

    b = BinderHub()

    class Provider(RepoProvider):
        pass

    # Setting providers that inherit from 'RepoProvider` should be allowed
    b.repo_providers = dict(gh=GitHubRepoProvider, gl=GitLabRepoProvider)
    b.repo_providers = dict(p=Provider)

    class BadProvider():
        pass

    # Setting providers that don't inherit from 'RepoProvider` should raise an error
    wrong_repo_providers = [GitHubRepoProvider, {}, 'GitHub', BadProvider]
    for repo_providers in wrong_repo_providers:
        with pytest.raises(TraitError):
            b.repo_providers = repo_providers
