# About the documentation

This documentation is automatically built on each commit [as configured on
ReadTheDocs](https://readthedocs.org/projects/binderhub-service/) and in the
`.readthedocs.yaml` file, and made available on
[binderhub-service.readthedocs.io](https://binderhub-service.readthedocs.io/en/latest/).

The documentation is meant to be structured according to the Diataxis framework
as documented in https://diataxis.fr/.

## Local documentation development

```shell
cd docs
pip install -r requirements.txt

# automatic build and livereload enabled web-server
make devenv

# automatic check of links validity
make linkcheck
```
