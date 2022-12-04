# Configuration file for Sphinx to build our documentation to HTML.
#
# Configuration reference: https://www.sphinx-doc.org/en/master/usage/configuration.html
#
import datetime
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
    "sphinxext.opengraph",
    "sphinxext.rediraffe",
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


# -- Options for linkcheck builder -------------------------------------------
# ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder
#
linkcheck_ignore = [
    r"(.*)github\.com(.*)#",  # javascript based anchors
    r"(.*)/#%21(.*)/(.*)",  # /#!forum/jupyter - encoded anchor edge case
    r"https://github.com/[^/]*$",  # too many github usernames / searches in changelog
    "https://github.com/jupyterhub/binderhub/pull/",  # too many PRs in changelog
    "https://github.com/jupyterhub/binderhub/compare/",  # too many comparisons in changelog
]
linkcheck_anchors_ignore = [
    "/#!",
    "/#%21",
]


# -- Options for the opengraph extension -------------------------------------
# ref: https://github.com/wpilibsuite/sphinxext-opengraph#options
#
# This extension help others provide better thumbnails and link descriptions
# when they link to this documentation from other websites, such as
# https://discourse.jupyter.org.
#
# ogp_site_url is set automatically by RTD
ogp_image = "_static/images/logo.png"
ogp_use_first_image = True


# -- Options for the rediraffe extension -------------------------------------
# ref: https://github.com/wpilibsuite/sphinxext-rediraffe#readme
#
# This extensions help us relocated content without breaking links. If a
# document is moved internally, we should configure a redirect like below.
#
rediraffe_branch = "main"
rediraffe_redirects = {
    "turn-off": "zero-to-binderhub/turn-off",
    "setup-registry": "zero-to-binderhub/setup-registry",
    "setup-binderhub": "zero-to-binderhub/setup-binderhub",
    "create-cloud-resources": "zero-to-binderhub/setup-prerequisites",
}
