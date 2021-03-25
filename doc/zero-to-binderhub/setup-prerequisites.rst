.. _create-cluster:

Set up the prerequisites
========================

BinderHub is built to run in a `Kubernetes cluster <http://kubernetes.io/>`_. It
relies on JupyterHub to launch and manage user servers, as well as a docker
registry to cache docker images it builds.

To deploy your own BinderHub, you'll first need to set up a Kubernetes cluster.
The following instructions will assist you in doing so.

Setting up a Kubernetes cluster
-------------------------------

First, deploy a Kubernetes cluster by following the `instructions in the Zero to
JupyterHub guide
<https://zero-to-jupyterhub.readthedocs.io/en/latest/kubernetes/setup-kubernetes.html>`_.
When you're done, move on to the next section.

Installing Helm
---------------

`Helm <https://helm.sh/>`_, the package manager for Kubernetes, is a useful tool
for: installing, upgrading and managing applications on a Kubernetes cluster.
Helm packages are called *charts*. We will be installing and managing JupyterHub
on our Kubernetes cluster using a Helm chart.

A Helm *chart* is mostly Helm *templates* and default *values* that are used to
render the templates into valid k8s resources. Each installation of a chart is
called a *release*, and each version of the release is called a *revision*.

Several `methods to install Helm
<https://github.com/helm/helm/blob/master/docs/install.md>`_ exist, the simplest
way to install Helm is to run Helm's installer script in a terminal.

.. code:: bash

   curl -sf https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3

Verifying the setup
~~~~~~~~~~~~~~~~~~~

Verify that you have installed helm, kubectl, and have an ability to communicate
with your Kubernetes cluster.

.. code:: bash

   helm version

Which will output something similar to:

.. code-block:: bash

   version.BuildInfo{Version:"v3.4.0", GitCommit:"7090a89efc8a18f3d8178bf47d2462450349a004", GitTreeState:"clean", GoVersion:"go1.14.10"}

Then check your kubectl version:

.. code-block:: bash

   kubectl version

Which will output something similar to:

.. code-block:: bash

   Client Version: version.Info{Major:"1", Minor:"19", GitVersion:"v1.19.3", GitCommit:"1e11e4a2108024935ecfcb2912226cedeafd99df", GitTreeState:"clean", BuildDate:"2020-10-14T12:50:19Z", GoVersion:"go1.15.2", Compiler:"gc", Platform:"linux/amd64"}
   Server Version: version.Info{Major:"1", Minor:"19", GitVersion:"v1.19.2", GitCommit:"f5743093fd1c663cb0cbc89748f730662345d44d", GitTreeState:"clean", BuildDate:"2020-09-16T13:32:58Z", GoVersion:"go1.15", Compiler:"gc", Platform:"linux/amd64"}

Now that you've installed Kubernetes and Helm, it's time to :ref:`setup-registry`.
