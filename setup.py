import os

from setuptools import setup, find_packages
import subprocess

import versioneer


here = os.path.dirname(__file__)

with open(os.path.join(here, 'requirements.txt')) as f:
    requirements = [
        l.strip() for l in f.readlines()
        if not l.strip().startswith('#')
    ]
    # manually add pycurl here, see comment in requirements.txt
    requirements.append("pycurl")

with open(os.path.join(here, 'README.md'), encoding="utf8") as f:
    readme = f.read()

# Build our js and css files before packaging
if os.name == "nt":
    subprocess.check_call(['npm.cmd', 'install'])
    subprocess.check_call(['npm.cmd', 'run', 'webpack'])
else:
    subprocess.check_call(['npm', 'install'])
    subprocess.check_call(['npm', 'run', 'webpack'])

setup(
    name='binderhub',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    python_requires='>=3.6',
    author='Project Jupyter Contributors',
    author_email='jupyter@googlegroups.com',
    license='BSD',
    url='https://binderhub.readthedocs.io/en/latest/',
    project_urls={
        'Documentation': 'https://binderhub.readthedocs.io/en/latest/',
        'Funding': 'https://jupyter.org/about',
        'Source': 'https://github.com/jupyterhub/binderhub/',
        'Tracker': 'https://github.com/jupyterhub/binderhub/issues',
    },
    # this should be a whitespace separated string of keywords, not a list
    keywords="reproducible science environments docker kubernetes",
    description="Turn a Git repo into a collection of interactive notebooks",
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
)
