# [BinderHub](https://github.com/jupyterhub/binderhub)

[![Documentation Status](https://img.shields.io/readthedocs/binderhub?logo=read-the-docs)](https://binderhub.readthedocs.io/en/latest/)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/jupyterhub/binderhub/Tests?logo=github&label=tests)](https://github.com/jupyterhub/binderhub/actions)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/jupyterhub/binderhub/CodeQL?logo=github&label=code%20scans)](https://github.com/jupyterhub/binderhub/actions)
[![Latest chart development release](https://img.shields.io/badge/dynamic/json.svg?label=latest&url=https://jupyterhub.github.io/helm-chart/info.json&query=$.binderhub.latest&colorB=orange)](https://jupyterhub.github.io/helm-chart/)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue.svg)](https://github.com/jupyterhub/binderhub/issues)
[![Discourse](https://img.shields.io/badge/help_forum-discourse-blue.svg)](https://discourse.jupyter.org/c/binder/binderhub)
[![Gitter](https://img.shields.io/badge/social_chat-gitter-blue.svg)](https://gitter.im/jupyterhub/binder)
[![Contribute](https://img.shields.io/badge/I_want_to_contribute!-grey?logo=jupyter)](https://github.com/jupyterhub/binderhub/blob/master/CONTRIBUTING.md)

## What is BinderHub?

**BinderHub** allows you to `BUILD` and `REGISTER` a Docker image from a
Git repository, then `CONNECT` with JupyterHub, allowing you to create a
public IP address that allows users to interact with the code and
environment within a live JupyterHub instance. You can select a specific
branch name, commit, or tag to serve.

BinderHub ties together:

- [JupyterHub](https://github.com/jupyterhub/jupyterhub) to provide a scalable
  system for authenticating users and spawning single user Jupyter Notebook
  servers, and
- [Repo2Docker](https://github.com/jupyter/repo2docker) which generates a Docker
  image using a Git repository hosted online.

BinderHub is built with Python, kubernetes, tornado, npm, webpack, and
sphinx.

## Documentation

For more information about the architecture, use, and setup of
BinderHub, see [the BinderHub
documentation](https://binderhub.readthedocs.io).

## Contributing

To contribute to the BinderHub project you can work on:

- [answering questions others have](https://discourse.jupyter.org/),
- writing documentation,
- designing the user interface, or
- writing code.

To see how to build the documentation, edit the user interface or modify
the code see [the contribution
guide](https://github.com/jupyterhub/binderhub/blob/master/CONTRIBUTING.md).

## Installation

**BinderHub** is based on Python 3, it's currently only kept updated on GitHub.
However, it can be installed using `pip`:

    pip install git+https://github.com/jupyterhub/binderhub

See [the BinderHub documentation](https://binderhub.readthedocs.io) for
a detailed guide on setting up your own BinderHub server.

## Why BinderHub?

Collections of Jupyter notebooks are becoming more common in scientific
research and data science. The ability to serve these collections on
demand enhances the usefulness of these notebooks.

## Who is BinderHub for?

- **Users** who want to easily interact with computational environments that
  others have created.
- **Authors** who want to create links that allow users to immediately interact
  with a computational enviroment that you specify.
- **Deployers** who want to create their own BinderHub to run on whatever
  hardware they choose.

## License

See `LICENSE` file in this repository.
