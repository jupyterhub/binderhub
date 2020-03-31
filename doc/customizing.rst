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
<https://github.com/jupyterhub/mybinder.org-deploy/blob/staging/mybinder/values.yaml#L54>`_.

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

Template customization
----------------------

BinderHub uses `Jinja <http://jinja.pocoo.org/>`_ template engine and
it is possible to customize templates in a BinderHub deployment.
Here it is explained by a minimal example which shows how to use a custom logo.

Before configuring BinderHub to use custom templates and static files,
you have to provide these files to the binder pod where the application runs.
One way to do this using `Init Containers
<https://kubernetes.io/docs/concepts/workloads/pods/init-containers/>`_ and a Git repo.

Firstly assume that you have a Git repo ``binderhub_custom_files`` which holds your custom files::

    binderhub_custom_files/
    ├── static
    │   └── custom_logo.svg
    └── templates
        └── page.html

where ``page.html`` extends the `base page.html
<https://github.com/jupyterhub/binderhub/blob/master/binderhub/templates/page.html>`_ and
updates only the source url of the logo in order to use your custom logo::

    {% extends "templates/page.html" %}

    {% block logo_image %}"{{ EXTRA_STATIC_URL_PREFIX }}custom_logo.svg"{% endblock logo_image %}

.. note::

    If you want to extend `any other base template
    <https://github.com/jupyterhub/binderhub/tree/master/binderhub/templates>`_,
    you have to include ``{% extends "templates/<base_template_name>.html" %}``
    in the beginning of your custom template.
    It is also possible to have completely new template instead of extending the base one.
    Then BinderHub will ignore the base one.

Now you can use ``Init Containers`` to clone that Git repo into a volume (``custom-templates``)
which is mounted to both init container and binder container.
To do that add the following into your ``config.yaml``::

    initContainers:
      - name: git-clone-templates
        image: alpine/git
        args:
          - clone
          - --single-branch
          - --branch=master
          - --depth=1
          - --
          - <repo_url>
          - /etc/binderhub/custom
        securityContext:
          runAsUser: 0
        volumeMounts:
          - name: custom-templates
            mountPath: /etc/binderhub/custom
    extraVolumes:
      - name: custom-templates
        emptyDir: {}
    extraVolumeMounts:
      - name: custom-templates
        mountPath: /etc/binderhub/custom

.. note::

    You have to replace ``<repo_url>`` with the url of the public repo (``binderhub_custom_files``)
    where you have your templates and static files.

The final thing you have to do is to configure BinderHub,
so it knows where to look for custom templates and static files (where the volume is mounted).
To do that update your ``config.yaml`` by the following::

    config:
      BinderHub:
        template_path: /etc/binderhub/custom/templates
        extra_static_path: /etc/binderhub/custom/static
        extra_static_url_prefix: /extra_static/
        template_variables:
            EXTRA_STATIC_URL_PREFIX: "/extra_static/"

.. warning::

    You have to set the ``extra_static_url_prefix`` different than ``/static/``
    which is the default static url prefix of BinderHub.
    Otherwise default one overrides it and BinderHub only uses default static files.

.. note::

    In this example a custom template variable (``EXTRA_STATIC_URL_PREFIX``)
    to hold the value of ``extra_static_url_prefix`` is also defined,
    which was used in custom ``page.html``.
    This is good to do specially if you have many custom templates and static files.

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

Pre-build steps
----------------

A Binder ``build`` refers to the process of creating a virtual environment for a git repository. This operation takes place in a `Kubernetes pod <https://kubernetes.io/docs/concepts/workloads/pods/pod/#what-is-a-pod>`_, where a `repo2docker <https://github.com/jupyter/repo2docker>`_ container does the heavy lifting to create the requested environment. 

If you want the eventual environment to access some additinoal resources without baking them into the built Docker image, you may need to execute some configurations **before** the ``repo2docker`` container is started. In Kubernetes, such priori steps are typically achieved using `init containers <https://kubernetes.io/docs/concepts/workloads/pods/init-containers/>`_.

In the BinderHub configuration, you can specify init containers to run in the build pod before the ``repo2docker`` call via the ``init_container_build`` key.

The `repo2data <https://github.com/SIMEXP/Repo2Data>`_  python package provides a good showcase for the use of ``init_container_build``:

.. code-block:: yaml

    config:
      BinderHub:
        extra_volume_build:
          - name: extra-volume
            hostPath:
              path: /DATA
              type: Directory
        init_container_build:
          - name: init-builder
          image: conpdev/repo2data
          args:
            - -r
            - $(REPO_URL)
          volumeMounts:
            - name: extra-volume
              mountPath: /data

In the configuration above, a ``conpdev/repo2data`` init container is run to:

1. Pull the dataset described by a `data_requirements.json <https://github.com/SIMEXP/Repo2Data#input>`_ to the server 
2. Set necessary configurations to associate the downloaded data with the corresponding user pod. 

Having the dataset available pripor to the user pod running, this approach does not prolong the time for spawning a user session and keeps the Docker images lean. Note that the use of ``init_container_build`` is not exclusive to the data management purposes. Any process that can be defined as a ``init container`` job can be specified before the ``repo2docker`` container is started in the build pod. 

.. note::

    Commits pushed to the user's git repository will trigger ``init_container_build`` runs.
