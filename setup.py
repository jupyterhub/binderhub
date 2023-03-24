import os
import sys

from jupyter_packaging import npm_builder, wrap_installers
from setuptools import find_packages, setup

# ensure the current directory is on sys.path
# so versioneer can be imported when pip uses
# PEP 517/518 build rules.
# https://github.com/python-versioneer/python-versioneer/issues/193
sys.path.append(os.path.dirname(__file__))

import versioneer

here = os.path.dirname(__file__)

# Representative files that should exist after a successful build
jstargets = [
    os.path.join(here, "binderhub", "static", "dist", "bundle.js"),
]

# Automatically rebuild assets in dist if js is modified
jsdeps = npm_builder(
    build_cmd="webpack",
    build_dir="binderhub/static/dist/",
    source_dir="binderhub/static/js/",
)
cmdclass = wrap_installers(
    pre_develop=jsdeps, pre_dist=jsdeps, ensured_targets=jstargets
)


with open(os.path.join(here, "requirements.txt")) as f:
    requirements = [
        line.strip() for line in f.readlines() if not line.strip().startswith("#")
    ]

with open(os.path.join(here, "README.md"), encoding="utf8") as f:
    readme = f.read()

setup(
    name="binderhub",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(cmdclass),
    python_requires=">=3.8",
    author="Project Jupyter Contributors",
    author_email="jupyter@googlegroups.com",
    license="BSD",
    url="https://binderhub.readthedocs.io/en/latest/",
    project_urls={
        "Documentation": "https://binderhub.readthedocs.io/en/latest/",
        "Funding": "https://jupyter.org/about",
        "Source": "https://github.com/jupyterhub/binderhub/",
        "Tracker": "https://github.com/jupyterhub/binderhub/issues",
    },
    # this should be a whitespace separated string of keywords, not a list
    keywords="reproducible science environments docker kubernetes",
    description="Turn a Git repo into a collection of interactive notebooks",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        # pycurl is an optional dependency which improves performance
        #
        # - pycurl requires both `curl-config` and `gcc` to be available when
        #   installing it from source.
        # - pycurl should always be used in production, but it's not relevant
        #   for building documentation which inspects the source code.
        #
        "pycurl": ["pycurl"],
    },
)
