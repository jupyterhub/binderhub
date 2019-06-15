.. _federation/federation:

========================
The BinderHub Federation
========================

While it may seem like ``mybinder.org`` is a single website, it is
in fact a **federation** of teams that deploy public BinderHubs to serve
the community. This page lists the BinderHubs that currently help
power ``mybinder.org``.

Visiting ``mybinder.org`` will randomly redirect you to one
of the following BinderHubs. You may also directly access a BinderHub
by using its respective sub-domain in your URL.

If your organization is interested in becoming part of the BinderHub
federation, check out :ref:`federation/joining`.

.. _federation/federation-list:

Members of the BinderHub Federation
===================================

Here is a list of the current members of the BinderHub federation:

.. include:: data-federation.txt


.. _federation/joining:

Joining the BinderHub Federation
================================

The Binder Project is an open community of developers as well as deployers
of BinderHub. BinderHub is designed to be used by any organization for
their own purposes. However, many members of the community also run
the BinderHub deployments at ``mybinder.org`` as a large, free public service
to the community.

Behind ``mybinder.org`` is a **federation of BinderHubs** - these are
BinderHubs run by those who wish to support the ``mybinder.org`` deployment
by taking on some of the users that click on public Binder links. Some
are university researchers, others work at companies, anybody is welcome
to deploy their own BinderHub to help power ``mybinder.org``.

.. _federation/things-to-consider:

If you're interested in joining the federation of BinderHubs, consider the
following questions:

1. **How much time will this take?** Answering this question depends largely
   on how comfortable you are deploying and maintaining your own BinderHub.
   If you are fairly comfortable, it won't take much time. Otherwise, it may
   be a good idea to gain some experience in running a BinderHub first -
   perhaps by helping with the ``mybinder.org`` deployment!
2. **Is there any kind of service agreement?** Not really. We expect that
   any member of the BinderHub federation will be committed to keeping their
   BinderHub running with a reasonable uptime, but we don't have any legal
   framework to enforce this. Use your best judgment when deciding if you'd
   like to join the BinderHub federation - if you can confidently say your
   BinderHub will be up the large majority of the time, then that's fine.
3. **What kind of cloud resources would I need?** This depends on how many
   you have :-)  We can increase or decrease the percentage of ``mybinder.org``
   traffic that goes to your BinderHub based on what you can handle. If you
   can only handle a few dozen user pods (remember users get ~ 2GB of RAM and
   1 CPU) then we can make sure you stay under that amount.
4. **I'm still interested, what should I do next to join?** If you'd still
   like to join the BinderHub federation, see :ref:`federation/how-to-join`.


.. _federation/how-to-join:

How to join the BinderHub Federation
====================================

If you'd like to join the BinderHub federation, please reach out to the
Binder team by opening an issue at `the mybinder.org repository <https://github.com/jupyterhub/mybinder.org-deploy>`_.
Mention that you'd like to join the federation, what kind of computational
resources you have, and what kind of human resources you have for maintaining
the BinderHub deployment.

The next step is for you to tell us where your BinderHub lives. We'll assign
a sub-domain of ``mybinder.org`` (e.g. ``ovh.mybinder.org``) that points to
your BinderHub. Finally, we'll change the routing configuration so that
some percentage of traffic to ``mybinder.org`` is directed to your BinderHub!
The last step is to tell everybody how awesome you are, and to add your
deployment to :ref:`federation/federation-list` page.