`BinderHub`_
============

.. image:: https://readthedocs.org/projects/binderhub/badge/?version=latest
   :target: http://binderhub.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

What is BinderHub?
------------------

**BinderHub** allows you to ``BUILD`` and ``REGISTER`` a Docker image using a
GitHub repository, including a specific branch name, commit, or tag. It
connects with JupyterHub, allowing you to create a public IP address that allows
users to interact with the code and environment within a live JupyterHub
instance.

BinderHub is similar in spirit to the existing `Binder <http://mybinder.org>`_
service. BinderHub ties together:

- `JupyterHub <https://github.com/jupyterhub/jupyterhub>`_ to provide
  a scalable system for authenticating users and spawning single user
  Jupyter Notebook servers, and

- Red Hat's `source-to-image <https://github.com/openshift/source-to-image>`_
  project from OpenShift to build a Docker image from a set of dependencies.

BinderHub is created using Python, kubernetes, tornado, and traitlets. As such,
it should be a familiar technical foundation for Jupyter developers.

Why BinderHub?
--------------

Collections of Jupyter notebooks are becoming more common in scientific research
and data science. The ability to serve these collections on demand enhances the
usefulness of these notebooks.

Installation
------------

**BinderHub** is based on Python 3, and it can be installed using ``pip``::

    pip install binderhub

Documentation
-------------

For more information about the architecture, use, and setup of BinderHub, see
`the documentation online <https://jupyterhub.github.io/binderhub>`_ or on
`ReadTheDocs <https://binderhub.readthedocs.io>`_.

License
-------

See ``LICENSE`` file in this repository.

.. _BinderHub: https://github.com/jupyterhub/binderhub
