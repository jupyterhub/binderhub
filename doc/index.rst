.. include:: ../README.rst

BinderHub Documentation
========================

.. note::

   This project is under active development and subject to change.

Site TOC
--------
.. toctree::

   setup.rst
   diagram.rst

What is BinderHub?
-------------------
BinderHub allows you to BUILD and REGISTER a Docker image using a GitHub
repository, then CONNECT with JupyterHub, allowing you to create a
public IP address that allows users to interact with the code / environment
you specify in the repository within a live JupyterHub instance. You can also
specify a specific branch name / commit / tag to serve.

It is similar in spirit to the existing `Binder <http://mybinder.org>`_ service.
It's goal is to tie together:

- `JupyterHub <https://github.com/jupyterhub/jupyterhub>`_ to provide
  a scalable system for authenticating users and spawning single user
  Jupyter Notebook servers, and

- `Repo2Docker <https://github.com/jupyter/repo2docker>`_ which generates
  a Docker image using a Git repository hosted online. This heavily utilizes:

- Red Hat's `source-to-image <https://github.com/openshift/source-to-image>`_
  project from OpenShift to build a Docker image from a set of dependencies.

BinderHub is created using Python, kubernetes, tornado, and traitlets. As such,
it should be a familiar technical foundation for Jupyter developers.

Why BinderHub?
---------------
Collections of Jupyter notebooks are becoming more common in scientific research
and data science. The ability to serve these collections on demand enhances the
usefulness of these notebooks.

Installation
------------

**BinderHub** is based on Python 3, and it can be installed using pip::

    pip install binderhub

License
-------

See `LICENSE` file in this repository.
