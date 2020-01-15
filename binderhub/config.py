import os
import json

from tornado.log import app_log

from .base import BaseHandler

config = {
    "gh": {
       "text": "GitHub repository name or URL",
       "tag_text": "Git ref (branch, tag, or commit)",
       "ref_prop_disabled": False,
       "label_prop_disabled": False,
    },
    "gist": {
        "text": "Gist ID (username/gistId) or URL",
        "tag_text": "Git commit SHA",
        "ref_prop_disabled": False,
        "label_prop_disabled": False,

    },
    "gl": {
        "text": "GitLab repository name or URL",
        "tag_text": "Git ref (branch, tag, or commit)",
        "ref_prop_disabled": False,
        "label_prop_disabled": False,
    },
    "git": {
        "text": "Arbitrary git repository URL (http://git.example.com/repo)",
        "tag_text": "Git ref (branch, tag, or commit) SHA",
        "ref_prop_disabled": False,
        "label_prop_disabled": False,
    },
    "zenodo": {
        "text": "Zenodo DOI (10.5281/zenodo.3242074)",
        "tag_text": "Git ref (branch, tag, or commit)",
        "ref_prop_disabled": True,
        "label_prop_disabled": True,
    },
    "figshare": {
        "text": "Figshare DOI (10.6084/m9.figshare.9782777.v1)",
        "tag_text": "Git ref (branch, tag, or commit)",
        "ref_prop_disabled": True,
        "label_prop_disabled": True,
    },
    "dataverse": {
        "text": "Dataverse DOI (10.7910/DVN/TJCLKP)",
        "tag_text": "Git ref (branch, tag, or commit)",
        "ref_prop_disabled": True,
        "label_prop_disabled": True,
    },
}


class ConfigHandler(BaseHandler):
    """Serve config"""

    async def get(self):
        cfg = json.dumps(config)
        loaded_r = json.loads(cfg)
        self.write(loaded_r)