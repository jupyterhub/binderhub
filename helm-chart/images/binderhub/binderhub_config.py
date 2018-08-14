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

c.BinderHub.debug = get_config('binder.debug.enabled', False)

c.BinderHub.docker_image_prefix = get_config('binder.registry.prefix')
if get_config('binder.use-registry'):
    c.BinderHub.docker_registry_host = get_config('binder.registry.host')
    if get_config('binder.registry.auth-host'):
        c.BinderHub.docker_auth_host = get_config('binder.registry.auth-host')
    c.BinderHub.docker_token_url = get_config('binder.registry.auth-token-url')

c.BinderHub.docker_push_secret = get_config('binder.push-secret')
c.BinderHub.build_namespace = os.environ['BUILD_NAMESPACE']

c.BinderHub.use_registry = get_config('binder.use-registry', True)
c.BinderHub.per_repo_quota = get_config('binder.per-repo-quota', 0)

c.BinderHub.builder_image_spec = get_config('binder.repo2docker-image')
c.BinderHub.build_node_selector = get_config('binder.build-node-selector', {})
c.BinderHub.log_tail_lines = get_config('binder.log-tail-lines', 100)

if os.path.exists('/etc/binderhub/config/binder.appendix'):
    with open('/etc/binderhub/config/binder.appendix') as f:
        c.BinderHub.appendix = f.read()

c.BinderHub.hub_url = os.environ['JUPYTERHUB_URL'] + '/'
c.BinderHub.hub_api_token = os.environ['JUPYTERHUB_API_TOKEN']

c.BinderHub.google_analytics_code = get_config('binder.google-analytics-code', None)
google_analytics_domain = get_config('binder.google-analytics-domain', None)
if google_analytics_domain:
    c.BinderHub.google_analytics_domain = google_analytics_domain

c.BinderHub.base_url = get_config('binder.base-url')

c.BinderHub.auth_enabled = get_config('binder.auth-enabled', False)
c.BinderHub.use_oauth = get_config('binder.use-oauth', False)

if get_config('dind.enabled', False):
    c.BinderHub.build_docker_host = 'unix://{}/docker.sock'.format(
        get_config('dind.host-socket-dir')
    )

github_hostname = get_config('github.hostname')
if github_hostname:
    c.GitHubRepoProvider.hostname = github_hostname

gitlab_hostname = get_config('gitlab.hostname')
if gitlab_hostname:
    c.GitHubRepoProvider.hostname = gitlab_hostname

template_variables = get_config('template.variables')
if template_variables:
    c.BinderHub.template_variables = template_variables
template_path = get_config('template.path')
if template_path:
    c.BinderHub.template_path = template_path
    static_path = get_config('template.static.path')
    if static_path:
        c.BinderHub.extra_static_path = static_path
    static_url_prefix = get_config('template.static.url-prefix')
    if static_url_prefix:
        c.BinderHub.extra_static_url_prefix = static_url_prefix

cors = get_config('binder.cors', {})
allow_origin = cors.get('allowOrigin')
if allow_origin:
    c.BinderHub.tornado_settings.update({
        'headers': {
            'Access-Control-Allow-Origin': allow_origin,
        }
    })

retries = get_config('binder.retries.count', None)
if retries is not None:
    c.Launcher.retries = retries

retry_delay = get_config('binder.retries.delay', None)
if retry_delay is not None:
    c.Launcher.retry_delay = retry_delay

for path in glob.glob('/etc/binderhub/config/extra-config.*.py'):
    load_subconfig(path)
