# Configuration file for Sphinx to build our documentation to HTML.
#
# Configuration reference: https://www.sphinx-doc.org/en/master/usage/configuration.html
#
import datetime
import os
import sys
from os.path import dirname

# -- Project information -----------------------------------------------------
# ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
#
project = "BinderHub"
copyright = f"{datetime.date.today().year}, Project Jupyter Contributors"
author = "Project Jupyter Contributors"


# -- Setup system path for autodoc extensions --------------------------------
#
# We use autodoc to generate documentation in reference/, so we configure the
# system path to help autodoc detect the binderhub module.
#
git_repo_root = dirname(dirname(dirname(__file__)))
sys.path.insert(0, git_repo_root)


# -- General Sphinx configuration ---------------------------------------------------
# ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
#
extensions = [
    "autodoc_traits",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]
root_doc = "index"
source_suffix = [".md", ".rst"]
default_role = "literal"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]


# -- Options for HTML output -------------------------------------------------
# ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
#
html_logo = "_static/images/logo.png"
html_favicon = "_static/images/favicon.png"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# pydata_sphinx_theme reference: https://pydata-sphinx-theme.readthedocs.io/en/latest/
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "use_edit_page_button": True,
    "github_url": "https://github.com/jupyterhub/binderhub",
    "twitter_url": "https://twitter.com/mybinderteam",
}
html_context = {
    "github_user": "jupyterhub",
    "github_repo": "binderhub",
    "github_version": "main",
    "doc_path": "docs/source",
}


# -- Setup of redirects for internally relocated content  --------------------
#
# Each entry represent an `old` path that is now available at a `new` path
#
internal_redirects = [
    ("turn-off.html", "zero-to-binderhub/turn-off.html"),
    ("setup-registry.html", "zero-to-binderhub/setup-registry.html"),
    ("setup-binderhub.html", "zero-to-binderhub/setup-binderhub.html"),
    ("create-cloud-resources.html", "zero-to-binderhub/setup-prerequisites.html"),
]
internal_redirect_template = """
<!DOCTYPE html>
<html>
  <head>
    <title>Going to {new_url}</title>
    <link rel="canonical" href="{canonical_url}{new_url}"/>
    <meta name="robots" content="noindex">
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <meta http-equiv="refresh" content="0; url={new_url}"/>
  </head>
</html>
"""


def create_internal_redirects(app, docname):
    if app.builder.name in ("html", "readthedocs"):
        print(app.config["html_context"])
        canonical_url = app.config["html_context"].get("canonical_url", "")
        for old_name, new in internal_redirects:
            page = internal_redirect_template.format(
                new_url=new,
                canonical_url=canonical_url,
            )

            target_path = app.outdir + "/" + old_name
            if not os.path.exists(os.path.dirname(target_path)):
                os.makedirs(os.path.dirname(target_path))

            with open(target_path, "w") as f:
                f.write(page)


def setup(app):
    app.connect("build-finished", create_internal_redirects)
