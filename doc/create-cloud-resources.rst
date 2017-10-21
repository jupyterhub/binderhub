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

`Google Container Engine <https://cloud.google.com/container-engine/>`_
(confusingly abbreviated to GKE) is the simplest and most common way of setting
up a Kubernetes Cluster. You may be able to receive `free credits
<https://cloud.google.com/free/>`_ for trying it out. You will need to
connect your credit card or other payment method to your google cloud account.

1. Go to ``https://console.cloud.google.com`` and log in.

2. Enable the `Container Engine API <https://console.cloud.google.com/apis/api/container.googleapis.com/overview>`_.

3. Install and initialize the **gcloud command-line tools**. These tools send
   commands to Google Cloud and lets you do things like create and delete
   clusters.

   - Go to the `gcloud downloads page <https://cloud.google.com/sdk/downloads>`_
     to **download and install the gcloud SDK**.
   - See the `gcloud documentation <https://cloud.google.com/sdk/>`_ for
     more information on the gcloud SDK.
   - Install ``kubectl``, which is a tool for controlling kubernetes. From
     the terminal, enter:

     .. code-block:: bash

        gcloud components install kubectl

4. Create a Kubernetes cluster on Google Cloud, by typing in the following
   command:

   .. code-block:: bash

      gcloud container clusters create <YOUR_CLUSTER> \
          --num-nodes=3 \
          --machine-type=n1-standard-2 \
          --zone=us-central1-b

   where:

   * ``--num-nodes`` specifies how many computers to spin up. The higher the
     number, the greater the cost.
   * ``--machine-type`` specifies the amount of CPU and RAM in each node. There
     is a `variety of types <https://cloud.google.com/compute/docs/machine-types>`_
     to choose from. Picking something appropriate here will have a large effect
     on how much you pay - smaller machines restrict the max amount of RAM each
     user can have access to but allow more fine-grained scaling, reducing cost.
     The default (`n1-standard-2`) has 2CPUs and 7.5G of RAM each, and might not
     be a good fit for all use cases!
   * ``--zone`` specifies which data center to use. Pick something that is not
     too far away from your users. You can find a list of them `here <https://cloud.google.com/compute/docs/regions-zones/regions-zones#available>`_.

5. To test if your cluster is initialized, run:

   .. code-block:: bash

      kubectl get node

   The response should list three running nodes.

Next we'll install a few tools that are required for BinderHub to run properly.

Installing Helm
---------------

Next, we'll install **Helm**. This allows us to control our Kubernetes cluster
with a configuration file (called a Helm Chart). By using a **Helm Chart**, we
can set up the cluster deployment to have the resources necessary for
running BinderHub.

Run the following commands to download and install helm::

   curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
   helm init

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
