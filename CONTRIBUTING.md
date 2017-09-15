# Contributing

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the [Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html).

## Local deployment

To develop binderhub, you can use a local installation of JupyterHub on minikube,
and run binderhub on the host system.

1. Follow [zero-to-jupyterhub](https://zero-to-jupyterhub.readthedocs.io/en/latest/setup-jupyterhub.html#install-jupyterhub) to setup minikube

2. deploy JupyterHub with helm

        helm install jupyterhub/jupyterhub --version=v0.4 \
            --name=binder \
            --namespace=binder \
            -f minikube-config.yaml

3. record the public port of the proxy-public service (`30269` in this case):

        $ kubectl get svc proxy-public --namespace=binder
        NAME           CLUSTER-IP   EXTERNAL-IP   PORT(S)        AGE
        proxy-public   10.0.0.144   <pending>     80:30269/TCP   26m

4. get the public ip of minikube:

        $ minikube ip
        192.168.99.100

5. make `binderhub_config.py` with:

    ```python
    c.BinderHub.use_registry = False
    c.BinderHub.hub_url = 'http://<minikube-ip>:<proxy-public-port>/'
    ```
6. install binderhub:

        python3 -m pip install -e .

7. start binderhub:

        python3 -m binderhub

8. visit [http://localhost:8585](http://localhost:8585)
