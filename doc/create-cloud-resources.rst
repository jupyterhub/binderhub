.. _create-cluster:

Create your cloud resources
===========================

BinderHub is built to run on top of Kubernetes, a distributed cluster manager.
It uses a JupyterHub to launch/manage user servers, as well as a
docker registry to cache images.

To create your own BinderHub, you'll first need to set up a properly
configured Kubernetes Cluster on the cloud, and then configure the
various components correctly. The following instructions will assist you
in doing so.

.. note::

   BinderHub uses a JupyterHub running on Kubernetes for much of its functionality.
   For information on setting up and customizing your JupyterHub, we recommend reading
   the `Zero to JupyterHub Guide <https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html#customization-guide>`_.

Setting up Kubernetes on `Google Cloud <https://cloud.google.com/>`_
--------------------------------------------------------------------

.. note::

   BinderHub is built to be cloud agnostic, and can run on various cloud
   providers (as well as bare metal). However, here we only provide
   instructions for Google Cloud as it has been the most extensively-tested.
   If you would like to help with adding instructions for other cloud
   providers, `please contact us <https://github.com/jupyterhub/binderhub/issues>`_!

First, install Kubernetes by following the
`instructions in the Zero to JupyterHub guide <https://zero-to-jupyterhub.readthedocs.io/en/latest/google/step-zero-gcp.html>`_.
When you're done, move on to the next section.

Install Helm
------------

.. include:: helm.txt
   :start-after: ===============
   :end-before: Next Step

Now that you've installed Kubernetes and Helm, it's time to :ref:`setup-registry`.
