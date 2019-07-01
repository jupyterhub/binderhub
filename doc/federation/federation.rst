.. _federation/federation:

========================
The BinderHub Federation
========================

While it may seem like ``mybinder.org`` is a single website, it is
in fact a **federation** of teams that deploy public BinderHubs to serve
the community. This page lists the BinderHubs that currently help
power ``mybinder.org``.

Visiting ``mybinder.org`` will randomly redirect you to one
of the following BinderHubs.

.. note::

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

Behind ``mybinder.org`` is a **federation of BinderHubs**. This means that there
are several independent hubs that each serve a fraction of the traffic
created by people clicking links pointing to ``mybinder.org``. Anyone
(a company, university or individual) is welcome to deploy a BinderHub
that forms part of the federation.

Adding a new BinderHub to the federation requires a mix of two kinds of
resources: compute and human power to operate the hub. The two extremes
of this mixture are:

* You donate compute power that the ``mybinder.org`` team
  **has full control over**, which means you don't have to be involved in day to
  day operations
* You donate compute power over which the ``mybinder.org`` team **does not**
  have full control which means you are also responsible for day to day
  operations of the BinderHub.

.. _federation/things-to-consider:

Things to consider when deciding to join the Binder federation
--------------------------------------------------------------

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
   traffic that goes to your BinderHub based on what you can handle.
4. **I'm still interested, what should I do next to join?** If you'd still
   like to join the BinderHub federation, see :ref:`federation/how-to-join`.


.. _federation/how-to-join:

How to join the BinderHub Federation
------------------------------------

If you've read through :ref:`federation/things-to-consider` and would
like to join the BinderHub federation, please reach out to the
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

.. _federation/faq:

The BinderHub Federation FAQ
============================

Can I deploy a BinderHub *both* for the federation and for my own community?
----------------------------------------------------------------------------

Yes! BinderHub can be deployed either as a public service (such as at mybinder.org),
or for a more restricted community. Serving a smaller community means you can
expose users to more resources or allow access to privileged data.

If you'd like to both serve a more specific population of users *and* support the
public mybinder.org federation, we recommend running two BinderHubs in parallel
with one another. You can do this on the same Kubernets cluster if you wish, and
you'd configure each BinderHub according to the resources and access that you
want to provide.

Who is currently in the BinderHub federation?
---------------------------------------------

The current list of BinderHubs that are contributing to mybinder.org can be
found at :ref:`federation/federation-list`.

Does the BinderHub federation share Docker images?
--------------------------------------------------

Currently, the federation does *not* share Docker images for repositories.
This means that you might have to build your repository a few times (one for
each BinderHub that serves your images). We know that this adds some extra
waiting for many folks, and if you have any suggestions for how we can speed
up this process please `open an issue <https://github.com/jupyterhub/binderhub>`_
in the BinderHub repository!