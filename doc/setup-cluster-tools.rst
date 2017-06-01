Set up cluster tools
------------------------
Next we'll install a few tools that are required for Binder to run properly.

Installing Helm
===============
First we'll install Helm. This allows us to control our Kubernetes cluster
with a configuration file (called a Helm Chart). By using a Helm Chart, we
can set up the cluster deployment to have the resources necessary for
running Binder Hub.

Run the following commands to download and install helm::
     
   curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash

   helm init

Install kubectl
===============

Next we'll install ``kubectl`` (short for Kubernetes Control). This allows us
to interact with the Kubernetes instance, and to get information about what
nodes are running on our Kubernetes platform. Run the following command::
             
   gcloud components install kubectl
     
Now that our tools are set up, we need to `set up our Docker image registry <setup-registry.html>`_.
