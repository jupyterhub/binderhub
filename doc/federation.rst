Federation
==========

In order to provide a number of guaranties, like persistence, scalability and
convenience, Binder and BinderHub have been developed to be ran in a federated
manner, this mean that you, or your organisation can decide to run a public, or
private binder (behind authentication).

When this is the case, you want most of the binder badges and link to
transparently redirect to your private instances. Moreover a user might want to
select on which instance to run their code. 

For this reason BinderHub have a number of settings allowing it to register
an instance with the main MyBinder.org and which users should be sent your way. 

To do so you must set the ``c.BinderHub.cannonical_address`` to the full
canonical canonical address of your binder instance (including ``https://``
prefix). For example in the Binder Config file: ``c.BinderHub.cannonical_address = 'https://binder.example.com/'``.

By doing so binder will now expose an ``https://binder.example.com/expose/``
url. Containing a "Register" button. When your users click this buttons, they
will be redirected to ``https://mybinder.org/`` and an (encrypted) cookie will
be set in their browser session, telling my binder these users should be allowed
to visit and use ``https://binder.example.com/``, then prompted if they would
like to make it their default. 

Once your users have choosen to do so, anytime such a user hit a
``https://mybinder.org/`` url, they will be redirected to your service.

Federation Portal
-----------------

If you are running in a close network and have multiple teams with their own
binder instances with various authorisations and difference in allocated
resources. 

By setting the ``c.BinderHub.use_as_federation_portal=True`` this will tell
the target binderhub to redirect to the user-selected binder. 

The ``c.BinderHub.default_binders_list`` can be used to pre-register a number of
known binder.

And the ``c.BinderHub.list_cookie_set_binders`` can be used to allow users to
register their own binders.

A binder cannot be both exposed and be a portal to avoid redirect loop. 
