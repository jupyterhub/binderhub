# About this folder

The Dockerfile in this folder is built by
[chartpress](https://github.com/jupyterhub/chartpress#readme), using the
requirements.txt file. The requirements.txt file is updated based on the
requirements.in file using [`pip-compile`](https://pip-tools.readthedocs.io).

## How to update requirements.txt

Use the "Run workflow" button at
https://github.com/jupyterhub/binderhub/actions/workflows/watch-dependencies.yaml.
