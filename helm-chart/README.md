# BinderHub Helm Chart

A [helm][] [chart][] for deploying [BinderHub] instances on [Kubernetes].

**[Zero to JupyterHub with Kubernetes]** provides detailed instructions for using this project within a JupyerHub deployment.

## Overview of [Kubernetes] terminology

### What is [helm]?

[helm] is the Kubernetes package manager. [Helm] streamlines installing and managing Kubernetes applications. _Reference: [helm repo]_

### What is a [chart]?

Charts are Helm packages that contain at least two things:

- A description of the package (`Chart.yaml`)
- One or more **templates**, which contain Kubernetes manifest files

_Reference: [Kubernetes Introduction to charts]_

## Contents of this repository

### `binderhub` folder

Fundamental elements of a chart including:

- `templates` folder
- `Chart.yaml.template`
- `values.yaml`

### `images` folder

Docker images for applications including:

- `binderhub`

### `chartpress`

Useful for compiling custom charts.

## Usage

In the helm-chart directory:

    chartpress

to build the docker images and rerender the helm chart.

[binderhub]: https://binderhub.readthedocs.io/en/latest/
[jupyterhub]: https://jupyterhub.readthedocs.io/en/latest/
[kubernetes]: https://kubernetes.io
[helm]: https://helm.sh/
[helm repo]: https://github.com/kubernetes/helm
[chart]: https://helm.sh/docs/topics/charts/
[kubernetes introduction to charts]: https://helm.sh/docs/topics/charts/
[zero to jupyterhub with kubernetes]: https://zero-to-jupyterhub.readthedocs.io/en/latest/
