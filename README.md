# binderhub-service

[![Documentation Status](https://img.shields.io/readthedocs/binderhub-service?logo=read-the-docs)](https://binderhub-service.readthedocs.io/en/latest/)
[![Latest chart development release](https://img.shields.io/badge/Helm_releases-https://2i2c.org/binderhub-service/blue?link=https://2i2c.org/binderhub-service/)](https://2i2c.org/binderhub-service/)

The binderhub-service is a Helm chart and guide to run BinderHub (the Python
software), as a standalone service to build and push images with repo2docker,
possibly configured for use with a JupyterHub chart installation.

## Background

The [binderhub chart]'s main use case has been to build images and launch
servers based on them for anonymous users without persistent home folder
storage. The binderhub chart does this by installing the [jupyterhub chart]
opinionatedly configured to not authenticate and provide users with home folder
storage.

There are use cases for putting binderhub behind authentication though, so
support for that [was added]. There are also use cases for providing users with
persistent home folders, and this led to [persistent binderhub chart] being
developed. The persistent binderhub chart, by depending on the binderhub chart,
depending on the jupyterhub chart, is even more complex than the binderhub chart
though. Currently, the project isn't actively maintained.

Could a new chart be developed to deploy binderhub next to an existing
jupyterhub instead, or even entirely on its own without the part where the built
image is launched in a jupyterhub? Could this enable existing jupyterhub chart
installations to add on binderhub like functionality? This is what this project
is exploring!

## Project scope

This project is currently developed to provide a Helm chart and documentation to
deploy and configure BinderHub the Python software for use either by itself, or
next to a JupyterHub Helm chart installation.

The documentation should help configure the BinderHub service to:

- run behind JupyterHub authentication and authorization
- in one or more ways be able to launch built images
- in one or more ways handle the issue repo2docker building an image with data
  put where JupyterHub user home folders typically is mounted

[binderhub chart]: https://github.com/jupyterhub/binderhub
[jupyterhub chart]: https://github.com/jupyterhub/zero-to-jupyterhub-k8s
[persistent binderhub chart]: https://github.com/gesiscss/persistent_binderhub
[was added]: https://github.com/jupyterhub/binderhub/pull/666

## Installation

Checkout this project's documentation for installation guide https://binderhub-service.readthedocs.io/en/latest.

## Funding

Funded in part by [GESIS](http://notebooks.gesis.org) in cooperation with
NFDI4DS [460234259](https://gepris.dfg.de/gepris/projekt/460234259?context=projekt&task=showDetail&id=460234259&)
and [CESSDA](https://www.cessda.eu).
