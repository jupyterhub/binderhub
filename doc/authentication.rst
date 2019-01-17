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

      hub:
        services:
          binder:
            oauth_redirect_uri: "<binderhub_url>/oauth_callback"
            oauth_client_id: "binder-oauth-client-test"
        extraConfig:
          binder: |
            from kubespawner import KubeSpawner

            class BinderSpawner(KubeSpawner):
              def start(self):
                  if 'image' in self.user_options:
                    # binder service sets the image spec via user options
                    self.image_spec = self.user_options['image']
                  return super().start()
            c.JupyterHub.spawner_class = BinderSpawner

      singleuser:
        # to make notebook servers aware of hub
        cmd: jupyterhub-singleuser

      auth: {}

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

    config:
      BinderHub:
        use_named_servers: true
    jupyterhub:
      hub:
        allowNamedServers: true

.. note::
    BinderHub assigns a unique name to each server with max 40 characters.
