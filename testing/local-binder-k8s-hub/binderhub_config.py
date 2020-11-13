# A development config to test a BinderHub deployment generally. It can be
# combined with with the auth specific config.

# Deployment assumptions:
# - BinderHub:  standalone local installation
# - JupyterHub: standalone k8s installation

import os
import subprocess

# We need to find out the IP at which BinderHub can reach the JupyterHub API
# For local development we recommend the use of minikube, but on GitHub
# Actions we use k3s. This means there are different ways of obtaining the IP.
# GITHUB_RUN_ID is an environment variable only set inside GH Actions, we
# don't care about its value, just that it is set
in_github_actions = os.getenv("GITHUB_RUN_ID") is not None

if in_github_actions:
    jupyterhub_ip = "localhost"

else:
    try:
        jupyterhub_ip = subprocess.check_output(['minikube', 'ip'], text=True).strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        jupyterhub_ip = '192.168.1.100'

c.BinderHub.debug = True
c.BinderHub.hub_url = 'http://{}:30902'.format(jupyterhub_ip)
c.BinderHub.hub_api_token = 'dummy-binder-secret-token'
c.BinderHub.use_registry = False
