import os
import glob
import yaml

def get_config(key, default=None):
    """
    Find a config item of a given name & return it

    Parses everything as YAML, so lists and dicts are available too
    """
    path = os.path.join('/etc/binderhub/config', key)
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
            print(key, data)
            return data
    except FileNotFoundError:
        return default

c.BinderHub.debug = True

c.BinderHub.docker_image_prefix = get_config('binder.registry.prefix')

c.BinderHub.docker_push_secret = get_config('binder.push-secret')
c.BinderHub.build_namespace = os.environ['BUILD_NAMESPACE']

c.BinderHub.use_registry = get_config('binder.use-registry', True)

c.BinderHub.builder_image_spec = get_config('binder.repo2docker-image')
c.BinderHub.hub_url = get_config('binder.hub-url')
c.BinderHub.hub_api_token = os.environ['JUPYTERHUB_API_TOKEN']

c.BinderHub.google_analytics_code = get_config('binder.google-analytics-code', None)
google_analytics_domain = get_config('binder.google-analytics-domain', None)
if google_analytics_domain:
    c.BinderHub.google_analytics_domain = google_analytics_domain

c.BinderHub.base_url = get_config('binder.base-url')


###  Federation configuration, ###

# this is necessary when not a federation portal to self-register
c.BinderHub.cannonical_address = get_config('binder.cannonical-address', '')

# by default we are _never_ a federation portal, don't know any other binders,
# and do not allow to store known binder in cookies.
c.BinderHub.use_as_federation_portal = get_config('binder.use-as-federation-portal', False)
c.BinderHub.default_binders = get_config('binder.default-binder-list', [])
c.BinderHub.list_cookie_set_binders = get_config('binder.list-cookie-set-binders', False)

if get_config('dind.enabled', False):
    c.BinderHub.build_docker_host = 'unix://{}/docker.sock'.format(
        get_config('dind.host-socket-dir')
    )

cors = get_config('binder.cors', {})
allow_origin = cors.get('allowOrigin')
if allow_origin:
    c.BinderHub.tornado_settings.update({
        'headers': {
            'Access-Control-Allow-Origin': allow_origin,
        }
    })


for path in glob.glob('/etc/binderhub/config/extra-config.*.py'):
    load_subconfig(path)
