from functools import lru_cache
from urllib.parse import urlparse

from ruamel.yaml import YAML

yaml = YAML()


# memoize so we only load config once
@lru_cache
def _load_values():
    """Load configuration from disk

    Memoized to only load once
    """
    path = "/etc/binderhub/config/values.yaml"
    print(f"Loading {path}")
    with open(path) as f:
        return yaml.load(f)


def get_value(key, default=None):
    """
    Find an item in values.yaml of a given name & return it

    get_value("a.b.c") returns values['a']['b']['c']
    """
    # start at the top
    value = _load_values()
    # resolve path in yaml
    for level in key.split("."):
        if not isinstance(value, dict):
            # a parent is a scalar or null,
            # can't resolve full path
            return default
        if level not in value:
            return default
        else:
            value = value[level]
    return value


# load custom templates, by default
c.BinderHub.template_path = "/etc/binderhub/templates"

# load config from values.yaml
for section, sub_cfg in get_value("config", {}).items():
    c[section].update(sub_cfg)

imageBuilderType = get_value("imageBuilderType")
if imageBuilderType in ["dind", "pink"]:
    hostSocketDir = get_value(f"{imageBuilderType}.hostSocketDir")
    if hostSocketDir:
        socketname = "docker" if imageBuilderType == "dind" else "podman"
        c.BinderHub.build_docker_host = f"unix://{hostSocketDir}/{socketname}.sock"

if c.BinderHub.auth_enabled:
    if "hub_url" not in c.BinderHub:
        c.BinderHub.hub_url = ""
    hub_url = urlparse(c.BinderHub.hub_url)
    c.HubOAuth.hub_host = f"{hub_url.scheme}://{hub_url.netloc}"
    if "base_url" in c.BinderHub:
        c.HubOAuth.base_url = c.BinderHub.base_url

# load extra config snippets
for key, snippet in sorted((get_value("extraConfig") or {}).items()):
    print(f"Loading extra config: {key}")
    exec(snippet)
