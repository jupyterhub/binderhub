# config file for testing with minikube-config.yaml
import subprocess
try:
    minikube_ip = subprocess.check_output(['minikube', 'ip']).decode('utf-8').strip()
except (subprocess.SubprocessError, FileNotFoundError):
    minikube_ip = '192.168.99.100'

c.BinderHub.hub_url = 'http://{}:30123'.format(minikube_ip)
c.BinderHub.hub_api_token = 'aec7d32df938c0f55e54f09244a350cb29ea612907ed4f07be13d9553d18a8e4'
c.BinderHub.docker_image_prefix = '127.0.0.1:5000/'
c.BinderHub.docker_registry_url = 'http://127.0.0.1:5000'
c.BinderHub.docker_push_secret = None
