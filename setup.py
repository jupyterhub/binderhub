import os

from setuptools import setup, find_packages
import subprocess

# get the version
version_ns = {}
here = os.path.dirname(__file__)
with open(os.path.join(here, 'binderhub', '_version.py')) as f:
    exec(f.read(), {}, version_ns)

with open(os.path.join(here, 'requirements.txt')) as f:
    requirements = [
        l.strip() in f.readlines()
        if not l.strip().startswith('#')
    ]

# Build our js and css files before packaging
subprocess.check_call(['npm', 'install'])
subprocess.check_call(['npm', 'run', 'webpack'])

setup(
    name='binderhub',
    version=version_ns['__version__'],
    python_requires='>=3.6',
    author='Project Jupyter Contributors',
    author_email='jupyter@googlegroups.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
)
