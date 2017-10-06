# Contributing

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the [Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html).

## Local deployment

### With minikube

To develop binderhub, you can use a local installation of JupyterHub on minikube,
and run binderhub on the host system.

1. Follow [zero-to-jupyterhub](https://zero-to-jupyterhub.readthedocs.io/en/latest/setup-jupyterhub.html#install-jupyterhub) to setup minikube

2. deploy JupyterHub with helm

        helm install jupyterhub/jupyterhub --version=v0.5.x-2140cd6 \
            --name=binder \
            --namespace=binder \
            -f testing/minikube-config.yaml

3. install binderhub:

        python3 -m pip install -e .

4. start binderhub with the testing config file:

        python3 -m binderhub -f testing/binderhub_config.py

5. visit [http://localhost:8585](http://localhost:8585)

### With Google Cloud

1. Set up a project on google cloud to which you have access.
   Do this via `console.google.com`.

2. Install `gcloud` components as well as `kubectl` on your local machine.

   See [these instructions](https://cloud.google.com/sdk/downloads) for how
   to do this.

3. Add authorization to your local `gcloud` to connect with the cloud.

   `gcloud auth login`
   `gcloud auth application-default login`

4. Connect your local `gcloud` to the project you created in step 1.

   `gcloud config set project <project-name>`

4. Create a cluster

   `gcloud container clusters create <name-of-cluster> --num-nodes=2 --machine-type=n1-standard-2 --zone=<zone>`

   Or, if there is already a cluster that you would like to use instead

   `gcloud container clusters get-credentials <name-of-cluster> --zone=<zone>`

5. Install BinderHub:

   `python3 -m pip install -e .`

6. Start BinderHub with the testing config file:

   `python3 -m binderhub -f testing/binderhub_config.py`
