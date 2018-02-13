Customizing your BinderHub deployment
=====================================

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
