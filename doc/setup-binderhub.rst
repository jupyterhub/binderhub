Set up BinderHub
================

.. note::

   If you wish to use encryption with ``letsencrypt``, BinderHub requires
   that you configure the DNS of a web address to point to the BinderHub IP
   address. This means that you need to have control over a URL such as
   ``www.mydomain.com``.

Download the Helm Chart and deployment repo for BinderHub
---------------------------------------------------------

BinderHub uses Helm Charts to set up the applications we'll use in our Binder
deployment. If you're curious about what Helm Charts are and how they're
used here, see the `Zero to JupyterHub guide
<https://zero-to-jupyterhub.readthedocs.io/en/latest/tools.html#helm>`_.

First grab the latest helm chart for BinderHub and install it.::

    helm repo add jupyterhub https://jupyterhub.github.io/helm-chart
    helm install --name binder jupyterhub/binderhub --version v0.1.0-464c4f5


Configure DNS
-------------

Next we'll configure our web address to point to the IP address for our
BinderHub.

Find the ``EXTERNAL-IP`` of the **nginx-ingress-controller**::

    kubectl --namespace=support get svc support-nginx-ingress-controller

Make DNS records for both binder and jupyterhub that point to that IP. For
example, make both::

   hub.mydomain.com
   binder.mydomain.com

point to the same ``EXTERNAL-IP`` address of the ingress controller.

.. note::

   When you configure the helm chart, you will add the DNS entry for binder and
   jupyterhub in the ``config.yaml`` file.


Configure the Helm Chart
------------------------

First create a file called ``secret.yaml``. In it, put the following code::

    jupyterhub:
      hub:
        cookieSecret: "<openssl rand -hex 32>"
      proxy:
        secretToken: "<openssl rand -hex 32>"
    registry:
      password: |
        <the json file from Service Accounts>
    hub:
      services:
        binder:
          apiToken: "<openssl rand -hex 32>"

.. tip::

   Don't forget the `|` after the ``password:`` label.

.. tip::

   For more information on getting a registry password, see
   `setup-registry`_.

Next, create a file called ``config.yaml``. In it, put the following code::

    registry:
      # Note this is project *ID*, not just project
      #
      # `<prefix>` can be any string and will be appended to image names
      # e.g., `dev` and `prod`.
      prefix:  gcr.io/<google-project-id>/<prefix>

    hub:
      # This is the DNS that you've configured. E.g. `beta.mybinder.org`
      # Note that there is `http://` here
      url: http://<dns-entry-for-jupyterhub>

    ingress:
      enabled: true
      # But no `http://` here
      host: <dns-entry-for-binder>

    jupyterhub:
      ingress:
        enabled: true
        # But no `http://` here
        host: <dns-entry-for-jupyterhub>

Now that BinderHub is properly configured, it's time to :doc:`deploy`.
