# Implementation

The [binderhub-service](https://github.com/2i2c-org/binderhub-service/) Helm chart runs BinderHub, the Python software, as a standalone service to build and push images with [repo2docker], next to [JupyterHub].

The following main resource components are most relevant for how the machinery works:

## The binderhub service


## The DaemonSet resource - DockerApi

The `binderhub-service` installation starts a `docker-api` pod on each of the user nodes via the following [DaemonSet definition](https://github.com/2i2c-org/binderhub-service/blob/main/binderhub-service/templates/docker-api/daemonset.yaml). The daemonset also setups a [hostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) volume that mounts a [unix socket](https://man7.org/linux/man-pages/man7/unix.7.html) from the user node into the `docker-api` pods.

The `docker-api` pod setups and starts the [dockerd](https://docs.docker.com/engine/reference/commandline/dockerd/) daemon, that will then be accessible via this unix socket by the `build pods`.

```{warning}
The `binderhub-service` chart currently support only Docker and not yet Podman. Checkout https://github.com/2i2c-org/binderhub-service/issues/31 for updates on Podmand support.
```

### The build pods

The `build pods` are managed by BinderHub through [`KubernetesBuildExecutor`](https://github.com/jupyterhub/binderhub/blob/7f8b6c3137a6f8e66e6c193ee81d32bcf0826a6e/binderhub/build.py#L222-L242) and are created as a result of an image build request. They must run on the same node as the builder pods to make use of the docker daemon. These pods mount **a k8s Secret** with the docker config file holding the necessary registry credentials so they can push to the container registry.

## Technical stack

[JupyterHub]: https://jupyterhub.readthedocs.io/en/stable/
[jupyterhub rbac]: https://jupyterhub.readthedocs.io/en/stable/rbac/index.html
[readthedocs]: https://readthedocs.org/
[sphinx]: https://www.sphinx-doc.org/en/master/
[sphinx-book-theme]: https://sphinx-book-theme.readthedocs.io/en/stable/
[myst-parser]: https://myst-parser.readthedocs.io/en/stable/
[github actions]: https://github.com/features/actions
[repo2docker]: https://github.com/jupyterhub/repo2docker
