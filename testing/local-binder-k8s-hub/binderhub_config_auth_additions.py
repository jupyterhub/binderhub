# A development config to test a BinderHub deployment that is relying on
# JupyterHub's as an OAuth2 based Identity Provider (IdP) for Authentication and
# Authorization. JupyterHub is configured with its own Authenticator.

# Deployment assumptions:
# - BinderHub:  standalone local installation
# - JupyterHub: standalone k8s installation

import os
from urllib.parse import urlparse

# As this config file reference traitlet values (c.BinderHub.hub_api_token,
# c.BinderHub.hub_url) set in the more general config file, it must load the
# more general config file first.
here = os.path.abspath(os.path.dirname(__file__))
load_subconfig(os.path.join(here, "binderhub_config.py"))

# Additional auth related configuration
c.BinderHub.base_url = "/"
c.BinderHub.auth_enabled = True
url = urlparse(c.BinderHub.hub_url)
c.HubOAuth.hub_host = f"{url.scheme}://{url.netloc}"
c.HubOAuth.api_token = c.BinderHub.hub_api_token
c.HubOAuth.api_url = c.BinderHub.hub_url + "/hub/api/"
c.HubOAuth.base_url = c.BinderHub.base_url
c.HubOAuth.hub_prefix = c.BinderHub.base_url + "hub/"
c.HubOAuth.oauth_redirect_uri = "http://127.0.0.1:8585/oauth_callback"
c.HubOAuth.oauth_client_id = "service-binder"
# We declare this environment variable, as it is used to set
# c.HubAuth.access_scopes's default value of relevance.
#
# ref: https://github.com/jupyterhub/jupyterhub/blob/5997614f452a3cfebfa541800012a914d37f3ec8/jupyterhub/services/auth.py#L358-L378
#
os.environ["JUPYTERHUB_SERVICE_NAME"] = "binder"
