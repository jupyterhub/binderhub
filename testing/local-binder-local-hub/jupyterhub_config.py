"""
A development config to test BinderHub locally.

Run `jupyterhub --config=binderhub_config.py` terminal
Host IP is needed in a few places
"""

import os
import socket

from dockerspawner import DockerSpawner

from binderhub.binderspawner_mixin import BinderSpawnerMixin


def random_port() -> int:
    """Get a single random port."""
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
hostip = s.getsockname()[0]
s.close()


# image & token are set via spawn options
class LocalContainerSpawner(BinderSpawnerMixin, DockerSpawner):
    pass


c.JupyterHub.spawner_class = LocalContainerSpawner
c.DockerSpawner.remove = True
c.DockerSpawner.allowed_images = "*"

c.Application.log_level = "DEBUG"
c.Spawner.debug = True
c.JupyterHub.authenticator_class = os.getenv("AUTHENTICATOR", "null")

auth_enabled = c.JupyterHub.authenticator_class != "null"
if auth_enabled:
    c.LocalContainerSpawner.auth_enabled = True
    c.LocalContainerSpawner.cmd = "jupyterhub-singleuser"
    c.JupyterHub.load_roles = [
        {
            "name": "user",
            "description": "Standard user privileges",
            "scopes": [
                "self",
                "access:services!service=binder",
            ],
        }
    ]
else:
    c.LocalContainerSpawner.cmd = "jupyter-notebook"

c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = hostip

binderhub_service_name = "binder"
binderhub_config = os.path.join(os.path.dirname(__file__), "binderhub_config.py")

binderhub_environment = {}
for env_var in ["JUPYTERHUB_EXTERNAL_URL", "GITHUB_ACCESS_TOKEN", "DOCKER_HOST"]:
    if os.getenv(env_var) is not None:
        binderhub_environment[env_var] = os.getenv(env_var)
    if auth_enabled:
        binderhub_environment["AUTH_ENABLED"] = "1"

binderhub_port = random_port()

c.JupyterHub.services = [
    {
        "name": binderhub_service_name,
        "admin": True,
        "command": [
            "python",
            "-mbinderhub",
            f"--config={binderhub_config}",
            f"--port={binderhub_port}",
        ],
        "url": f"http://localhost:{binderhub_port}",
        "environment": binderhub_environment,
    }
]
c.JupyterHub.default_url = f"/services/{binderhub_service_name}/"

c.JupyterHub.tornado_settings = {
    "slow_spawn_timeout": 0,
}

c.KubeSpawner.events_enabled = True
