import os

from setuptools import setup, find_packages

# get the version
version_ns = {}
here = os.path.dirname(__file__)
with open(os.path.join(here, 'binderhub', '_version.py')) as f:
    exec(f.read(), {}, version_ns)

setup(
    name='binderhub',
    version=version_ns['__version__'],
    python_requires='>=3.5',
    author='Project Jupyter Contributors',
    author_email='jupyter@googlegroups.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'kubernetes==3.*',
        'escapism',
        'tornado',
        'traitlets',
        'docker',
        'jinja2',
        'prometheus_client',
    ]
)
