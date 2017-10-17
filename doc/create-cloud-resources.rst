.. _create-cluster:

Create your cloud resources
===========================

BinderHub is built on top of JupyterHub, which uses Kubernetes to manage
user instances in the cloud. You'll first need to set up some cloud resources,
and make sure that Kubernetes is running on them, and configure them to work
properly with one another.

Setting up Kubernetes on `Google Cloud <https://cloud.google.com/>`_
--------------------------------------------------------------------

.. note::

   Currently, BinderHub only runs on Google Cloud. Support for other cloud
   providers will be added in the future.

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

Install kubectl
---------------

Next we'll install ``kubectl`` (short for Kubernetes Control). This allows us
to interact with the Kubernetes instance, and to get information about what
nodes are running on our Kubernetes platform. Run the following command::

   gcloud components install kubectl

.. note::

   If you're working from within Google Cloud Console, this will already be
   installed.

.. _setup-registry:

Set up the container registry
-----------------------------

BinderHub will build Docker images out of GitHub repositories, and then
register those images with an online registry so that JupyterHub can
serve user instances from that registry. You can use any registry that
you like, though this guide covers how to properly configure the **Google
Container Registry** (``gcr.io``).

Doing this involves using the Container Registry user interface in google
cloud. The following steps will create an account with google cloud that has
the authorization to push to google container registry:

1. Go to `console.cloud.google.com`_
2. Make sure your project is selected
3. Click ``<hamburger menu> -> IAM & Admin -> Service Accounts`` menu option
4. Click **Create service account**
5. Give your account a descriptive name such as "BinderHub-registry"
6. Click ``Role -> Storage -> Storage Admin`` menu option
7. Check **Furnish new private key**
8. Click **Create**

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
