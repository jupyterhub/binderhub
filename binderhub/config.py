from .base import BaseHandler


class ConfigHandler(BaseHandler):
    """Serve config"""

    def generate_config(self):
        config = dict()
        for repo_provider_class_alias, repo_provider_class in self.settings[
            "repo_providers"
        ].items():
            config[repo_provider_class_alias] = repo_provider_class.labels
            config[repo_provider_class_alias][
                "display_name"
            ] = repo_provider_class.display_name
            config[repo_provider_class_alias][
                "regex_detect"
            ] = repo_provider_class.regex_detect
        return config

    async def get(self):
        self.write(self.generate_config())
