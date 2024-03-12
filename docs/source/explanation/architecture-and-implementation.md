(architecture-and-implementation)=
# Architecture and Implementation

## Architecture

The `binderhub-service` chart runs the [BinderHub] Python software, in [api-only mode](https://binderhub.readthedocs.io/en/latest/reference/app.html#binderhub.app.BinderHub.enable_api_only_mode) (the default), as a standalone service to build, and push [Docker] images from source code repositories, on demand, using [repo2docker]. This service can then be paired with [JupyterHub] to allow users to initiate build requests from their hubs. 

Thus, the architecture of this system must:
- facilitate the building and pushing of Docker images with repo2docker
- easily integrate with a JupyterHub deployment
- but also run as a standalone service
- operate within a Kubernetes environment

## Implementation details

% (This image was generated at the following URL: https://docs.google.com/presentation/d/1KC9cyXGPGBQoeZ0sLxHORyhjXDklIfn-rZ5SAdRB08Q/edit?usp=sharing) following the BinderHub architecture chart at https://docs.google.com/presentation/d/1t5W4Rnez6xBRz4YxCxWYAx8t4KRfUosbCjS4Z1or7rM/edit#slide=id.g25dbc82125_0_53

``` {figure} ../_static/images/binderhub-service-diagram.png
:alt: Here is a high-level overview of the components that make up binderhub-service.
```

When a build & push request is fired, the following events happen:

1. **BinderHub creates and starts a `build pod` that runs `repo2docker`**

   The `build pods` are managed by BinderHub through [`KubernetesBuildExecutor`](https://github.com/jupyterhub/binderhub/blob/7f8b6c3137a6f8e66e6c193ee81d32bcf0826a6e/binderhub/build.py#L222-L242) and are created as a result of an image build request.

   For the image build to work, the docker client processes running on these nodes need to be able to communicate with the dockerd daemon. This communication is done via unix socket mounted on the node.

2. **repo2docker uses Docker to build and push the images**

   A running [dockerd](https://docs.docker.com/engine/reference/commandline/dockerd/) daemon will intercept the docker commands initiated by the the docker client processes running on these build pods. This dockerd daemon is setup by the `docker-api` pods.

   The `docker-api` pods are setup to start on each node matching the [`dockerApi.nodeSelector`](https://github.com/2i2c-org/binderhub-service/blob/308965029a901993293539f159c66d15b767e8c8/binderhub-service/values.yaml#L131) by the following [DaemonSet definition](https://github.com/2i2c-org/binderhub-service/blob/main/binderhub-service/templates/docker-api/daemonset.yaml).

   The daemonset also setups a [hostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) volume that mounts a [unix socket](https://man7.org/linux/man-pages/man7/unix.7.html) from this node into the `docker-api` pods.

   ```{important}
   The docker-api pods and the build pods must run on the same node so they can use the unix socket on it to interact with the docker daemon listening on this socket.
   ```

3. **the build pods will then use the configured credentials to push the image to the repository**

    The build pods mount [**a k8s Secret** with the docker config file](https://github.com/2i2c-org/binderhub-service/blob/308965029a901993293539f159c66d15b767e8c8/binderhub-service/templates/secret.yaml#L5) holding the necessary registry credentials so they can push to the container registry.

```{warning}
The `binderhub-service` chart currently only supports Docker and Podman is not yet available. Checkout https://github.com/2i2c-org/binderhub-service/issues/31 for updates on Podmand support.
```

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
