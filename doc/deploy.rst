Deploy your Binder
------------------

Now that everything is configured properly, it's time to deploy your
Binder instance. To do this we'll install the Helm Chart that we've just
specified. Do this by running the following commands::

   helm install helm-chart/binderhub --name=binder --namespace=binder -f secret.yaml -f config.yaml

This will instruct Kubernetes to construct the machinery necessary to
run BinderHub and serve user instances with JupyterHub. This may take a
minute to finish setting up. To get the status of your Binder deployment,
use the following command::

   kubectl --namespace=binder get pod

If you make changes to your Helm Chart (e.g., while debugging), you can
run an upgrade on your Kubernetes deployment like so::

   helm upgrade binder helm-chart/binderhub -f secret.yaml -f config.yaml

Now go to the URL that you've specified for accessing Binder (e.g.,
``beta.mybinder.org``). You should now have a fully-functioning Binder
deployment!

If you'd like to tear down your BinderHub instance, see our `tear down guide <turn-off.html>`_.
