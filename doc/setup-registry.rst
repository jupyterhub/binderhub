.. _setup-registry:

Set up the container registry
=============================

BinderHub will build Docker images out of Git repositories, and then push
them to a Docker registry so that JupyterHub can launch user servers based
on these images. You can use any registry that
you like, though this guide covers how to properly configure two popular
registries: the **Google Container Registry** (``gcr.io``) and DockerHub
(``hub.docker.com``).

.. _use-gcr:

Set up Google Container Registry
--------------------------------

To use Google Container Registry, you'll need to provide BinderHub
with proper credentials so it can push images. You can do so by creating a
service account that has authorization to push to Google Container Registry:

1. Go to `console.cloud.google.com`_
2. Make sure your project is selected
3. Click ``<top-left menu w/ three horizontal bars> -> IAM & Admin -> Service Accounts`` menu option
4. Click **Create service account**
5. Give your account a descriptive name such as "binderhub-builder"
6. Click ``Role -> Storage -> Storage Admin`` menu option
7. Check **Furnish new private key**
8. Leave key type as default of **JSON**
9. Click **Create**

These steps will download a **JSON file** to your computer. The JSON file
contains the password that can be used to push Docker images to the ``gcr.io``
registry.

.. warning::

   Don't share the contents of this JSON file with anyone. It can be used to
   gain access to your google cloud account!

.. important::

   Make sure to store this JSON file as you cannot generate a second one
   without re-doing the steps above.

.. _use-docker-hub:

Set up Docker Hub registry
------------------------------

To use **Docker Hub** as a registry first you have to create a
`Docker ID account <https://docs.docker.com/docker-id/>`_
in `Docker Hub <https://hub.docker.com/>`_. Your
Docker ID (username) and password are used to push Docker images to the registry.

If you want to store Docker images under an organization, you can
`create an organization <https://docs.docker.com/docker-hub/orgs/>`_.
This is useful if different Binder instances want to use same registry to store images.

See the next section for how to properly configure your BinderHub to use
Docker Hub.

Next step
---------

Now that our cloud resources are set up, it's time to :doc:`setup-binderhub`.

.. _console.cloud.google.com: http://console.cloud.google.com
