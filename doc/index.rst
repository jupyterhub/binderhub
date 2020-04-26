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

To get started creating your own BinderHub, start with :ref:`zero-to-binderhub`.


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

   zero-to-binderhub/index

Customization and deployment information
========================================

Information on how to customize your BinderHub as well as explore what others
in the community have done.

.. toctree::
   :maxdepth: 2

   customization/index

BinderHub Developer and Architecture Documentation
==================================================

A more detailed overview of the BinderHub design, architecture, and functionality.

.. toctree::
   :maxdepth: 2
   :caption:  Developer and architecture docs

   developer/index

The BinderHub community
=======================

The BinderHub community includes members of organizations deploying their own BinderHubs,
as well as members of the broader Jupyter and Binder communities.

This section contains a collection of resources for and about the BinderHub community.

.. toctree::
   :maxdepth: 2

   community/index
