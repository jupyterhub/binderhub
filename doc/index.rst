=========
BinderHub
=========

.. image:: https://badges.gitter.im/jupyterhub/binder.svg
   :alt: Join the chat at https://gitter.im/jupyterhub/binder
   :target: https://gitter.im/jupyterhub/binder

.. image:: https://img.shields.io/badge/help_forum-discourse-blue.svg
   :alt: Join our community Discourse page at https://discourse.jupyter.org
   :target: https://discourse.jupyter.org/c/binder/binderhub


Getting started
===============

The primary goal of BinderHub is creating custom computing environments that
can be used by many remote users. BinderHub enables an end user to easily
specify a desired computing environment from a Git repo. BinderHub then
serves the custom computing environment at a URL which users can access
remotely.

This guide assists you, an administrator, through the process of setting up
your BinderHub deployment.

To get started creating your own BinderHub, start with :doc:`create-cloud-resources`.

.. note::

   BinderHub uses a JupyterHub running on Kubernetes for much of its functionality.
   For information on setting up and customizing your JupyterHub, we recommend reading
   the `Zero to JupyterHub Guide <https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html#customization-guide>`_.


BinderHub Deployments
=====================

Our directory of BinderHubs is published at :doc:`known-deployments`.

If your BinderHub deployment is not listed, please
`open an issue <https://github.com/jupyterhub/binderhub/issues>`_
to discuss adding it.

Zero to BinderHub
=================

A guide to help you create your own BinderHub from scratch.

.. toctree::
   :maxdepth: 2
   :numbered:
   :caption: Zero to BinderHub

   create-cloud-resources
   setup-registry
   setup-binderhub
   turn-off

Customization and deployment information
========================================

Information on how to customize your BinderHub as well as explore what others
in the community have done.

.. toctree::
   :maxdepth: 2
   :caption: Customization and deployment

   debug
   customizing
   authentication
   known-deployments
   federation/federation

BinderHub Developer and Architecture Documentation
==================================================

A more detailed overview of the BinderHub design, architecture, and functionality.

.. toctree::
   :maxdepth: 2
   :caption:  Developer and architecture docs

   overview
   eventlogging
   api
   reference/ref-index.rst
