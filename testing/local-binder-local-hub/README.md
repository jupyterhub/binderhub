# A development config to test BinderHub locally without Kubernetes

This runs `repo2docker` locally (_not_ in a container), then launches the built container in a local JupyterHub configured with DockerSpawner (or any container spawner that can use local container images).

Install JupyterHub and dependencies

    pip install -r requirements.txt
    npm install -g configurable-http-proxy

Install local BinderHub from source

    pip install -e ../..

Run JupyterHub in one terminal

    jupyterhub --config=binderhub_config.py

Run BinderHub in another terminal

    python3 -m binderhub -f binderhub_config.py
