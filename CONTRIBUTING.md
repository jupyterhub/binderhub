# Contributing to BinderHub

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the
[Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributing/content-contributor.html).

Depending on what you want to develop, you can setup BinderHub in different ways.
- [Develop documentation](#develop-documentation).
- [Develop user interface](#develop-user-interface). A BinderHub webserver is running locally and
  JupyterHub is mocked, this setup doesn't involve Kubernetes.
- [Develop Kubernetes integration](#develop-kubernetes-integration). A BinderHub webserver is running locally,
  and JupyterHub is installed in a Kubernetes cluster.
- [Develop Helm chart](#develop-helm-chart) - The BinderHub Helm chart with JupyterHub as a
  dependency is installed in a Kubernetes cluster.

 This document also contains information on [how to run tests](#running-tests) and
 [common maintainer tasks](#common-maintainer-tasks).


## Develop documentation

You are assumed to have a modern version of [Python](https://www.python.org/).
The documentation uses the [reStructuredText markup
language](http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).

1. Clone the BinderHub repository to your local computer and `cd` into it.

   ```bash
   git clone https://github.com/jupyterhub/binderhub
   cd binderhub
   ```

1. Install BinderHub and the documentation tools:

   ```bash
   python3 -m pip install -r doc/doc-requirements.txt
   ```

1. The documentation is located in the `doc/` sub-directory, `cd` into it:

   ```bash
   cd ./doc
   ```

1. To build the documentation run:

   ```bash
   make html
   ```

1. Open the main documentation page in your browser, it is located at
   `_build/html/index.html`. On a Mac you can open it directly from the
   terminal with `open _build/html/index.html`.


## Develop user interface

Developing BinderHub's user interface can be done both without Kubernetes and
JupyterHub by mocking that interaction. You are assumed to have a modern version
of [Python](https://www.python.org/) and [node / npm](https://nodejs.org/)
installed.

1. Clone the BinderHub git repository to your local computer and `cd` into it.

   ```bash
   git clone https://github.com/jupyterhub/binderhub
   cd binderhub
   ```

1. Install BinderHub, the Python package.

   ```bash
   python3 -m pip install -e .
   ```

1. Install the NodeJS dependencies from package.json.

   ```bash
   npm install
   ```

1. Create the JS and CSS bundles BinderHub serves as a webserver to visitors.

   ```bash
   npm run webpack:watch
   ```

1. Start the BinderHub webserver locally.

   ```bash
   python3 -m binderhub -f testing/local-binder-mocked-hub/binderhub_config.py
   ```

1. Visit the BinderHub webserver at http://localhost:8585.

Building and launching repositories will not work. You can still work on the
user interface of those parts as BinderHub is configured to fake those actions.
You can tell you are using the fake builder and launcher from the fact that the
build will never complete.

To learn how to set yourself with a BinderHub development environment that lets
you modify the builder and launcher refer to [Develop Kubernetes
integration](#develop-kubernetes-integration) or [Develop Helm
chart](#develop-helm-chart).

## Develop Kubernetes integration

This requires `helm` and a functional Kubernetes cluster. Please do
[preliminary Kubernetes setup](#kubernetes-setup) if you haven't already
before continuing here.

With a Kubernetes cluster running, as you verify with `kubectl version`, you can
continue.

1. Locally install BinderHub as a Python package and its development
   requirements locally.

   ```bash
   python3 -m pip install -e . -r dev-requirements.txt
   ```

1. Install the JupyterHub Helm chart by itself into your Kubernetes cluster
   current namespace.

   ```bash
   # Append --auth here if you want to develop against a non-public BinderHub
   # that relies on JupyterHub's configured Authenticator to decide if the users
   # are allowed access or not.
   ./testing/local-binder-k8s-hub/install-jupyterhub-chart
   ```

1. Configure `docker` using environment variables to use the same Docker daemon
   as your `minikube` cluster. This means images you build are directly
   available to the cluster.

   ```bash
   eval $(minikube docker-env)
   ```

1. Start BinderHub with the testing config file.

   ```bash
   python3 -m binderhub -f testing/local-binder-k8s-hub/binderhub_config.py
   ```

1. Visit [http://localhost:8585](http://localhost:8585)

1. Congratulations, you can now make changes and see how they influence the
   deployment. You may be required to restart the BinderHub depending on what
   you change. You can also start running `pytest` tests to verify the
   Deployment functions as it should.


### Cleanup resources

1. To cleanup the JupyterHub Helm chart you have installed in Kubernetes...

   ```bash
   helm delete binderhub-test
   ```

1. To stop running the Kubernetes cluster...

   ```bash
   minikube stop
   ```

## Develop Helm chart

This requires `helm` and a functional Kubernetes cluster. Please do
[preliminary Kubernetes setup](#kubernetes-setup) if you haven't already
before continuing here.

With a Kubernetes cluster running, as you verify with `kubectl version`, you can
continue.

1. Install development requirements, including `pytest` and `chartpress`.

   ```bash
   python3 -m pip install -r dev-requirements.txt
   ```

1. Configure `docker` using environment variables to use the same Docker daemon
   as your `minikube` cluster. This means images you build are directly
   available to the cluster.

   ```bash
   eval $(minikube docker-env)
   ```

1. Build the docker images referenced by the Helm chart and update its default
   values to reference these images.

   ```bash
   (cd helm-chart && chartpress)
   ```

1. Validate, and then install the Helm chart defined in helm-chart/binderhub.

   This validation step is not making any modification to your Kubernetes
   cluster, but will use it to validate if the Helm chart's rendered resources
   are valid Kubernetes resources according to the Kubernetes cluster.

   ```bash
   helm template --validate binderhub-test helm-chart/binderhub \
      --values testing/k8s-binder-k8s-hub/binderhub-chart-config.yaml \
      --set config.BinderHub.hub_url=http://$(minikube ip):30902 \
      --set config.BinderHub.access_token=$GITHUB_ACCESS_TOKEN
   ```

   If the validation succeeds, go ahead and upgrade/install the Helm chart.

   ```bash
   helm upgrade --install binderhub-test helm-chart/binderhub \
      --values testing/k8s-binder-k8s-hub/binderhub-chart-config.yaml \
      --set config.BinderHub.hub_url=http://$(minikube ip):30902 \
      --set config.BinderHub.access_token=$GITHUB_ACCESS_TOKEN

   echo "BinderHub inside the Minikube based Kubernetes cluster is starting up at http://$(minikube ip):30901"
   ```

1. Congratulations, you can now make changes and run the step above again to see
   how they influence the deployment. You can also start running `pytest` tests
   to verify the Deployment functions as it should.

### Cleanup resources

1. To cleanup resources you have installed and start fresh...

   ```bash
   helm delete binderhub-test
   ```

1. To stop running the Kubernetes cluster...

   ```bash
   minikube stop
   ```

## Kubernetes setup

A fully functional BinderHub needs to have access to a Kubernetes cluster with a
JupyterHub installed on it. You can either run BinderHub as a Python webserver
locally and install JupyterHub on its own in the Kubernetes cluster, or install
the entire BinderHub Helm chart which installs the JupyterHub Helm chart as a
dependency.

All the steps are given as command-line commands for Ubuntu systems. They are
used as a common denominator that can be translated into the correct commands on
your local system.

You are assumed to have a modern version of [Python](https://www.python.org/),
[node / npm](https://nodejs.org/) installed, and the command line tool `curl`.

1. [Install Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/).

1. Start a minikube Kubernetes cluster inside a virtual machine (virtualbox,
   xhyve, or KVM2).

   ```bash
   minikube start
   ```

1. Install `kubectl` - the CLI to interact with a Kubernetes cluster.

   ```bash
   curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl
   sudo mv kubectl /usr/local/bin/
   ```

   Here are the [official installation instructions](https://kubernetes.io/docs/tasks/tools/install-kubectl/).

1. Install `helm` - the Kubernetes package manager.

   ```bash
   curl -sf https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
   ```

   Here are the [official installation instructions](https://helm.sh/docs/intro/install/).

1. Let `helm` know about the official JupyterHub Helm chart repository.

   ```bash
   helm repo add --force-update jupyterhub https://jupyterhub.github.io/helm-chart/
   helm repo update
   ```

1. Clone the binderhub git repository to your local computer and `cd` into it.

   ```bash
   git clone https://github.com/jupyterhub/binderhub
   cd binderhub
   ```

### Tip: Use local repo2docker version

BinderHub runs repo2docker in a container. For testing the combination of an
unreleased repo2docker feature with BinderHub, you can use a locally build
repo2docker image. You can configure the image in the file
`testing/local-binder-k8s-hub/binderhub_config.py` with the following line:

```python
c.BinderHub.build_image = 'jupyter-repo2docker:my_image_tag'
```

**Important**: the image must be build using the same Docker daemon as the
minikube cluster, otherwise you get an error _"Failed to pull image [...]
repository does not exist or may require 'docker login'"_.

### Tip: Increase your GitHub API limit

By default, GitHub has a limit of 60 API requests per hour. We recommend
using a GitHub API token before running tests
in order to avoid hitting your API limit. Steps to do so are outlined in
the [BinderHub documentation](https://binderhub.readthedocs.io/en/latest/setup-binderhub.html#increase-your-github-api-limit).

### Tip: Start Minikube with more memory

By default, `minikube start` allocates 2GiB of main memory to the
underlying VM, which might be too low to run the builder successfully.

You may run `minikube start --memory 8192` to start Minikube with a 8GiB
VM underneath.




## Running tests

This git repository contains `pytest` based tests that you can run locally.
Depending on your development setup, you may want to run different kind of
tests. You can get some hints on what tests to run and how by inspecting
`.travis.yaml`.

### Environment variables influencing tests
- `BINDER_URL`: An address of an already running BinderHub as reachable from the
  tests. If this is set, the test suite will not start temporary local BinderHub
  servers but instead interact with the remote BinderHub.
- `GITHUB_ACCESS_TOKEN`: A GitHub access token to help avoid quota limitations
  for anonymous users. It is used to enable certain tests making many calls to
  GitHub API.

### Pytest marks labelling tests
- `remote`: Tests for them the BinderHub is already running somewhere.
- `github_api`: Tests that communicate with the GitHub API a lot.
- `auth`: Tests related to BinderHub's usage of JupyterHub as an OAuth2 Identity
  Provider (IdP) for non public access.


## Common maintainer tasks

These are tasks that BinderHub maintainers perform.


### Bumping the JupyterHub Helm chart version

The BinderHub Helm chart depends on the [JupyterHub Helm
chart](https://jupyterhub.github.io/helm-chart/), and its version is pinned
within `helm-chart/binderhub/requirements.yaml`. It is straightforward to update
it with another version from the [JupyterHub Helm chart
repository](https://jupyterhub.github.io/helm-chart/).

Use the [JupyterHub Helm chart's
changelog](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/blob/master/CHANGELOG.md)
to prepare for breaking changes associated with the version bump.


### Releasing

#### BinderHub Python package release checklist

* update/close the `CHANGES.md` for this release (see below)
* create a git tag for the release
* `pip install twine`
* `python setup.py sdist`
* `python setup.py bdist_wheel`
* `twine check dist/*` to check the README parses on PyPI
* edit `$HOME/.pypirc` to use the binder team account
* `twine upload dist/*`
* create a new release on https://github.com/jupyterhub/binderhub/releases
* add a new section at the top of the change log for future releases

For more details, see this [guide on uploading package to
PyPI](https://packaging.python.org/guides/distributing-packages-using-setuptools/#uploading-your-project-to-pypi).

#### Updating the changelog

As BinderHub does not have a typical semver release schedule, we try to
update the changelog in `CHANGES.md` every three months. A useful tool
for this [can be found here](https://github.com/choldgraf/github-activity).
If you choose to use this tool, the command that generated current sections
in the changelog is below:

```bash
github-activity jupyterhub/binderhub -s <START-DATE> -u <END-DATE> --tags enhancement,bug --strip-brackets
```

Copy and paste the output of this command into a new section in `CHANGES.md`.
