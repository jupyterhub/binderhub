---
title: 'BinderHub: shareable, interactive computing environments with Kubernetes'
tags:
  - jupyter
  - jupyterhub
  - interactive computing
  - cloud computing
  - binder
  - kubernetes
  - helm

authors:
 - name: Project Jupyter
   orcid:
   affiliation:
 - name: Tim Head
   orcid: XXXX
   affiliation: Wild Tree Tech
 - name: Jessica Forde
   orcid: XXXX
   affiliation: Project Jupyter
 - name: Brian Granger
   orcid: 0000-0002-5223-6168
   affiliation: Cal Poly
 - name: Chris Holdgraf
   orcid: 0000-0002-2391-0678
   affiliation: University of California, Berkeley
 - name: M Pacer
   orcid: XXX
   affiliation: University of California, Berkeley
 - name: Yuvi Panda
   orcid: XXXX
   affiliation: University of California, Berkeley
 - name: Fernando Perez
   orcid: XXXX
   affiliation: University of California, Berkeley
 - name: Min Ragan-Kelley
   orcid:  0000-0002-1023-7082
   affiliation: Simula Research Laboratory
 - name: Carol Willing
   orcid: 0000-0002-9817-8485
   affiliation: Cal Poly
date: YYYY-MM-DD
bibliography: paper.bib
---

# Summary

BinderHub enables authors to create sharable, interactive
computational environments by specifying their environment in an online
git repository.

BinderHub runs a service that lets users put their code in a repository online, use
the BinderHub service to build a Docker image using configuration files in that
repository, then serve that Docker image to users via a public link. BinderHub
will flexibly create cloud resources as users request to interact with a
particular repository's link, and will automatically destroy these resources
after periods of inactivity. A public deployment of BinderHub exists at
`mybinder.org`, though BinderHub is designed to be deployed by anyone. It is
cloud-agnostic and can support many different workflows.

BinderHub interfaces closely with the [JupyterHub Helm Chart](https://github.com/jupyterhub/zero-to-jupyterhub-k8s),
which runs a JupyterHub service on Kubernetes. It includes a Python module
that interfaces with other open-source tools (e.g., [repo2docker](https://github.com/jupyter/repo2docker)) to run the service
described above. It also includes a Helm
chart template that allows others to deploy their own Binder service using
Kubernetes.

For more information, see the [BinderHub documentation](https://binderhub.readthedocs.io)
as well as the [Binder user documentation](https://docs.mybinder.org).

_Note: Author ordering is in alphabetical order._

# References
