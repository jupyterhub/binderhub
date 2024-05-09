# A development config to test BinderHub locally without Kubernetes

This runs `repo2docker` locally (_not_ in a container), then launches the built container in a local JupyterHub configured with DockerSpawner (or any container spawner that can use local container images).

Install JupyterHub and dependencies

    pip install -r requirements.txt
    npm install -g configurable-http-proxy

Install local BinderHub from source

    pip install -e ../..

Run JupyterHub in one terminal

    jupyterhub --config=jupyterhub_config.py

BinderHub will be running as a managed JupyterHub service, go to http://localhost:8000
and you should be redirected to BinderHub.

If you want to test BinderHub with dummy authentication:

    export AUTHENTICATOR=dummy
    jupyterhub --config=jupyterhub_config.py
