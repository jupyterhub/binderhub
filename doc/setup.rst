How to set up BinderHub
=======================

It's possible to deploy your own BinderHub instance in order to
serve on-the-fly Jupyter notebooks and computing environments. In order
to do this, you'll need four things:

1. Hardware that will run the BinderHub architecture and user instances
1. A Kubernetes cluster that is running and to which we have API access
1. A Docker registry that will host container images
1. A JupyterHub that's configured to serve single-use nodes.

We'll cover how to set up each of these below.

Choose your hardware
--------------------
First you'll need hardware on which we'll run JupyterHub. This is most
commonly a cloud computing platform such as Google Cloud, Microsoft Azure,
or Amazon EC2. You can also deploy BinderHub on your own hardware if you
so choose. <<<Add links to these deployments...maybe instructions to set
up on their platforms as well>>>.

Set up a Kubernetes cluster
---------------------------
This is also platform-dependent, though it is relatively straightforward
to set up kubernetes on most cloud computing providers. For instructions
on how to do this, see <<<zero to jupyterhub link>>>.

Set up and configure JupyterHub
-------------------------------
To set up JupyterHub on the cloud, see <<<zero to jupyterhub link>>>.

Once you've got JupyterHub running, update your ``config.yaml`` file to
include the following lines.::

   somevariable:
      somevalue: 'therightvalueprobablynotthisname'

Choosing a Docker container registry
------------------------------------
The container registry is where your built Docker images will be registered
so that JupyterHub can serve them. There are already several options
for registering / hosting Docker images. The two most common ones are
DockerHub and the Google Container Registry.

To specify which of these you wish to use, add the following to your
``config.yaml`` file.::

   someothervariable:
      somevalue: 'theotherrightvaluemaybethisisitthistime'
