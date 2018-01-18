.. _diagram:

The BinderHub Architecture
==========================

BinderHub connects several services together to provide on-the-fly creation
and registry of Docker images. After a user inputs a GitHub repo name or URL,
BinderHub primarily does the following things:

1. Builds automatically a Docker container image using
   `Repo2Docker <https://github.com/jupyter/repo2docker>`_.
2. Registers this Docker image with an online registry.
3. Sends registry information to a JupyterHub instance that then serves the
   Docker image.

Here is a high-level overview of the components that make up BinderHub.

.. This image was generated at the following URL: https://docs.google.com/presentation/d/1t5W4Rnez6xBRz4YxCxWYAx8t4KRfUosbCjS4Z1or7rM/edit#slide=id.g25dbc82125_0_53

.. raw:: html

   <img src="_static/images/binderhub_diagram.png" />
