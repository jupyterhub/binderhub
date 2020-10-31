# A development config to test a BinderHub deployment generally. It can be
# combined with with the auth specific config.

# Deployment assumptions:
# - BinderHub:  standalone local installation
# - JupyterHub: standalone k8s installation

import os
import subprocess
try:
    minikube_ip = subprocess.check_output(['minikube', 'ip']).decode('utf-8').strip()
except (subprocess.SubprocessError, FileNotFoundError):
    minikube_ip = '192.168.1.100'

c.BinderHub.hub_url = 'http://{}:30902'.format(minikube_ip)
c.BinderHub.hub_api_token = 'dummy-binder-secret-token'
c.BinderHub.use_registry = False
c.BinderHub.build_namespace = os.environ.get('K8S_NAMESPACE', 'binderhub-test')
