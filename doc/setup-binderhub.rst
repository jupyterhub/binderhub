Set up BinderHub
================

Download the Helm Chart and deployment repo for BinderHub
---------------------------------------------------------

::

    git clone https://github.com/jupyterhub/helm-chart
    git clone https://github.com/jupyterhub/binderhub-deploy


Install the "support" applications
----------------------------------

::

    cd binderhub-deploy/support
    helm dep up
    cd ..
    cd ..
    helm install --name=support --namespace=support binderhub-deploy/support


Now find the IP of the **nginx-ingress-controller**::

    kubectl --namespace=support get svc support-nginx-ingress-controller

And make DNS records for both binder and jupyterhub that point to that IP.

.. note:: **Set up DNS**

   To use a custom domain name for your binder and jupyterhub,
   you will need a domain name and then set up DNS records for binder and
   jupyterhub. This means you'll need to set up a web address to be accessible
   by your Binder. The process will differ a bit depending on the web host
   you're using.

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
        <the json file from service account>

.. tip::

   Don't forget the `|` after the ``password:`` label.

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
