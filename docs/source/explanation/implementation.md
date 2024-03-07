# Implementation

The [binderhub-service](https://github.com/2i2c-org/binderhub-service/) Helm chart runs BinderHub, the Python software, as a standalone service to build and push images with [repo2docker], next to [JupyterHub].

The `binderhub-service` installation starts a `docker-api` pod on each of the user nodes via the following [DaemonSet definition](https://github.com/2i2c-org/binderhub-service/blob/main/binderhub-service/templates/docker-api/daemonset.yaml).

The `docker-api` pod setups and starts the [dockerd](https://docs.docker.com/engine/reference/commandline/dockerd/) daemon, that will then be accessible via a mounted unix socket on the node, by the `build pods`.

The `build pods` are created as a result of an image build request, and they must run on the same node as the builder pods to make use of the docker daemon. These pods mount a k8s Secret with the docker config file holding the necessary registry credentials so they can push to the container registry.

## Technical stack

[JupyterHub]: https://jupyterhub.readthedocs.io/en/stable/
[jupyterhub rbac]: https://jupyterhub.readthedocs.io/en/stable/rbac/index.html
[readthedocs]: https://readthedocs.org/
[sphinx]: https://www.sphinx-doc.org/en/master/
[sphinx-book-theme]: https://sphinx-book-theme.readthedocs.io/en/stable/
[myst-parser]: https://myst-parser.readthedocs.io/en/stable/
[github actions]: https://github.com/features/actions
[repo2docker]: https://github.com/jupyterhub/repo2docker
