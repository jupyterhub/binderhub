# A development config to test a BinderHub deployment generally. It can be
# combined with with the auth specific config.

# Deployment assumptions:
# - BinderHub:  standalone local installation
# - JupyterHub: standalone k8s installation

import logging
import os

logger = logging.getLogger(__name__)

# We need to find out the IP at which BinderHub can reach the JupyterHub API
# For local development we recommend the use of minikube, but on GitHub
# Actions we use k3s. This means there are different ways of obtaining the IP.
# GITHUB_RUN_ID is an environment variable only set inside GH Actions, we
# don't care about its value, just that it is set
in_github_actions = os.getenv("GITHUB_RUN_ID") is not None

if in_github_actions:
    jupyterhub_ip = "localhost"

else:
    jupyterhub_ip = os.getenv("LOCAL_BINDER_JUPYTERHUB_IP", None)

    if jupyterhub_ip is None:
        logger.warning(
            "LOCAL_BINDER_JUPYTERHUB_IP environment variable is missing. Using 'localhost' as JupyterHub's domain."
        )
        jupyterhub_ip = "localhost"

c.BinderHub.debug = True
c.BinderHub.hub_url = f"http://{jupyterhub_ip}:30902"
c.BinderHub.hub_api_token = "dummy-binder-secret-token"
c.BinderHub.use_registry = False
