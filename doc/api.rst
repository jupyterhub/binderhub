BinderHub API Documentation
===========================

Endpoint
--------

There's one API endpoint, which is:

::

    /build/<provider>/<spec>

Even though it says **build** it is actually performs **launch**.

Provider
--------

Provider is a supported provider, and **spec** is the specification for
the given provider.

Currently supported providers and their specs are:

+------------+-----------+-------------------------------------------------------------+----------------------------+
| Provider   | prefix    | spec                                                        | notes                      |
+============+===========+=============================================================+============================+
| GitHub     | ``gh``    | ``<user>/<repo>/<commit-sha-or-tag-or-branch>``             |                            |
+------------+-----------+-------------------------------------------------------------+----------------------------+
| Git        | ``git``   | ``<url-escaped-url>/<commit-sha>``                          | arbitrary HTTP git repos   |
+------------+-----------+-------------------------------------------------------------+----------------------------+
| GitLab     | ``gl``    | ``<url-escaped-namespace>/<commit-sha-or-tag-or-branch>``   |                            |
+------------+-----------+-------------------------------------------------------------+----------------------------+

Next, construct an appropriate URL and send a request.

You'll get back an `Event
Stream <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events>`__.
It's pretty much just a long-lived HTTP connection with a well known
JSON based data protocol. It's one-way communication only (server to
client) and is straightforward to implement across multiple languages.

When the request is received, the following happens:

1. Check if this image exists in our cached image registry. If so,
   launch it.
2. If it doesn't exist in the image registry, we check if a build is
   currently running. If it is, we attach to it and start streaming logs
   from it to the user.
3. If there is no build in progress, we start a build and start
   streaming logs from it to the user.
4. If the build succeeds, we contact the JupyterHub API and start
   launching the server.

Events
------

This section catalogs the different events you might receive.

Failed
~~~~~~

Emitted whenever a build or launch fails. You *must* close your
EventStream when you receive this event.

::

    {'phase': 'failed', 'message': 'Reason for failure'}

Built
~~~~~

Emitted after the image has been built, before launching begins. This is
emitted in the start if the image has been found in the cache registry,
or after build completes successfully if we had to do a build.

::

    {'phase': 'built', 'message': 'Human readable message', 'imageName': 'Full name of the image that is in the cached docker registry'}

Note that clients shouldn't rely on the imageName field for anything
specific. It should be considered an internal implementation detail.

Waiting
~~~~~~~

Emitted when we started a build pod and are waiting for it to start.

::

    {'phase': 'waiting', 'message': 'Human readable message'}

Building
~~~~~~~~

Emitted during the actual building process. Direct stream of logs from
the build pod from repo2docker, in the same form as logs from a normal
docker build.

::

    {'phase': 'building', 'message': 'Log message'}

Fetching
~~~~~~~~

Emitted when fetching the repository to be built from its source
(GitHub, GitLab, wherever).

::

    {'phase': 'fetching', 'message': 'log messages from fetching process'}

Pushing
~~~~~~~

Emitted when the image is being pushed to the cache registry. This
provides structured status info that could be in a progressbar. It's
structured similar to the output of docker push.

::

    {'phase': 'pushing', 'message': 'Human readable message', 'progress': {'layer1':  {'current': <bytes-pushed>, 'total': <full-bytes>}, 'layer2': {'current': <bytes-pushed>, 'total': <full-bytes>}, 'layer3': "Pushed", 'layer4': 'Layer already exists'}}

Launching
~~~~~~~~~

When the repo has been built, and we're in the process of waiting for
the hub to launch. This could end up succeeding and emitting a 'ready'
event or failing and emitting a 'failure' event.

::

    {'phase': 'launching', 'message': 'user friendly message'}

Ready
~~~~~

When your notebook is ready! You get a endpoint URL and a token used to
access it. You can access the notebook / API by using the token in one
of the ways the `notebook accepts security
tokens <http://jupyter-notebook.readthedocs.io/en/stable/security.html>`__

::

    {"phase": "ready", "message": "Human readable message", "url": "full-url-of-notebook-server", "token": "notebook-server-token"}

Heartbeat
---------

In EventSource, all lines beginning with ``:`` are considered comments.
We send a ``:heartbeat`` every 30s to make sure that we can pass through
proxies without our request being killed.
