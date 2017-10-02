from setuptools import setup, find_packages

setup(
    name='binderhub',
    version='0.1',
    install_requires=[
        'kubernetes==3.*',
        'tornado',
        'traitlets',
        'docker',
        'jinja2',
        'prometheus_client'
    ],
    python_requires='>=3.5',
    author='Project Jupyter Contributors',
    author_email='jupyter@googlegroups.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
)
