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
<https://kubernetes.io/docs/concepts/workloads/pods/init-containers/>`_ and a git repo.

Firstly assume that you have a git repo ``binderhub_custom_files`` which holds your custom files::

    binderhub_custom_files/
    ├── static
    │   └── custom_logo.svg
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

Now you can use ``Init Containers`` to clone that git repo into a volume (``custom-templates``)
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
