# Contributing

Welcome! As a [Jupyter](https://jupyter.org) project, we follow the [Jupyter contributor guide](https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html).

To develop binderhub, you can use a local installation of JupyterHub on minikube,
and run binderhub on the host system.  Note that you will quickly hit your API limit
on GitHub if you don't have a token.

## Installation

1. [Install Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/) and start it: `minikube start`.

   For MacOS, you may find installing from https://github.com/kubernetes/minikube/releases may be
   more stable than using Homebrew.

2. Install helm

   ```bash
   curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
   ```

   [Alternative methods](https://docs.helm.sh/using_helm/#installing-the-helm-client) for helm installation
   exist if you prefer installing without using the script.

3. Initialize helm in minikube

   ```bash
   helm init
   ```
4. Add the JupyterHub helm charts repo:

   ```bash
   helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
   helm repo update
   ```

5. Install JupyterHub in minikube with helm

        ./testing/minikube/install-hub

6. Install binderhub and its development requirements:

        python3 -m pip install -e . -r dev-requirements.txt

7. Before starting the local dev/test deployment run:

        eval $(minikube docker-env)

7. Start binderhub with the testing config file:

        python3 -m binderhub -f testing/minikube/binderhub_config.py

8. Visit [http://localhost:8585](http://localhost:8585)

All features should work, including building and launching.

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

2. Run it!

   ```bash
   python3 -m binderhub -f testing/localonly/binderhub_config.py
   ```

3. You can now access it locally at http://localhost:8585

Note that building and launching will not work, but the
`testing/localonly/binderhub_config.py` setup a fake building process which
allows you to work on the UI experience.
