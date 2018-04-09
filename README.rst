`BinderHub`_
============

.. image:: https://travis-ci.org/jupyterhub/binderhub.svg?branch=master
   :target: https://travis-ci.org/jupyterhub/binderhub
   :alt: travis status

.. image:: https://readthedocs.org/projects/binderhub/badge/?version=latest
   :target: https://binderhub.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

What is BinderHub?
------------------

**BinderHub** allows you to ``BUILD`` and ``REGISTER`` a Docker image using a
GitHub repository, then ``CONNECT`` with JupyterHub, allowing you to create a
public IP address that allows users to interact with the code and environment
within a live JupyterHub instance. You can select a specific branch name,
commit, or tag to serve.

BinderHub ties together:

- `JupyterHub <https://github.com/jupyterhub/jupyterhub>`_ to provide
  a scalable system for authenticating users and spawning single user
  Jupyter Notebook servers, and

- `Repo2Docker <https://github.com/jupyter/repo2docker>`_ which generates
  a Docker image using a Git repository hosted online.

BinderHub is created using Python, kubernetes, tornado, and traitlets. As such,
it should be a familiar technical foundation for Jupyter developers.

Why BinderHub?
--------------

Collections of Jupyter notebooks are becoming more common in scientific research
and data science. The ability to serve these collections on demand enhances the
usefulness of these notebooks.

Who is BinderHub for?
---------------------
* **Users** who want to easily interact with computational environments that
  others have created.
* **Authors** who want to create links that allow users to immediately interact with a
  computational enviroment that you specify.
* **Deployers** who want to create their own BinderHub to run on whatever
  hardware they choose.

Installation
------------

**BinderHub** is based on Python 3, it's currently only hosted on GitHub (pip release soon).
However, it can be installed using ``pip``::

    pip install git+https://github.com/jupyterhub/binderhub
    
See `the BinderHub documentation <https://binderhub.readthedocs.io>`_ for a detailed guide on setting
up your own BinderHub server.

**Local development**: To run BinderHub locally in order to make contributions to the codebase,
see `the contribution guide <https://github.com/jupyterhub/binderhub/blob/master/CONTRIBUTING.md>`_.

Documentation
-------------

For more information about the architecture, use, and setup of BinderHub, see
`the BinderHub documentation <https://binderhub.readthedocs.io>`_.

License
-------

See ``LICENSE`` file in this repository.


.. _BinderHub: https://github.com/jupyterhub/binderhub
