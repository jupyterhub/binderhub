Customizing your BinderHub deployment
=====================================

JupyterHub customization
------------------------

Because BinderHub uses JupyterHub to manage all user sessions, you can
customize many aspects of the resources available to the user. This is
primarily done by modifications to your BinderHub's Helm chart (``config.yaml``).

To make edits to your JupyterHub deplyoment via ``config.yaml``, use
the following pattern::

  binderhub:
     jupyterhub:
        <JUPYTERHUB-CONFIG-YAML>

For example, see `this section of the mybinder.org Helm Chart
<https://github.com/jupyterhub/mybinder.org-deploy/blob/a7d83838aea24a4f143a2b8630f4347fa722a6b3/mybinder/values.yaml#L192>`_.

For information on how to configure your JupyterHub deployment, see the
`JupyterHub for Kubernetes Customization Guide
<https://zero-to-jupyterhub.readthedocs.io/en/latest/#customization-guide>`_.

If you want to customise the spawner you can subclass it in ``extraConfig``.
For example::

  binderhub:
    jupyterhub:
      hub:
        extraConfig:
          10-binder-customisations: |
            class MyCustomBinderSpawner(BinderSpawner):
                ...

            c.JupyterHub.spawner_class = MyCustomBinderSpawner

BinderHub uses the `jupyterhub.hub.extraConfig setting
<https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/advanced.html#hub-extraconfig>`_
to customise JupyterHub.
For example, ``BinderSpawner`` is defined under the ``00-binder`` key.
Keys are evaluated in alphanumeric order, so later keys such as
``10-binder-customisations`` can use objects defined in earlier keys.

About page customization
------------------------

BinderHub serves a simple about page at ``https://BINDERHOST/about``. By default
this shows the version of BinderHub you are running. You can add additional
HTML to the page by setting the ``c.BinderHub.about_message`` configuration
option to the raw HTML you would like to add. You can use this to display
contact information or other details about your deployment.

.. _repo-specific-config:

Custom configuration for specific repositories
----------------------------------------------

Sometimes you would like to provide a repository-specific configuration.
For example, if you'd like certain repositories to have **higher pod quotas**
than others, or if you'd like to provide certain resources to a subset of
repositories.

To override the configuration for a specific repository, you can provide
a list of dictionaries that allow you to provide a pattern to match against
each repository's specification, and override configuration values for any
repositories that match this pattern.

.. note::

   If you provide **multiple patterns that match a single repository** in your
   spec-specific configuration, then **later values in the list will override
   earlier values**.

To define this list of patterns and configuration overrides, use the
following pattern in your Helm Chart (here we show an example using
``GitHubRepoProvider``, but this works for other RepoProviders as well):

.. code-block:: yaml

   config:
       GitHubRepoProvider:
         spec_config:
           - pattern: ^ines/spacy-binder.*:
             config:
                key1: value1
           - pattern: pattern2
             config:
                key1: othervalue1
                key2: othervalue2

For example, the following specification configuration will assign a
pod quota of 999 to the spacy-binder repository, and a pod quota
of 1337 to any repository in the JupyterHub organization.

.. code-block:: yaml

   config:
       GitHubRepoProvider:
         spec_config:
           - pattern: ^ines/spacy-binder.*:
             config:
                quota: 999
           - pattern: ^jupyterhub.*
             config:
                quota: 1337


Banning specific repositories
----------------------------------------------

You may want to exclude certain repositories from your BinderHub instance.
You can do this by providing a list of **banned_spec** patterns.
BinderHub will not accept URLs matching any of the banned patterns.

For example, the following configuration will prevent notebooks in the spacy-binder
repository and the ml-training repository from launching.

.. code-block:: yaml

   config:
     GitHubRepoProvider:
       # Add banned repositories to the list below
       # They should be strings that will match "^<org-name>/<repo-name>.*"
       banned_specs:
         - ^ines/spacy-binder.*
         - ^aschen/ml-training.*

You can also use a negative lookahead. For example, the following configuration will
prevent all notebooks except those in repositories in the myorg organization from launching.

.. code-block:: yaml

   config:
     GitHubRepoProvider:
       banned_specs:
         - ^(?!myorg\/.*).*$
