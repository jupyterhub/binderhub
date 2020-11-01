# Contributing to BinderHub

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the
[Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributing/content-contributor.html).

Depending on what you want to develop, you can setup BinderHub in different ways.
- [Develop documentation](#).
- [Develop user interface](#). A BinderHub webserver is running locally and
  JupyterHub is mocked, this setup doesn't involve Kubernetes.
- [Develop Kubernetes integration](#). A BinderHub webserver is running locally,
  and JupyterHub is installed in a Kubernetes cluster.
- [Develop Helm chart](#) - The BinderHub Helm chart with JupyterHub as a
  dependency is installed in a Kubernetes cluster.


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
   Repeat this step if you change the source JS or CSS.

   ```bash
   npm run webpack
   ```

1. Start the BinderHub webserver locally.

   ```bash
   python3 -m binderhub -f testing/local-binder-mocked-hub/binderhub_config.py
   ```

1. Visit the BinderHub werbserver at http://localhost:8585.

Building and launching repositories will not work. You can still work on the
user interface of those parts as BinderHub is configured to fake those actions.
You can tell you are using the fake builder and launcher from the fact that the
build will never complete.

To learn how to set yourself with a BinderHub development environment that
lets you modify the builder and launcher refer to
[Kubernetes integration changes](#Kubernetes-integration-changes).


## Develop Kubernetes integration

Setting yourself up to develop the Kubernetes integration requires a few
one-time setup steps. These steps are described in the "One-time installation"
section below. Follow those first then return here for day to day development
procedures.


### Day to day development tasks

After having setup `minikube` and `helm` once, these are the tasks you need for
every day development.

* Start and stop minikube with `minikube start` and `minikube stop`.
* Install JupyterHub in `minikube` with helm `./testing/local-binder-k8s-hub/install-jupyterhub-chart`
* Setup `docker` to use the same Docker daemon as your minikube cluster `eval $(minikube docker-env)`
* Start BinderHub `python3 -m binderhub -f testing/local-binder-k8s-hub/binderhub_config.py`
* Visit your BinderHub at[http://localhost:8585](http://localhost:8585)

To execute most of our test suite you need a running minikube cluster. It does
not need to have anything installed on it though:

```bash
minikube start
pytest -svx -m "not auth_test"
```

The tests should generate familiar pytest like output and complete in a few
seconds.

To execute all the main tests use `./ci/test-main` which will setup a
JupyterHub on minikube for you. These tests will generate a lot of output and
take a few minutes to run. The tests will attempt to clean up after themselves
on your minikube cluster.

To execute the tests related to authentication use `./ci/test-auth` which will
setup a JupyterHub on minikube for you and use configuration files to configure
your BinderHub to require authentication. These tests will generate a lot of
output and take a few minutes to run. The tests will attempt to clean up after
themselves on your minikube cluster.

To manually test changes to the Helm chart you will have to build the chart,
all images involved and deploy it locally. Steps to do this:

1. start minikube
1. setup docker to user the minikube dockerd `eval $(minikube docker-env)`
1. build the helm chart `cd helm-chart && chartpress && cd ..`
1. install the BinderHub chart with

   ```
   helm upgrade --install binderhub-test \
      helm-chart/binderhub \
      -f testing/k8s-binder-k8s-hub/binderhub-chart-config.yaml
   ```

You can now access your BinderHub at: `http://192.168.99.100:30901`. If your
minikube instance has a different IP use `minikube ip` to find it. You will have
to use that IP in two places. Add `--set config.BinderHub.hub_url:
http://$IP:30902` to your `helm install` command and access your BinderHub at
`http://$IP:30901`. Replace `$IP` with the output of `minikube ip`.

To remove the deployment again: `helm delete binderhub-test`.


### One-time installation

To run the full BinderHub it needs to have access to a kubernetes cluster with a
JupyterHub installed on it. This is what we will setup in this section. All the
steps are given as command-line commands for Ubuntu systems. They are used as a
common denominator that can be translated into the correct commands on your
local system.

Before you begin, there are a few utilities that need to be installed.

```bash
sudo apt install python3 python3-pip npm curl
```

If you a on linux, you may additionally need to install socat for port
forwarding.

```bash
sudo apt install socat
```

1. Clone the binderhub repository to your local computer and `cd` into it.

   ```bash
   git clone https://github.com/jupyterhub/binderhub
   cd binderhub
   ```

1. [Install Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/).

1. Start a minikube Kubernetes cluster inside a virtual machine.

   ```bash
   # This require you have either virtualbox, xhyve, or KVM2 installed.
   minikube start
   ```

1. Install `helm` - the Kubernetes package manager.

   ```bash
   curl -sf https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
   ```

   [Alternative installation options](https://helm.sh/docs/intro/install/) are
   available.

1. Let `helm` know about the official JupyterHub Helm chart repository.

   ```bash
   helm repo add --force-update jupyterhub https://jupyterhub.github.io/helm-chart/
   helm repo update
   ```

1. Locally install BinderHub as a Python package and its development
   requirements locally.

   ```bash
   python3 -m pip install -e . -r dev-requirements.txt
   ```

1. Install the JupyterHub Helm chart by itself into your Kubernetes cluster.

   ```bash
   ./testing/local-binder-k8s-hub/install-jupyterhub-chart
   ```

1. Before running BinderHub locally, do the following.

   ```bash
   eval $(minikube docker-env)
   ```

   This command sets up `docker` to use the same Docker daemon as your minikube
   cluster does. This means images you build are directly available to the
   cluster.

   To undo this step, you can run the following.

   ```bash
   eval $(minikube docker-env -u)
   ```

1. Start BinderHub with the testing config file.

   ```bash
   python3 -m binderhub -f testing/local-binder-k8s-hub/binderhub_config.py
   ```

1. Visit [http://localhost:8585](http://localhost:8585)

With this setup, all features should work, including building and launching of
repositories.


### Tip: Use local repo2docker version

BinderHub runs repo2docker in a container. For testing the combination of an
unreleased repo2docker feature with BinderHub, you can use a locally build
repo2docker image. You can configure the image in the file
`testing/local-binder-k8s-hub/binderhub_config.py` with the following line:

```python
c.BinderHub.build_image = 'jupyter-repo2docker:my_image_tag'
```

**Important**: the image must be build using the same Docker daemon as the minikube cluster, otherwise you get an error _"Failed to pull image [...]  repository does not exist or may require 'docker login'"_.

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

## Common maintainer tasks

These are tasks that BinderHub maintainers perform.


### Bumping the JupyterHub Helm Chart version

BinderHub uses the [JupyterHub Helm Chart](https://jupyterhub.github.io/helm-chart/)
to install the proper version of JupyterHub. The version that is used is specified
in the BinderHub Meta Chart, `helm-chart/binderhub/requirements.yaml`.

To bump the version of JupyterHub that BinderHub uses, go to the [JupyterHub
Helm Chart](https://jupyterhub.github.io/helm-chart/) version page, find the
release hash that you want (e.g. `0.10.0`) and update the following field in the
`requirements.yaml` file.

**Make sure to double-check that there are no breaking changes in JupyterHub**.
Sometimes JupyterHub introduces breaking changes to its helm chart (such as the
structure of particular fields). Make sure that none of these changes have been
introduced, particularly when bumping major versions of JupyterHub.


### Releasing

Checklist for creating BinderHub releases. For PyPI packaging read https://packaging.python.org/guides/distributing-packages-using-setuptools/#uploading-your-project-to-pypi

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

### Bumping the changelog

As BinderHub does not have a typical semver release schedule, we try to
update the changelog in `CHANGES.md` every three months. A useful tool
for this [can be found here](https://github.com/choldgraf/github-activity).
If you choose to use this tool, the command that generated current sections
in the changelog is below:

```bash
github-activity jupyterhub/binderhub -s <START-DATE> -u <END-DATE> --tags enhancement,bug --strip-brackets
```

Copy and paste the output of this command into a new section in `CHANGES.md`.
