"""
A development config to test BinderHub locally.

Run `jupyterhub --config=binderhub_config.py` terminal
Host IP is needed in a few places
"""
import os
import socket

from dockerspawner import DockerSpawner

from binderhub.binderspawner_mixin import BinderSpawnerMixin

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
hostip = s.getsockname()[0]
s.close()


# image & token are set via spawn options
class LocalContainerSpawner(BinderSpawnerMixin, DockerSpawner):
    pass


c.JupyterHub.spawner_class = LocalContainerSpawner
c.DockerSpawner.remove = True
c.LocalContainerSpawner.cmd = "jupyter-notebook"

c.Application.log_level = "DEBUG"
c.Spawner.debug = True
c.JupyterHub.authenticator_class = "nullauthenticator.NullAuthenticator"

c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = hostip

binderhub_service_name = "binder"
binderhub_config = os.path.join(os.path.dirname(__file__), "binderhub_config.py")

binderhub_environment = {}
for env_var in ["JUPYTERHUB_EXTERNAL_URL", "GITHUB_ACCESS_TOKEN"]:
    if os.getenv(env_var) is not None:
        binderhub_environment[env_var] = os.getenv(env_var)
c.JupyterHub.services = [
    {
        "name": binderhub_service_name,
        "admin": True,
        "command": ["python", "-mbinderhub", f"--config={binderhub_config}"],
        "url": "http://localhost:8585",
        "environment": binderhub_environment,
    }
]
c.JupyterHub.default_url = f"/services/{binderhub_service_name}/"

c.JupyterHub.tornado_settings = {
    "slow_spawn_timeout": 0,
}

c.KubeSpawner.events_enabled = True
