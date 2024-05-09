"""
A development config to test BinderHub locally.

If you are running BinderHub manually (not via JupyterHub) run
`python -m binderhub -f binderhub_config.py`

Override the external access URL for JupyterHub by setting the
environment variable JUPYTERHUB_EXTERNAL_URL
Host IP is needed in a few places
"""

import os
import socket

from binderhub.build_local import LocalRepo2dockerBuild
from binderhub.quota import LaunchQuota

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
hostip = s.getsockname()[0]
s.close()

c.BinderHub.debug = True
c.BinderHub.use_registry = False
c.BinderHub.builder_required = False

c.BinderHub.build_class = LocalRepo2dockerBuild
c.BinderHub.push_secret = ""
c.BinderHub.launch_quota_class = LaunchQuota

c.BinderHub.about_message = "This is a local dev deployment without Kubernetes"
c.BinderHub.banner_message = (
    'See <a href="https://github.com/jupyterhub/binderhub">BinderHub on GitHub</a>'
)

c.BinderHub.hub_url_local = "http://localhost:8000"

# Assert that we're running as a managed JupyterHub service
# (otherwise c.BinderHub.hub_api_token is needed)
assert os.getenv("JUPYTERHUB_API_TOKEN")
c.BinderHub.base_url = os.getenv("JUPYTERHUB_SERVICE_PREFIX")
# JUPYTERHUB_BASE_URL may not include the host
# c.BinderHub.hub_url = os.getenv('JUPYTERHUB_BASE_URL')
c.BinderHub.hub_url = os.getenv("JUPYTERHUB_EXTERNAL_URL") or f"http://{hostip}:8000"

if os.getenv("AUTH_ENABLED") == "1":
    c.BinderHub.auth_enabled = True
