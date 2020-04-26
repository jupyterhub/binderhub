.. _create-cluster:

Set up the prerequisites
========================

BinderHub is built to run on top of Kubernetes, a distributed cluster manager.
It uses a JupyterHub to launch and manage user servers, as well as a
docker registry to cache images.

To create your own BinderHub, you'll first need to set up a Kubernetes Cluster
and then configure its various components correctly. The following instructions
will assist you in doing so.

.. note::

   BinderHub uses a JupyterHub running on Kubernetes for much of its functionality.
   For information on setting up and customizing your JupyterHub, we recommend reading
   the `Zero to JupyterHub Guide <https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html>`_.

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


Installing Helm
---------------

`Helm <https://helm.sh/>`_, the package manager for Kubernetes, is a useful tool
for: installing, upgrading and managing applications on a Kubernetes cluster.
Helm packages are called *charts*.
We will be installing and managing JupyterHub on
our Kubernetes cluster using a Helm chart.

Charts are abstractions describing how to install packages onto a Kubernetes
cluster. When a chart is deployed, it works as a templating engine to populate
multiple `yaml` files for package dependencies with the required variables, and
then runs `kubectl apply` to apply the configuration to the resource and install
the package.

Helm has two parts: a client (`helm`) and a server (`tiller`). Tiller runs
inside of your Kubernetes cluster as a pod in the kube-system namespace. Tiller
manages both, the *releases* (installations) and *revisions* (versions) of charts deployed
on the cluster. When you run `helm` commands, your local Helm client sends
instructions to `tiller` in the cluster that in turn make the requested changes.


.. note::

   These instructions are for Helm 2.
   Helm 3 includes several major breaking changes and is not yet officially
   supported

Several `methods to install Helm
<https://github.com/helm/helm/blob/master/docs/install.md>`_ exist, the
simplest way to install Helm is to run Helm's installer script in a terminal:

.. code:: bash

  curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash

Initializing Helm
~~~~~~~~~~~~~~~~~

After installing helm on your machine, initialize Helm on your Kubernetes
cluster:

1. Set up a `ServiceAccount
   <https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/>`_
   for use by `tiller`.

   .. code-block:: bash

      kubectl --namespace kube-system create serviceaccount tiller

2. Give the `ServiceAccount` full permissions to manage the cluster.

   .. code-block:: bash

      kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller

3. Initialize `helm` and `tiller`.

   .. code-block:: bash

      helm init --service-account tiller --history-max 100 --wait

   This command only needs to run once per Kubernetes cluster, it will create a
   `tiller` deployment in the kube-system namespace and setup your local `helm`
   client.
   This command installs and configures the `tiller` part of Helm (the whole
   project, not the CLI) on the remote kubernetes cluster. Later when you want
   to deploy changes with `helm` (the local CLI), it will talk to `tiller`
   and tell it what to do. `tiller` then executes these instructions from
   within the cluster.
   We limit the history to 100 previous installs as very long histories slow
   down helm commands a lot.

   .. note::

      If you wish to install `helm` on another computer, you won't need to setup
      `tiller` again but you still need to initialize `helm`:

      .. code-block:: bash

         helm init --client-only

Securing Helm
~~~~~~~~~~~~~

Ensure that `tiller` is secured against access from inside the cluster:

.. code:: bash

   kubectl patch deployment tiller-deploy --namespace=kube-system --type=json --patch='[{"op": "add", "path": "/spec/template/spec/containers/0/command", "value": ["/tiller", "--listen=localhost:44134"]}]'

By default `tiller`'s port is exposed in the cluster without authentication and
if you probe this port directly (i.e. by bypassing `helm`) then `tiller`'s
permissions can be exploited. This step forces `tiller` to listen to commands
from localhost (i.e. `helm`) *only* so that other pods inside the cluster cannot
ask `tiller` to install a new chart granting them arbitrary, elevated RBAC
privileges which they could then exploit.
`More details here. <https://engineering.bitnami.com/articles/helm-security.html>`_

Verifying the setup
~~~~~~~~~~~~~~~~~~~

You can verify that you have the correct version and that it installed properly
by running:

.. code:: bash

   helm version

It should provide output like below. If you just installed everything for the
first time it might take one or two minutes to show the output. Make sure you
have at least version 2.11.0 and that the client (`helm`) and server
version (`tiller`) match!

.. code-block:: bash

   Client: &version.Version{SemVer:"v2.11.0", GitCommit:"2e55dbe1fdb5fdb96b75ff144a339489417b146b", GitTreeState:"clean"}
   Server: &version.Version{SemVer:"v2.11.0", GitCommit:"2e55dbe1fdb5fdb96b75ff144a339489417b146b", GitTreeState:"clean"}

Now that you've installed Kubernetes and Helm, it's time to :ref:`setup-registry`.
