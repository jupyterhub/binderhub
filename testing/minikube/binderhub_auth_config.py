import os
here = os.path.abspath(os.path.dirname(__file__))
load_subconfig(os.path.join(here, 'binderhub_config.py'))

c.BinderHub.base_url = '/services/binder/'
c.BinderHub.auth_enabled = True
c.BinderHub.use_named_servers = False
c.BinderHub.builder_required = False

# configuration for service authentication
c.HubOAuth.api_token = c.BinderHub.hub_api_token
c.HubOAuth.api_url = c.BinderHub.hub_url + '/hub/api/'
c.HubOAuth.base_url = c.BinderHub.base_url
c.HubOAuth.hub_prefix = '/hub/'
c.HubOAuth.oauth_client_id = 'binder-oauth-client-test'
