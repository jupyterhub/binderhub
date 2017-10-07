# Contributing

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the [Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html).

## Minikube

To develop binderhub, you can use a local installation of JupyterHub on minikube,
and run binderhub on the host system.

1. [Install Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/).

2. deploy JupyterHub with helm

        helm install jupyterhub/jupyterhub --version=v0.5.x-2140cd6 \
            --name=binder \
            --namespace=binder \
            -f testing/minikube/jupyterhub-helm-config.yaml

3. install binderhub:

        python3 -m pip install -e .

4. start binderhub with the testing config file:

        python3 -m binderhub -f testing/minikube/binderhub_config.py

5. visit [http://localhost:8585](http://localhost:8585)

All features should work, including building and launching.

## Pure HTML / CSS / JS development

If you do not want to set up minikube but just want to hack on the html / css / js,
there is a simpler method!

1. Install binderhub:

   ```bash
   python3 -m pip install -e .
   ```

2. Run it!

   ```bash
   python3 -m binderhub.app -f testing/localonly/binderhub_config.py
   ```

3. You can now access it locally at https://localhost:8585

Note that building and launching will not work!
