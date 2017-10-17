BinderHub
=========

.. important::

   BinderHub is under active development and subject to breaking changes.

Getting started
---------------

The primary goal of BinderHub is creating custom computing environments that
can be used by many remote users. BinderHub enables an end user to easily
specify a desired computing environment from a GitHub repo. BinderHub then
serves the custom computing environment at a URL which users can access
remotely.

This guide assists you, an administrator, through the process of setting up
your BinderHub deployment and helps you connect and configure the following
things:

- A **cloud provider** such Google Cloud, Microsoft Azure, Amazon EC2, and
  others
- **Kubernetes** to manage resources on the cloud
- **Helm** to configure and control Kubernetes
- **Docker** to use containers that standardize computing environments
- A **BinderHub UI** that users can access to specify GitHub repos they want
  built
- **BinderHub** to generate Docker images using the URL of a GitHub repository
- A **Docker registry** (such as gcr.io) that hosts container images
- **JupyterHub** to deploy temporary containers for users

To get started, start with :doc:`create-cloud-resources`.

.. tip::

   If you’d like to extend your JupyterHub setup, see the complementary guide
   `Zero to JupyterHub <https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html>`_.

Full Table of Contents
----------------------

.. toctree::
   :maxdepth: 2
   :numbered:

   diagram
   create-cloud-resources
   setup-binderhub
   debug
   turn-off
   api/api-index.rst
