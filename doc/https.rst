Secure with HTTPS
=================

To enable HTTPS on your BinderHub you can setup an ingress proxy and configure
it to serve both, the Binder and JupyterHub interface, using TLS. You can
either manually provide TLS certificates or use
`Let's Encrypt <https://letsencrypt.org/>`_ to automatically get signed
certificates.

Setup IP & domain
-----------------

1. Get a static IP(v4) address that you will assign to your ingress proxy
   later. For example, on Google Cloud this can be done using
   ``gcloud compute addresses create <alias-name-for-ip> --region <region>``
   and retrieve the assigned IP using ``gcloud compute addresses list``.
2. Buy a domain name from a registrar. Pick whichever one you want.
3. Set A records to your above retrieved external IP, one for Binder and
   one for JupyterHub. We need two distinct subdomains for the routing to
   the two different services as they will be served by the same ingress proxy.
   We suggest you use ``hub.binder.`` for JupyterHub and ``binder.`` for your
   BinderHub. Once you are done your BinderHub will be available at
   ``https://binder.``.
4. Wait some minutes for the DNS A records to propagate.

cert-manager for automatic TLS certificate provisioning
-------------------------------------------------------

To automatically generate TLS certificates and sign them using
`Let's Encrypt <https://letsencrypt.org/>`_, we utilise
`cert-manager <https://github.com/jetstack/cert-manager>`_.
Installation is done by using the following command:

.. code::

    kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v0.11.0/cert-manager.yaml

For installations of Kubernetes v1.15 or below, you also need to supply
``--validate=false`` to the above command. For more detail on this, see
the `Getting Started guide <https://docs.cert-manager.io/en/latest/getting-started/install/kubernetes.html>`_.

We then need to create an issuer that will contact Let's Encrypt for signing
our certificates. Use the following template to create a new file
``binderhub-issuer.yaml`` and instantiate it using
``kubectl apply -f binderhub-issuer.yaml``.

.. code:: yaml

    apiVersion: cert-manager.io/v1alpha2
    kind: Issuer
    metadata:
      name: letsencrypt-production
      namespace: <same-namespace-as-binderhub>
    spec:
      acme:
        # You must replace this email address with your own.
        # Let's Encrypt will use this to contact you about expiring
        # certificates, and issues related to your account.
        email: <your-contact-mail>
        server: https://acme-v02.api.letsencrypt.org/directory
        privateKeySecretRef:
          # Secret resource used to store the account's private key.
          name: letsencrypt-production
        solvers:
        - http01:
            ingress:
              class: nginx

See the documentation for `more details on configuring the issuer <https://docs.cert-manager.io/en/latest/tasks/issuers/setup-acme/index.html>`_.

Ingress proxy using nginx
-------------------------

We will use the `nginx ingress controller <https://github.com/kubernetes/ingress-nginx>`_
to proxy the TLS connection to our BinderHub setup. This will run using
the static IP we have acquired before. We therefore create a new configuration
file ``nginx-ingress.yaml``:

.. code:: yaml

    controller:
      service:
        loadBalancerIP: <STATIC-IP>

Afterwards we install the ingress proxy using
``helm install stable/nginx-ingress --name binderhub-proxy --namespace <same-namespace-as-binderhub> -f nginx-ingress.yaml``.
Then wait until it is ready and showing the correct IP when looking at the output of
``kubectl --namespace <same-namespace-as-binderhub> get services binderhub-proxy-nginx-ingress-controller``.

Adjust BinderHub config to serve via HTTPS
------------------------------------------

With the static IP, DNS records and ingress proxy setup, we can now change our
BinderHub configuration to serve traffic via HTTPS. Therefore adjust your ``config.yaml``
with the following sections and apply it using ``helm upgrade ...``.

.. code:: yaml

    config:
      BinderHub:
        hub_url: https://<jupyterhub-URL>
    service:
      type: ClusterIP

    jupyterhub:
      proxy:
        service:
          type: ClusterIP
      ingress:
        enabled: true
        hosts:
          - <jupyterhub-URL>
        annotations:
          kubernetes.io/ingress.class: nginx
          kubernetes.io/tls-acme: "true"
          cert-manager.io/issuer: letsencrypt-production
          https:
            enabled: true
            type: nginx
        tls:
           - secretName: <jupyterhub-URL-with-dashes-instead-of-dots>-tls
             hosts:
              - <jupyterhub-URL>

    ingress:
      enabled: true
      hosts:
         - <binderhub-URL>
      annotations:
        kubernetes.io/ingress.class: nginx
        kubernetes.io/tls-acme: "true"
        cert-manager.io/issuer: letsencrypt-production
        https:
          enabled: true
          type: nginx
      tls:
        - secretName: <binderhub-URL-with-dashes-instead-of-dots>-tls
          hosts:
            - <binderhub-URL>

Once the ``helm upgrade ...`` command has been run, it may take up to
10 minutes until the certificates are issued. You can check their status using
``kubectl describe certificate --namespace <binderhub-namespace> <binderhub-URL>-tls``.
