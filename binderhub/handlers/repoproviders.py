import json

from ..base import BaseHandler


class RepoProvidersHandlers(BaseHandler):
    """Serve config"""

    async def get(self):
        config = [
            repo_provider_class.display_config
            for repo_provider_class in self.settings["repo_providers"].values()
        ]
        self.set_header("Content-type", "application/json")
        self.write(json.dumps(config))
