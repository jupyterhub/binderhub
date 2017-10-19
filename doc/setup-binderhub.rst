Set up BinderHub
================

BinderHub uses Helm Charts to set up the applications we'll use in our Binder
deployment. If you're curious about what Helm Charts are and how they're
used here, see the `Zero to JupyterHub guide
<https://zero-to-jupyterhub.readthedocs.io/en/latest/tools.html#helm>`_.

Below we'll cover how to configure your Helm Chart, and how to create your
BinderHub deployment.

Preparing to install
--------------------

To configure the Helm Chart we'll need to generate several pieces of
information and insert them into ``yaml`` files.

The first is the content of the JSON file created when we set up
the container registry. For more information on getting a registry password, see
:ref:`setup-registry`. We'll copy/paste the contents of this file in the steps
below.

Create two random tokens by running the following commands then copying the
outputs.::

    openssl rand -hex 32
    openssl rand -hex 32

.. note::

   This command is run **twice** because we need two different tokens.

Create ``secret.yaml`` file
---------------------------

Create a file called ``secret.yaml`` and enter the following::

  jupyterhub:
      hub:
        services:
          binder:
            apiToken: "<output of FIRST `openssl rand -hex 32` command>"
      proxy:
        secretToken: "<output of SECOND `openssl rand -hex 32` command>"
  registry:
    password: |
      <content of the JSON file downloaded earlier for the container registry from Service Accounts>
      <it will look something like the following (with actual values instead of empty strings)>
      {
      "type": "",
      "project_id": "",
      "private_key_id": "",
      "private_key": "",
      "client_email": "",
      "client_id": "",
      "auth_uri": "",
      "token_uri": "",
      "auth_provider_x509_cert_url": "",
      "client_x509_cert_url": ""
      }
  hub:
    services:
      binder:
        apiToken: "<output of FIRST `openssl rand -hex 32` command>"

.. tip::

   The content you put just after ``password: |`` must all line up at the same
   tab level.

.. tip::

   Don't forget the ``|`` after the ``password:`` label.

Create ``config.yaml``
----------------------

Create a file called ``config.yaml`` and enter the following::

  registry:
    prefix:  gcr.io/<google-project-id>/<prefix>
    enabled: true

  rbac:
     enabled: false
  jupyterhub:
     hub:
        rbac:
           enabled: false

.. note::

   **google-project-id**:
   Note that the ``google-project-id`` in the ``prefix:`` line is the project *ID*,
   not just the project name. Although the project name and project ID can be the same,
   sometimes these will differ (i.e. if you have created a project name that's been
   used before).

.. note::

   **`prefix`**:
   `<prefix>` can be any string, and will be appended to image names. We
   recommend something descriptive such as ``dev`` or ``prod``.

Install BinderHub
-----------------

First, get the latest helm chart for BinderHub.::

    helm repo add jupyterhub https://jupyterhub.github.io/helm-chart
    helm repo update

Next, **install the Helm Chart** using the configuration files
that you've just created. Do this by running the following command::

    helm install jupyterhub/binderhub --version=v0.1.0-789e30a --name=binder --namespace=binder -f secret.yaml -f config.yaml

.. note::

   ``--version`` refers to the version of the BinderHub **Helm Chart**.

.. note::

   ``name`` and ``namespace`` may be different, but we recommend using
   the same ``name`` and ``namespace`` to avoid confusion. We recommend
   something descriptive and short.

This installation step will deploy both a BinderHub and a JupyterHub, but
they are not yet set up to communicate with each other. We'll fix this in
the next step. Wait a few moments before moving on as the resources may take a
few minutes to be set up.

Connect BinderHub and JupyterHub
--------------------------------

In the google console, run the following command to print the IP address
of the JupyterHub we just deployed.::

  kubectl --namespace=binder get svc proxy-public

Copy the IP address under ``EXTERNAL-IP``. This is the IP of your
JupyterHub. Now, add the following lines to ``config.yaml`` file::

  hub:
    url: http://<IP in EXTERNAL-IP>

Next, upgrade the helm chart to deploy this change::

  helm upgrade binder jupyterhub/binderhub --version=v0.1.0-789e30a -f secret.yaml -f config.yaml

Try out your BinderHub Deployment
---------------------------------

If the ``helm upgrade`` command above succeeds, it's time to try out your
BinderHub deployment.

First, find the IP address of the BinderHub deployment by running the following
command::

  kubectl --namespace=binder get svc binder

Note the IP address in ``EXTERNAL-IP``. This is your BinderHub IP address.
Type this IP address in your browser and a BinderHub should be waiting there
for you.

You now have a functioning BinderHub at the above IP address. For next
steps, see :doc:`debug` and :doc:`turn-off`.
