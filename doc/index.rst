BinderHub
=========

.. warning::

   BinderHub is under active development and subject to breaking changes.

Getting started
---------------

The primary goal of BinderHub is creating custom computing environments that
can be used by many remote users. BinderHub enables an end user to easily
specify a desired computing environment from a GitHub repo. BinderHub then
serves the custom computing environment at a URL which users can access
remotely.

This guide assists you, an administrator, through the process of setting up
your BinderHub deployment.

To get started creating your own BinderHub, start with :doc:`create-cloud-resources`.

.. tip::

   If you’d like to extend your JupyterHub setup, see the complementary guide
   `Zero to JupyterHub <https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html>`_.

Zero to BinderHub
-----------------

A guide to help you create your own BinderHub from scratch.

.. toctree::
   :maxdepth: 2
   :numbered:

   create-cloud-resources
   setup-registry
   setup-binderhub
   turn-off

Customization and more information
----------------------------------

.. toctree::
   :maxdepth: 2
   :numbered:

   overview
   debug
   customizing
   api
   reference/ref-index.rst
