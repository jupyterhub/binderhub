Getting started
---------------

The goal of BinderHub is to allow users to quickly create custom
computing environments that can be accessed remotely (e.g., at a specific URL)
by multiple users.

This guide acts as an assistant to guide you through the process of setting up your BinderHub deployment. It helps you connect and configure
the following things:

* A cloud provider such Google Cloud, Microsoft Azure, Amazon EC2, and others
* Kubernetes to manage resources on the cloud
* Helm to configure and control Kubernetes
* Docker to use containers that standardize computing environments
* A UI that users can access to specify GitHub repos they want built
* BinderHub to generate Docker images using the URL of a github repository
* A Docker registry (such as gcr.io) that hosts container images
* JupyterHub to deploy temporary containers for users

To get started, start with the `next item <create-k8s-cluster.html>`_ the list on our main page.

.. note:: If you’d like to extend your jupyterhub setup, see the complementary guide `Zero to JupyterHub <https://zero-to-jupyterhub.readthedocs.io>`_.
