# binderhub-service

[![Documentation Status](https://img.shields.io/readthedocs/binderhub-service?logo=read-the-docs)](https://binderhub-service.readthedocs.io/en/latest/)
[![Latest chart development release](https://img.shields.io/badge/Helm_releases-https://2i2c.org/binderhub-service/blue?link=https://2i2c.org/binderhub-service&color=blue)](https://2i2c.org/binderhub-service/)

The binderhub-service is a Helm chart and guide to run BinderHub (the Python
software), as a standalone service to build and push images with repo2docker,
possibly configured for use with a JupyterHub chart installation.

## History

The BinderHub project provides two major pieces of functionality:

1. Building (and pushing) images via an API using content from various
   providers.
2. Launch interactive sessions using the built images (via a JupyterHub).

The current upstream [binderhub helm chart](https://github.com/jupyterhub/binderhub/tree/main/helm-chart)
is a very opinionated distribution, focusing purely on public instances of BinderHub
(such as [mybinder.org](https://mybinder.org)). It has strong opinions on how
the JupyterHub should be configured, and how it should be connected to the BinderHub.
While historically this allowed for faster iteration on mybinder.org itself,
it has major limitations when used elsewhere.

1. It places restrictions on how the JupyterHub used to launch the interactive sessions
   can be installed and configured. It required workarounds for several types
   of configuration, particularly around persistence (see [persistent binderhub](https://github.com/gesiscss/persistent_binderhub)
   for example).
2. It can not be deployed without the attached, opinionated JupyterHub it comes with.
   This makes deployment for use with alternate frontends (such as
   [jupyterhub-fancy-profiles](https://github.com/yuvipanda/jupyterhub-fancy-profiles)
   difficult)

This project is designed to provide a standalone helm chart that does not have these
restrictions.

## Restrictions

To prevent a recurrance of the issues with the existing binderhub chart, the following
restrictions are in place for any work on this chart:

> There will not be a _direct_ dependency on a JupyterHub. We can provide documentation on
> how to set this chart up next to a JupyterHub, but we will not provide a JupyterHub
> directly (via a [helm dependency](https://helm.sh/docs/chart_best_practices/dependencies/))
> or otherwise.

## Scope

The documentation should help configure the BinderHub service to:

- run behind JupyterHub authentication and authorization
- in one or more ways be able to launch built images
- in one or more ways handle the issue repo2docker building an image with data
  put where JupyterHub user home folders typically is mounted

## Installation

Checkout this project's documentation for installation guide https://binderhub-service.readthedocs.io/en/latest.

## Funding

Funded in part by [GESIS](http://notebooks.gesis.org) in cooperation with
NFDI4DS [460234259](https://gepris.dfg.de/gepris/projekt/460234259?context=projekt&task=showDetail&id=460234259&)
and [CESSDA](https://www.cessda.eu).
