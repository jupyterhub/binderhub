(architecture-and-implementation)=
# Architecture and Implementation

## The architecture

The `binderhub-service` chart runs the [BinderHub] Python software, in [api-only mode](https://binderhub.readthedocs.io/en/latest/reference/app.html#binderhub.app.BinderHub.enable_api_only_mode) (the default), as a standalone service to build, and push [Docker] images from source code repositories, on demand, using [repo2docker]. This service can then be paired with [JupyterHub] to allow users to initiate build requests from their hubs. 

Thus, the architecture of this system must:
- facilitate the building and pushing of Docker images with repo2docker
- easily integrate with a JupyterHub deployment
- but also run as a standalone service
- operate within a Kubernetes environment

### What happens when a build & push request is fired

1. BinderHub creates and starts a `build pod`
2. this build pod needs to be able to run `repo2docker` to build and push the image to the registry that was setup via the config
3. for this, repo2docker needs Docker to build and push the images
4. a running daemon will intercept the docker commands initiated by the the docker client processes running on these build pods
5. these build pods will then use the configured credentials to push the image to the repository.

## Implementation details

The following main resource components are most relevant for how the machinery works:

### The binderhub service


### The DaemonSet resource - DockerApi

The `binderhub-service` installation starts a `docker-api` pod on each of the user nodes via the following [DaemonSet definition](https://github.com/2i2c-org/binderhub-service/blob/main/binderhub-service/templates/docker-api/daemonset.yaml). The daemonset also setups a [hostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) volume that mounts a [unix socket](https://man7.org/linux/man-pages/man7/unix.7.html) from the user node into the `docker-api` pods.

The `docker-api` pod setups and starts the [dockerd](https://docs.docker.com/engine/reference/commandline/dockerd/) daemon, that will then be accessible via this unix socket by the `build pods`.

```{warning}
The `binderhub-service` chart currently support only Docker and not yet Podman. Checkout https://github.com/2i2c-org/binderhub-service/issues/31 for updates on Podmand support.
```

#### The build pods

The `build pods` are managed by BinderHub through [`KubernetesBuildExecutor`](https://github.com/jupyterhub/binderhub/blob/7f8b6c3137a6f8e66e6c193ee81d32bcf0826a6e/binderhub/build.py#L222-L242) and are created as a result of an image build request. They must run on the same node as the builder pods to make use of the docker daemon. These pods mount **a k8s Secret** with the docker config file holding the necessary registry credentials so they can push to the container registry.

## Technical stack

[BinderHub]: https://binderhub.readthedocs.io/en/latest/index.html
[JupyterHub]: https://jupyterhub.readthedocs.io/en/stable/
[jupyterhub rbac]: https://jupyterhub.readthedocs.io/en/stable/rbac/index.html
[readthedocs]: https://readthedocs.org/
[sphinx]: https://www.sphinx-doc.org/en/master/
[sphinx-book-theme]: https://sphinx-book-theme.readthedocs.io/en/stable/
[myst-parser]: https://myst-parser.readthedocs.io/en/stable/
[github actions]: https://github.com/features/actions
[repo2docker]: https://github.com/jupyterhub/repo2docker
[Docker]: https://binderhub.readthedocs.io/en/latest/index.html
