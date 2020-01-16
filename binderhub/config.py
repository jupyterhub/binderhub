from tornado.log import app_log
from .base import BaseHandler

class ConfigHandler(BaseHandler):
    """Serve config"""
    def initialize(self, repo_providers=None):
        self.repo_providers = repo_providers

    def generate_config(self):
        config = dict()
        for repo_provider_class_alias, repo_provider_class in self.repo_providers.items():
            config[repo_provider_class_alias] = repo_provider_class.labels
        return config

    async def get(self):
        self.write(self.generate_config())