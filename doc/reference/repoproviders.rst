.. _api-repoproviders:

repoproviders
=============

Module: :mod:`binderhub.repoproviders`
--------------------------------------

.. automodule:: binderhub.repoproviders

.. currentmodule:: binderhub.repoproviders

:class:`RepoProvider`
---------------------

A generic repository provider class.

.. autoconfigurable:: RepoProvider
    :members:


:class:`GitHubRepoProvider`
---------------------------

`GitHub <https://github.com/>`_ is a website for hosting and sharing git repositories.

.. autoconfigurable:: GitHubRepoProvider
    :members:


:class:`GitLabRepoProvider`
---------------------------

`GitLab <https://https://about.gitlab.com/>`_ offers hosted as well as self-hosted git
repositories.

.. autoconfigurable:: GitLabRepoProvider
    :members:


:class:`GistRepoProvider`
---------------------------

`Gists <https://gist.github.com/>`_ are small collections of files stored on GitHub. They
behave like lightweight repositories.

.. autoconfigurable:: GistRepoProvider
    :members:


:class:`ZenodoProvider`
---------------------------

`Zenodo <https://zenodo.org/>`_ is a non-profit provider of scholarly artifacts
(such as code repositories) run in partnership with CERN.

.. autoconfigurable:: ZenodoProvider
    :members:


:class:`FigshareProvider`
---------------------------

`FigShare <https://figshare.com/>`_ is company that offers hosting for scholarly
artifacts (such as code repositories).

.. autoconfigurable:: FigshareProvider
    :members:


:class:`GitRepoProvider`
---------------------------

A generic repository provider for URLs that point directly to a git repository.

.. autoconfigurable:: GitRepoProvider
    :members:
