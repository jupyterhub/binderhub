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

.. _setup-registry:

Set up the container registry
-----------------------------

BinderHub will build Docker images out of GitHub repositories, and then push
them to a docker registry so that JupyterHub can launch user servers based
on these images.You can use any registry that
you like, though this guide covers how to properly configure the **Google
Container Registry** (``gcr.io``).

You need to provide BinderHub with proper credentials so it can push images
to the Google Container Registry. You can do so by creating a service
account that has authorization to push to Google Container Registry:

1. Go to `console.cloud.google.com`_
2. Make sure your project is selected
3. Click ``<top-left menu w/ three horizontal bars> -> IAM & Admin -> Service Accounts`` menu option
4. Click **Create service account**
5. Give your account a descriptive name such as "BinderHub-registry"
6. Click ``Role -> Storage -> Storage Admin`` menu option
7. Check **Furnish new private key**
8. Leave key type as default of **JSON**
9. Click **Create**

These steps will download a **JSON file** to your computer. The JSON file
contains the password that can be used to push Docker images to the ``gcr.io``
registry.

.. warning::

   Don't share the contents of this JSON file with anyone. It can be used to
   gain access to your google cloud account!

.. important::

   Make sure to store this JSON file as you cannot generate a second one
   without re-doing the steps above.

Now that our cloud resources are set up, it's time to :doc:`setup-binderhub`.

.. _console.cloud.google.com: http://console.cloud.google.com
