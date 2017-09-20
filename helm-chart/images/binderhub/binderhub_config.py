import os
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
