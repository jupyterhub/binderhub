# [JupyterHub Helm Chart](https://github.com/jupyterhub/helm-chart)


A [helm][] [chart][] for deploying [JupyterHub] instances on [Kubernetes].

**[Zero to JupyterHub with Kubernetes]** provides detailed instructions for using this project within a JupyerHub deployment.

## Overview of [Kubernetes] terminology

### What is [helm]?

[helm] is the Kubernetes package manager. [Helm] streamlines  installing and managing Kubernetes applications. *Reference: [helm repo]*

### What is a [chart]?

Charts are Helm packages that contain at least two things:

- A description of the package (`Chart.yaml`)
- One or more **templates**, which contain Kubernetes manifest files

*Reference: [Kubernetes Introduction to charts]*

## Contents of this repository

### `jupyterhub` folder

Fundamental elements of a chart including:

- `templates` folder
- `Chart.yaml.template`
- `values.yaml`

### `images` folder

Docker images for applications including:

- `builder`
- `hub`
- `proxy`
- `singleuser-sample`

### `Makefile`

Useful for compiling custom charts.

## Usage

To build and push Docker images in the `images` directory:

    make images

To create chart metadata and package chart for use:

    make chart


[JupyterHub]: https://jupyterhub.readthedocs.io/en/latest/
[Kubernetes]: https://kubernetes.io
[helm]: https://helm.sh/
[helm repo]: https://github.com/kubernetes/helm
[chart]: https://github.com/kubernetes/helm/blob/master/docs/charts.md
[Kubernetes Introduction to charts]: https://github.com/kubernetes/helm/blob/master/docs/charts.md
[Zero to JupyterHub with Kubernetes]: https://zero-to-jupyterhub.readthedocs.io/en/latest/
