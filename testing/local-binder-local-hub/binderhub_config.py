######################################################################
## A development config to test BinderHub locally.
#
# Run `python3 -m binderhub -f binderhub_config.py` in one terminal
# Run `jupyterhub --config=binderhub_config.py` in another terminal

# If True JupyterHub will take care of running BinderHub as a managed service
RUN_BINDERHUB_AS_JUPYTERHUB_SERVICE = True

# Host IP is needed in a few places
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
hostip = s.getsockname()[0]
s.close()


######################################################################
## BinderHub config

from binderhub.binderspawner_mixin import BinderSpawnerMixin
from binderhub.build_local import LocalRepo2dockerBuild
import os


c.BinderHub.debug = True
c.BinderHub.use_registry = False
c.BinderHub.builder_required = False

c.BinderHub.build_class = LocalRepo2dockerBuild
c.BinderHub.push_secret = None

c.BinderHub.about_message = "<blink>Hello world.</blink>"
c.BinderHub.banner_message = 'This is headline <a href="#">news.</a>'

if RUN_BINDERHUB_AS_JUPYTERHUB_SERVICE:
    c.BinderHub.base_url = os.getenv('JUPYTERHUB_SERVICE_PREFIX')
    c.BinderHub.hub_url = os.getenv('JUPYTERHUB_BASE_URL')
else:
    c.BinderHub.hub_url = f'http://{hostip}:8000'
    # Shared with JupyterHub
    api_token = "secretsecretsecretsecretsecretsecret"
    c.BinderHub.hub_api_token = api_token


######################################################################
## JupyterHub config

from dockerspawner import DockerSpawner

# image & token are set via spawn options
class LocalContainerSpawner(BinderSpawnerMixin, DockerSpawner):
    pass


c.JupyterHub.spawner_class = LocalContainerSpawner
c.DockerSpawner.remove = True
c.LocalContainerSpawner.cmd = 'jupyter-notebook'

c.Application.log_level = 'DEBUG'
c.JupyterHub.Spawner.debug = True
c.JupyterHub.authenticator_class = "nullauthenticator.NullAuthenticator"

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = hostip

binderhub_service_name = 'binder'
if RUN_BINDERHUB_AS_JUPYTERHUB_SERVICE:
    c.JupyterHub.services = [{
        "name": binderhub_service_name,
        "admin": True,
        "command": ["python", "-mbinderhub", f"--config={__file__}"],
        "url": f"http://localhost:8585",
    }]
    c.JupyterHub.default_url = f"/services/{binderhub_service_name}/"
else:
    c.JupyterHub.services = [{
        "name": binderhub_service_name,
        "admin": True,
        "api_token": api_token,
    }]
