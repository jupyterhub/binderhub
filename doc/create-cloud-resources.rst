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

Setting up Kubernetes on `Google Cloud <https://cloud.google.com/>`_
--------------------------------------------------------------------

.. note::

   BinderHub is built to be cloud agnostic, and can run on various cloud
   providers (as well as bare metal). However, here we only provide
   instructions for Google Cloud as it has been the most extensively-tested.
   If you would like to help with adding instructions for other cloud
   providers, `please contact us <https://github.com/jupyterhub/binderhub/issues>`_!

.. include:: k8s.txt
   :start-after: Setting up Kubernetes on `Google Cloud <https://cloud.google.com/>`_
   :end-before: .. _microsoft-azure:

Install Helm
------------

.. include:: helm.txt
   :start-after: ===============
   :end-before: Next Step

Now that you've installed Kubernetes and Helm, it's time to :ref:`setup-registry`.
