.. _use-docker-hub:

Use ``Docker Hub`` as registry
==============================

To use **Docker Hub** as registry first you have to create a
`Docker ID account <https://docs.docker.com/docker-id/>`_
in `Docker Hub <https://hub.docker.com/>`_.
Docker ID (username) and password are used to push Docker images to the registry.

If you want to store Docker images under an organisation, you can
`create an organization <https://docs.docker.com/docker-hub/orgs/>`_.
This is useful if different Binder instances want to use same registry to store images.

Configuration
-------------

Update ``secret.yaml`` by entering the following::

  registry:
    username: <docker-id>
    password: <password>

.. note::

   * **``<docker-id>``** and **``<password>``** are your credentials to login to Docker Hub.
     If you use an organisation to store your Docker images, this account must be a member of it.

Update ``config.yaml`` by entering the following::

  registry:
    enabled: true
    prefix: <docker-id/organization-name>/<prefix>
    host: https://registry.hub.docker.com
    authHost: https://index.docker.io/v1
    authTokenUrl: https://auth.docker.io/token?service=registry.docker.io

.. note::

   * **``<docker-id/organization-name>``** is where you want to store Docker images.
     This can be your Docker ID account or an organization that your account belongs to.
   * **``<prefix>``** can be any string, and will be prepended to image names. We
     recommend something descriptive such as ``binder-dev`` or ``binder-prod``.
