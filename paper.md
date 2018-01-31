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

BinderHub is a framework for enabling authors to create sharable, interactive
computational environments by specifying their environment in an online
git repository.

BinderHub interfaces closely with the [JupyterHub Helm Chart](https://github.com/jupyterhub/zero-to-jupyterhub-k8s),
which runs a JupyterHub service on Kubernetes. It includes a Python module
with logic for reading Git repositories from various providers (e.g., GitHub),
generating a Docker image for the environment specified in that repository,
and creating a link that users can share with others. It also includes a Helm
chart template that allows others to deploy their own Binder service using
Kubernetes.

_Note: Author ordering is in alphabetical order._

# References
