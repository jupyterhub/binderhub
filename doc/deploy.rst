Deploy your Binder
==================

Now that everything is configured properly, it's time to deploy your
Binder instance. Let's **install the Helm Chart** that you've just created.
Do this by running the following commands::

   helm install helm-chart/binderhub --name=binder --namespace=binder -f secret.yaml -f config.yaml

This command will instruct Kubernetes to construct the machinery necessary to
run BinderHub and serve user instances with JupyterHub. This may take a
minute or two to finish setting up. To **check the status of your Binder**
deployment, use the following command::

   kubectl --namespace=binder get pod

If you make changes to your Helm Chart (e.g., while debugging), you should
run an upgrade on your Kubernetes deployment like so::

   helm upgrade binder helm-chart/binderhub -f secret.yaml -f config.yaml

Now go to the URL that you've specified for accessing Binder (e.g.,
``beta.mybinder.org``). You should now have a fully-functioning Binder
deployment!

Go ahead and test out the Binder deployment to make sure that it's operating
properly.

If you'd like to tear down your BinderHub instance (perhaps to save on costs
while testing or learning how to create a deployment), see our :doc:`turn-off`.
