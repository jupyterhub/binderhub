Enabling Authentication
=======================

By default BinderHub runs without authentication and
for each launch it creates a temporary user and starts a server for that user.

In order to enable authentication for BinderHub by using JupyterHub as an oauth provider,
you need to add the following into ``config.yaml``:

.. code:: yaml

    config:
      BinderHub:
        auth_enabled: true

    jupyterhub:
      cull:
        # don't cull authenticated users
        users: False
      custom:
        binderauth_enabled: true
      hub:
        redirectToServer: false
        services:
          binder:
            oauth_no_confirm: true
            oauth_redirect_uri: "http://<binderhub_url>/oauth_callback"
            oauth_client_id: "binder-oauth-client-test"

      singleuser:
        # to make notebook servers aware of hub
        cmd: jupyterhub-singleuser

      auth: {}

If the configuration above was entered correctly, once you upgrade your
BinderHub Helm Chart with ``helm upgrade...``, users that arrive at your
BinderHub URL will be directed to a login page. Once they enter their
credentials, they'll be taken to the typical BinderHub landing page.

.. note::

   If users *don't* go to a BinderHub landing page after they log-in,
   then the configuration above is probably incorrect. Double-check that
   the BinderHub configuration (and the JupyterHub authentication configuration)
   look good.
.. note::
    For ``jupyterhub.auth`` you should use config of your authenticator.
    For more information you can check
    `the Authentication guide
    <https://zero-to-jupyterhub.readthedocs.io/en/stable/authentication.html>`_.

.. warning::
    ``jupyterhub-singleuser`` requires ``JupyterHub`` to be installed in user server images.
    Therefore ensure that you use at least ``jupyter/repo2docker:ccce3fe`` image
    to build user images. Because ``repo2docker`` installs ``JupyterHub`` by default after that.

Authentication with named servers
---------------------------------

With above configuration Binderhub limits each authenticated user to start one server at a time.
When a user already has a running server, BinderHub displays an error message.

If you want to have users be able to launch multiple servers at the same time,
you have to enable named servers on JupyterHub:

.. code:: yaml

    jupyterhub:
      hub:
        allowNamedServers: true
        # change this value as you wish,
        # or remove this line if you don't want to have any limit
        namedServerLimitPerUser: 5

.. note::
    BinderHub assigns a unique name to each server with max 40 characters.
