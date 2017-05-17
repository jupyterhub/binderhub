BuilderHub Documentation
========================

.. note::

   This project is under active development and subject to change.

Site TOC
--------
.. toctree::

   diagram.rst

What is BuilderHub?
-------------------
BuilderHub allows you to BUILD and REGISTER a Docker image using a GitHub
repository along with a branch name / commit / tag. It also connects with
JupyterHub, allowing you to create a public IP address that allows users to
interact with the code / environment you specify in the repository within
a live JupyterHub instance.

It is similar in spirit to the existing `Binder <mybinder.org>`_ service. It's
goal is to tie together:

- `JupyterHub <https://github.com/jupyterhub/jupyterhub>`_ to provide
  a scalable system for authenticating users and spawning single user
  Jupyter Notebook servers, and

- Red Hat's `source-to-image <https://github.com/openshift/source-to-image>`_
  project from OpenShift to build a Docker image from a set of dependencies.

Builderhub is created using Python, kubernetes, tornado, and traitlets. As such,
it should be a familiar technical foundation for Jupyter developers.

Why BuilderHub?
---------------
Collections of Jupyter notebooks are becoming more common in scientific research
and data science. The ability to serve these collections on demand enhances the
usefulness of these notebooks.

Installation
------------

**builderhub** is based on Python 3, and it can be installed using pip::

    pip install builderhub

License
-------

See `LICENSE` file in this repository.
