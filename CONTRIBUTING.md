# Contributing

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the [Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html).

To develop binderhub, you can use a local installation of JupyterHub on minikube,
and run binderhub on the host system.  Note that you will quickly hit your API limit
on GitHub if you don't have a token.

## Installation

Before you begin, there are a few utilities that need to be installed:
```bash
sudo apt install python3 python3-pip npm curl
```
You will need docker installed from https://docs.docker.com/install/ to run JupyterHub.
If you a on linux, you may additionally need to install socat for port forwarding:

```bash
sudo apt install socat
```

1. Clone the binderhub repository to your local computer and ```cd``` into it.
   ```bash
   git clone https://github.com/jupyterhub/binderhub
   cd binderhub
   ```

1. [Install Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/) to run Kubernetes locally.

   For MacOS, you may find installing from https://github.com/kubernetes/minikube/releases may be
   more stable than using Homebrew.

   To start your cluster on minikube, run the command: `minikube start`, this starts a local kubernetes cluster using VM. This command assumes that you have already installed one of the VM drivers: virtualbox/xhyve/KVM2.

1. Install helm to manage installing and running binderhub on your cluster,

   ```bash
   curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
   ```

   [Alternative methods](https://docs.helm.sh/using_helm/#installing-the-helm-client) for helm installation
   exist if you prefer installing without using the script.

1. Initialize helm in minikube. This command initializes the local CLI and installs Tiller on your kubernetes cluster in one step:

   ```bash
   helm init
   ```
1. Add the JupyterHub helm charts repo:

   ```bash
   helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
   helm repo update
   ```

1. Install binderhub and its development requirements:

    ```bash
    python3 -m pip install -e . -r dev-requirements.txt
    ```

    This list of packages is necessary to create an environment that will generate the Docker image using the Git repository. Regardless of what is in the setup.py file, the requirements file will install what the user needs to build the Docker image.

1. Install JupyterHub in minikube with helm

   ```bash
   ./testing/minikube/install-hub
   ```

1. Before starting the local dev/test deployment run:

   ```bash
   eval $(minikube docker-env)
   ```

    This command sets up docker to use the same docker daemon as your minikube cluster does. This means images you build are directly available to the cluster.
    Note: when you no longer wish to use the minikube host, you can undo this change by running:

   ```bash
   eval $(minikube docker-env -u)
   ```

1. Start binderhub with the testing config file:

    ```bash
    python3 -m binderhub -f testing/minikube/binderhub_config.py
    ```

1. Visit [http://localhost:8585](http://localhost:8585)

All features should work, including building and launching.

### Debugging tips

There is an option to configure the disk size of the minikube VM on start using the flag `minikube start --disk-size string` the default value is "20g".

If you get a Disk Available error you can run `minikube delete` and then reinstall binderhub following the installation guide above.

## Increase your GitHub API limit

By default, GitHub has a limit of 60 API requests per hour. We recommend
using a GitHub API token before running tests
in order to avoid hitting your API limit. Steps to do so are outlined in
the [BinderHub documentation](https://binderhub.readthedocs.io/en/latest/setup-binderhub.html#increase-your-github-api-limit).

## Testing

To run unit tests, navigate to the root of the repository, then call:

   ```bash
   pytest
   ```

We recommend increasing your GitHub API rate limit before running tests (see above).

## Building JS and CSS

We use [npm](https://www.npmjs.com) for managing our JS / CSS dependencies and
[webpack](https://webpack.js.org/) for bundling them together. You need to have
a recent version of `npm` installed to run things locally.

1. Run `npm install`. This should fetch and install all our frontend dependencies.
2. Run `npm run webpack`. This runs webpack and creates our JS / CSS bundles. You
   *need* to run this every time you make CSS / JS changes to see them live. Alternatively,
   you can run `npm run webpack:watch` to automatically rebuild JS / CSS changes as
   you make them.

## Pure HTML / CSS / JS development

If you do not want to set up minikube but just want to hack on the html / css / js,
there is a simpler method!

1. Install binderhub:

   ```bash
   python3 -m pip install -e .
   ```

1. Run it!

   ```bash
   python3 -m binderhub -f testing/localonly/binderhub_config.py
   ```

1. You can now access it locally at http://localhost:8585

Note that building and launching will not work, but the
`testing/localonly/binderhub_config.py` setup a fake building process which
allows you to work on the UI experience.


## Bumping the JupyterHub Helm Chart version

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


## Releasing

Checklist for creating BinderHub releases. For PyPI packaging read https://packaging.python.org/guides/distributing-packages-using-setuptools/#uploading-your-project-to-pypi

* remove the `dev` suffix in `binderhub/_version.py`
* update/close the `CHANGES.rst` for this release
* add a new section at the top of the change log for future releases
* `pip install twine`
* `python setup.py sdist`
* `python setup.py bdist_wheel`
* `twine check dist/*` to check the README parses on PyPI
* edit `$HOME/.pypirc` to use the binder team account
* `twine upload dist/*`
* create a new release on https://github.com/jupyterhub/binderhub/releases
* bump the version in `_version.py` from `0.n.y` to `0.(n+1).0dev`
