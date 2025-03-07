"""
This configuration file is mounted to be read by binderhub with the sole purpose
of loading chart configuration passed via "config" and "extraConfig".
"""

from functools import lru_cache

from ruamel.yaml import YAML


@lru_cache
def _read_chart_config():
    """
    Read chart configuration, mounted via a k8s Secret rendered by the chart.
    """
    yaml = YAML(typ="safe")
    with open("/etc/binderhub/mounted-secret/chart-config.yaml") as f:
        return yaml.load(f)


@lru_cache
def get_chart_config(config_path=None, default=None):
    """
    Returns the full chart configuration, or a section of it based on a config
    section's path like "config.BinderHub".
    """
    config = _read_chart_config()
    if not config_path:
        return config

    for key in config_path.split("."):
        if not isinstance(config, dict):
            # can't resolve full path,
            # parent section's config is is a scalar or null
            return default
        if key not in config:
            return default
        config = config[key]
    return config


# load the config object for traitlets based configuration
c = get_config()  # noqa

# load "config" (YAML values)
for section, value in get_chart_config("config").items():
    if not value:
        continue
    print(f"Loading config.{section}")
    c[section].update(value)

# load "extraConfig" (Python code)
for key, snippet in sorted(get_chart_config("extraConfig").items()):
    if not snippet:
        continue
    print(f"Running extraConfig.{key}")
    exec(snippet)
