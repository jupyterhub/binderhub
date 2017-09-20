# Contributing

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the [Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html).

## Local deployment

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
