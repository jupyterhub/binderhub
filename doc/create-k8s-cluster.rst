Create your Kubernetes cluster
------------------------------
It is possible to run a Binder deployment on any cloud provider or on
your own hardware. This guide will focus on using the Google cloud computing
engine.

Set up Google cloud credentials
===============================
Before starting with Google Cloud, make sure that you've got an account
with their cloud computing platform. You also need to authorize the components
that we'll use to get Binder running.

<<<TODO>>>

* Set up gcloud credentials
* auth login
* set zone
* set project
* enable API
* enable container registry
* Do::

   gcloud auth application-default login
          
Create your cluster
===================
Next we'll tell Google to create a cluster that will run our code (and
serve user instances). There are many ways to customize the cluster you'll
use and you can see some examples of this below. To create your cluster, run the following command::
    
   gcloud container clusters create dev --num-nodes=1 --cluster-version=1.6.4\
      --machine-type=n1-highmem-4 --disable-addons=HttpLoadBalancing\
      --zone=us-central1-b

Next, we need to `set up tools on the cluster <setup-cluster-tools.html>`_.
