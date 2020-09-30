Enabling CORS
=============

Cross-Origin Resource Sharing (CORS) is a mechanism that gives a 
web application running at one origin, access to resources from a 
different origin. For security reasons, browsers restrict these 
"cross-origin" requests by default.

In the context of a BinderHub deployment, CORS is relevant when you
wish to leverage binder as a computing backend for a web application 
hosted at some other domain. For example, the amazing libraries 
`Juniper <https://github.com/ines/juniper>`_ and 
`Thebe <https://github.com/executablebooks/thebe>`_ leverage binder as 
a computing backend to facilitate live, interactive coding, directly 
within a static HTML webpage. For this functionality, CORS must be 
enabled.

Adjusting BinderHub config to enable CORS
-----------------------------------------

As mentioned above, for security reasons, CORS is not enabled by 
default for BinderHub deployments. To enable CORS we need to add 
additional HTTP headers to allow our BinderHub deployment to be 
accessed from a different origin. This is as simple as adding the 
following to your ``config.yaml``:

.. code:: yaml
  
    cors: &cors
      allowOrigin: '*'

    jupyterhub:
      custom:
        cors: *cors

For example, if you're following on from the previous section 
:doc:`../https`, your ``config.yaml`` might look like this:

.. code:: yaml
  
    config:
      BinderHub:
        hub_url: https://<jupyterhub-URL> # e.g. https://hub.binder.example.com
    
    cors: &cors
      allowOrigin: '*'

    jupyterhub:
      custom:
        cors: *cors
      ingress:
        enabled: true
        hosts:
          - <jupyterhub-URL> # e.g. hub.binder.example.com
        annotations:
          kubernetes.io/ingress.class: nginx
          kubernetes.io/tls-acme: "true"
          cert-manager.io/issuer: letsencrypt-production
          https:
            enabled: true
            type: nginx
        tls:
          - secretName: <jupyterhub-URL-with-dashes-instead-of-dots>-tls # e.g. hub-binder-example-com-tls
            hosts:
              - <jupyterhub-URL> # e.g. hub.binder.example.com

    ingress:
      enabled: true
      hosts:
        - <binderhub-URL> # e.g. binder.example.com
      annotations:
        kubernetes.io/ingress.class: nginx
        kubernetes.io/tls-acme: "true"
        cert-manager.io/issuer: letsencrypt-production
        https:
          enabled: true
          type: nginx
      tls:
        - secretName: <binderhub-URL-with-dashes-instead-of-dots>-tls  # e.g. binder-example-com-tls
          hosts:
            - <binderhub-URL> # e.g. binder.example.com

Once you've adjusted ``config.yaml`` to enable CORS, apply your changes 
with::

    helm upgrade <namespace> jupyterhub/binderhub --version=<version>  -f secret.yaml -f config.yaml

It may take ~10 minutes for the changes to take effect.
