Set up BinderHub
================

BinderHub uses Helm Charts to set up the applications we'll use in our Binder
deployment. If you're curious about what Helm Charts are and how they're
used here, see the `Zero to JupyterHub guide
<https://zero-to-jupyterhub.readthedocs.io/en/latest/tools.html#helm>`_.

Below we'll cover how to configure your Helm Chart, and how to create your
BinderHub deployment.

Configure the helm chart
------------------------

To configure the Helm Chart we'll need to generate and insert a few pieces of
information.

The first is the content of the JSON file created when we set up
the container registry. For more information on getting a registry password, see
:ref:`setup-registry`. We'll copy/paste the contents of this file in the steps
below.

We also need two random tokens to configure out BinderHub. Generate these
tokens by running the following commands then copying the outputs.::

    openssl rand -hex 32
    openssl rand -hex 32

.. note::

   This command is run **twice** because we need two different tokens.

Configure ``secret.yaml``
-------------------------

Create a file called ``secret.yaml``. In it, put the following code::

  jupyterhub:
      hub:
        services:
          binder:
            apiToken: "<output of FIRST `openssl rand -hex 32`>"
      proxy:
        secretToken: "<output of SECOND `openssl rand -hex 32`>"
  registry:
    password: |
      <contents of the json file from Service Accounts>
  hub:
    services:
      binder:
        apiToken: "<output of FIRST `openssl rand -hex 32`>"

.. tip::

   The content you put just after ``password: |`` must all line up at the same
   tab level.

.. tip::

   Don't forget the ``|`` after the ``password:`` label.

Configure ``config.yaml``
-------------------------

Create a file called ``config.yaml``. In it, put the following code::

  registry:
    # Note this is project *ID*, not just project
    #
    # `<prefix>` can be any string and will be appended to image names
    # e.g., `dev` and `prod`.
    prefix:  gcr.io/<google-project-id>/<prefix>
    enabled: true

  rbac:
     enabled: false
  jupyterhub:
     hub:
        rbac:
           enabled: false

Deploy the helm chart
---------------------

First grab the latest helm chart for BinderHub.::

    helm repo add jupyterhub https://jupyterhub.github.io/helm-chart
    helm repo update

Now we'll **install the Helm Chart** using the configuration
that you've just created. Do this by running the following command::

    helm install jupyterhub/binderhub --version=v0.1.0-789e30a --name=binder --namespace=binder -f secret.yaml -f config.yaml

.. note::

   ``--version`` refers to the version of the BinderHub **Helm Chart**.

.. note::

   ``name`` and ``namespace`` don't *have* to be the same, but we recommend
   it to avoid confusion. You can choose other names if you want, we
   recommend something descriptive and short.

This will deploy both a BinderHub and a JupyterHub, but they won't be
able to communicate with one another yet. We'll fix this in the next
step. Wait a few moments before moving on as the resources may take a
few minutes to be set up.

Connect BinderHub and JupyterHub
--------------------------------
In the google console, run the following command to print the IP address
of the JupyterHub we just deployed.::

  kubectl --namespace=binder get svc proxy-public

Copy the IP address under ``EXTERNAL-IP``. This is the IP of your
JupyterHub. Now, add the following lines to ``config.yaml``.::

  hub:
    url: https://<IP in EXTERNAL-IP>

Now upgrade the helm chart with our changes.::

  helm upgrade binder jupyterhub/binderhub --version=v0.1.0-789e30a -f secret.yaml -f config.yaml

Try out your BinderHub Deployment
---------------------------------
If the ``helm upgrade`` command above succeeds, it's time to try out your
BinderHub deployment! First we'll find the IP address of the BinderHub
deployment. Run the following command::

  kubectl --namespace=binder get svc binder

Note the IP address in ``EXTERNAL-IP``. This is your BinderHub IP address.
Type that IP address in your browser and a BinderHub should be waiting there
for you.

You should now have a functioning BinderHub at the above IP address. For next
steps, see :doc:`debug` and :doc:`turn-off`.
