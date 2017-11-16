Debugging BinderHub
===================

If BinderHub isn't behaving as you'd expect, you'll need to debug your
kubernetes deployment of the JupyterHub and BinderHub services. For a
guide on how to debug in Kubernetes, see the `Zero to JupyterHub debugging
guide <https://zero-to-jupyterhub.readthedocs.io/en/latest/debug.html>`_.

Changing the helm chart
-----------------------
If you make changes to your Helm Chart (e.g., while debugging), you should
run an upgrade on your Kubernetes deployment like so::

     helm upgrade binder jupyterhub/binderhub --version=v0.1.0-397eb59 -f secret.yaml -f config.yaml
