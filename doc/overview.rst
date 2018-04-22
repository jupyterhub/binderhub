.. _diagram:

The BinderHub Architecture
==========================

This page provides a high-level overview of the technical pieces that make
up a BinderHub deployment.

Tools used by BinderHub
-----------------------

BinderHub connects several services together to provide on-the-fly creation
and registry of Docker images. It utilizes the following tools:

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

What happens when a user clicks a Binder link?
----------------------------------------------

After a user clicks a Binder link, the following chain of events happens:

1. BinderHub resolves the link to the repository.
2. BinderHub determines whether a Docker image already exists for the repository at the latest
   ``ref`` (git commit hash, branch, or tag).
3. **If the image doesn't exist**, BinderHub creates a ``build`` pod that uses
   `repo2docker <https://github.com/jupyter/repo2docker>`_ to do the following:
      * Fetch the repository associated with the link
      * Build a Docker container image containing the environment specified in
        `configuration files <https://mybinder.readthedocs.io/en/latest/using.html#supported-configuration-files>`_
        in the repository.
      * Push that image to a Docker registry, and send the registry information
        to the BinderHub for future reference.
4. BinderHub sends the Docker image registry to **JupyterHub**.
5. JupyterHub creates a Kubernetes pod for the user that serves the built Docker image
   for the repository.
6. JupyterHub monitors the user's pod for activity, and destroys it after a short period of
   inactivity.

A diagram of the BinderHub architecture
---------------------------------------

Here is a high-level overview of the components that make up BinderHub.

.. This image was generated at the following URL: https://docs.google.com/presentation/d/1t5W4Rnez6xBRz4YxCxWYAx8t4KRfUosbCjS4Z1or7rM/edit#slide=id.g25dbc82125_0_53

.. raw:: html

   <img src="_static/images/architecture.png" />
