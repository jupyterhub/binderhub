# Contributing to BinderHub

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the
[Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributing/content-contributor.html).

There are several different setups for developing BinderHub, depending on which
parts of it you want to change: the [documentation](#documentation-changes),
the [user interface](#user-innterface-changes), or the
[kubernetes integration](#Kubernetes-integration-changes).


## Documentation changes

Work on the documentation requires the least amount of setup. You will need
to have a modern version of [Python](https://www.python.org/). The documentation
uses the [reStructuredText markup language](http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).

1. Clone the BinderHub repository to your local computer and ```cd``` into it.
   ```bash
   git clone https://github.com/jupyterhub/binderhub
   cd binderhub
   ```
1. 1. Install BinderHub and the documentation tools:

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


## User interface changes

Work on the user interface requires a medium amount of setup. You will need
to have a modern version of [Python](https://www.python.org/) and
[npm](https://www.npmjs.com) installed.

1. Clone the BinderHub repository to your local computer and ```cd``` into it.
   ```bash
   git clone https://github.com/jupyterhub/binderhub
   cd binderhub
   ```

1. Install BinderHub:

   ```bash
   python3 -m pip install -e .
   ```

1. Install the JavaScript dependencies:

   ```bash
   npm install
   ```

1. Create the JS and CSS bundles with:

   ```bash
   npm run webpack
   ```
  Note: you need to run this every time you make a change to the CSS or JS
  for it to take effect.

1. Run it!

   ```bash
   python3 -m binderhub -f testing/localonly/binderhub_config.py
   ```

1. Visit http://localhost:8585 to see it in action.

Building and launching repositories will not work. You can still work on the
user interface of those parts as BinderHub is configured to fake those
actions. You can tell you are using the fake builder and launcher from the fact
that the build will never complete.

To learn how to set yourself with a BinderHub development environment that
lets you modify the builder and launcher refer to
[Kubernetes integration changes](#Kubernetes-integration-changes).


## Kubernetes integration changes

Setting yourself up to make changes to the kubernetes integration of BinderHub
requires a few one-time setup steps. These steps are described in the
"One-time installation" section below. Follow those first then return here for
day to day development procedures.


### Day to day development tasks

After having setup minikube and helm once, these are the tasks you need for
every day development.

* Start and stop minikube with `minikube start` and `minikube stop`.
* Install JupyterHub in minikube with helm `./testing/minikube/install-hub`
* Setup `docker` to use the same Docker daemon as your minikube cluster `eval $(minikube docker-env)`
* Start BinderHub `python3 -m binderhub -f testing/minikube/binderhub_config.py`
* Visit your BinderHub at[http://localhost:8585](http://localhost:8585)

To execute most of our test suite you need a running minikube cluster.
It does not need to have anything installed on it though:

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
helm install \
  --name binder-test \
  --namespace binder-test-helm \
  helm-chart/binderhub \
  -f helm-chart/minikube-binder.yaml
```

You can now access your BinderHub at: `http://192.168.99.100:30901`. If your
minikube instance has a different IP use `minikube ip` to find it. You will
have to use that IP in two places. Add `--set config.BinderHub.hub_url: http://$IP:30902`
to your `helm install` command and access your BinderHub at `http://$IP:30901`.
Replace `$IP` with the output of `minikube ip`.

To remove the deployment again: `helm delete --purge binder-test`.


### One-time installation

To run the full BinderHub it needs to have access to a kubernetes cluster
with a JupyterHub installed on it. This is what we will setup in this section.
All the steps are given as command-line commands for Ubuntu systems. They are
used as a common denominator that can be translated into the correct commands
on your local system.

Before you begin, there are a few utilities that need to be installed:
```bash
sudo apt install python3 python3-pip npm curl
```

If you a on linux, you may additionally need to install socat for port forwarding:

```bash
sudo apt install socat
```

1. Clone the binderhub repository to your local computer and ```cd``` into it.
   ```bash
   git clone https://github.com/jupyterhub/binderhub
   cd binderhub
   ```

1. [Install Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/)
   to run Kubernetes locally.

   To start your minikube cluster , run the command: `minikube start`. This
   starts a local kubernetes cluster inside a virtual machine. This command
   assumes that you have already installed one of the VM drivers: virtualbox,
   xhyve or KVM2.
1. Install helm to manage installing JupyterHub and BinderHub on your cluster,

   ```bash
   curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
   ```

   [Alternative methods](https://docs.helm.sh/using_helm/#installing-the-helm-client)
   for helm installation exist if you prefer installing without using the script.

1. Initialize helm in minikube. This command initializes the local CLI and
   installs Tiller on your kubernetes cluster in one step:

   ```bash
   helm init
   ```

1. Add the JupyterHub helm charts repo:

   ```bash
   helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
   helm repo update
   ```

1. Install BinderHub and its development requirements:

    ```bash
    python3 -m pip install -e . -r dev-requirements.txt
    ```

1. Install JupyterHub in minikube with helm

   ```bash
   ./testing/minikube/install-hub
   ```

1. Before starting your local deployment run:

   ```bash
   eval $(minikube docker-env)
   ```

  This command sets up `docker` to use the same Docker daemon as your minikube
  cluster does. This means images you build are directly available to the
  cluster. Note: when you no longer wish to use the minikube host, you can
  undo this change by running:

   ```bash
   eval $(minikube docker-env -u)
   ```

1. Start BinderHub with the testing config file:

    ```bash
    python3 -m binderhub -f testing/minikube/binderhub_config.py
    ```

1. Visit [http://localhost:8585](http://localhost:8585)

All features should work, including building and launching of repositories.


### Tip: Use local repo2docker version

BinderHub runs repo2docker in a container.
For testing the combination of an unreleased repo2docker feature with BinderHub, you can use a locally build repo2docker image.
You can configure the image in the file `testing/minikube/binderhub_config.py` with the following line:

```python
c.BinderHub.build_image = 'jupyter-repo2docker:my_image_tag'
```

**Important**: the image must be build using the same Docker daemon as the minikube cluster, otherwise you get an error _"Failed to pull image [...]  repository does not exist or may require 'docker login'"_.

### Tip: Enable debug logging

In the file `testing/minikube/binderhub_config.py` add the following line:

```python
c.BinderHub.debug = True
```

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

To bump the version of JupyterHub that BinderHub uses, go to the [JupyterHub Helm Chart](https://jupyterhub.github.io/helm-chart/) version page, find the release
hash that you want (e.g. `0.6.0-2c53640`) and update the following field in
the `requirements.yaml` file:

   ```yaml
   dependencies:
     version: "<helm-chart-version>"
   ```

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
