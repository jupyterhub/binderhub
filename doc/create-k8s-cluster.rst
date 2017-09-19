.. _create-cluster:

Create your Kubernetes cluster
==============================

BinderHub is built on top of JupyterHub, which uses Kubernetes to manage
user instances in the cloud. You'll first need to set up some cloud resources,
and make sure that Kubernetes is running on them.

The `JupyterHub Kubernetes guide <https://zero-to-jupyterhub.readthedocs.io/en/latest/create-k8s-cluster.html>`_
has instructions on setting up both cloud resources as well as
Kubernetes on several cloud providers. We
recommend that you follow these instructions to set up Kubernetes, and then
return to this guide to set up your BinderHub deployment.

Once you've set up Kubernetes and your cloud resources, it's time to
`set up tools for running BinderHub on the cluster <setup-cluster-tools.html>`_.
