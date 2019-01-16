from urllib.parse import urlparse
import os
here = os.path.abspath(os.path.dirname(__file__))
load_subconfig(os.path.join(here, 'binderhub_config.py'))

c.BinderHub.base_url = '/'
c.BinderHub.auth_enabled = True
# configuration for authentication
hub_url = urlparse(c.BinderHub.hub_url)
c.HubOAuth.hub_host = '{}://{}'.format(hub_url.scheme, hub_url.netloc)
c.HubOAuth.api_token = c.BinderHub.hub_api_token
c.HubOAuth.api_url = c.BinderHub.hub_url + '/hub/api/'
c.HubOAuth.base_url = c.BinderHub.base_url
c.HubOAuth.hub_prefix = c.BinderHub.base_url + 'hub/'
c.HubOAuth.oauth_redirect_uri = 'http://127.0.0.1:8585/oauth_callback'
c.HubOAuth.oauth_client_id = 'binder-oauth-client-test'
