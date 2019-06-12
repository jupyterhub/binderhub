BinderHub Deployments
=====================

BinderHub is open-source technology that can be deployed anywhere that
Kubernetes is deployed. The Binder community hopes that it will be used
for many applications in research and education. As new organizations adopt
BinderHub, we'll update this page in order to provide inspiration to others
who wish to do so.

If you or your organization has set up a BinderHub that isn't listed here,
please `open an issue <https://github.com/jupyterhub/binderhub/issues>`_ on
our GitHub repository to discuss adding it!

GESIS - Leibniz-Institute for the Social Sciences
-------------------------------------------------

Deployed on bare-metal using ``kubeadm``.

* `Deployment repository <https://github.com/gesiscss/orc>`__
* `BinderHub / JupyterHub links <https://notebooks.gesis.org/>`__

Pangeo - A community platform for big data geoscience
-----------------------------------------------------

Pangeo-Binder allows users to perform computations using distributed
computing resources via the `dask-kubernetes`_ package. Read more about the
`Pangeo project here`_. Pangeo-Binder is deployed on Google Cloud Platform using
Google Kubernetes Engine (GKE).

_`dask-kubernetes`: https://dask-kubernetes.readthedocs.io/en/latest/
_`Pangeo project here`: https://pangeo.io/

* `Deployment repository`__
* `BinderHub / JupyterHub links`__
* `Pangeo-Binder documentation`__

__ https://github.com/pangeo-data/pangeo-binder
__ http://binder.pangeo.io
__ https://pangeo-binder.readthedocs.io/en/latest


OVH - A public BinderHub
------------------------

Deployed on `OVH <https://ovh.com>`_'s Kubernetes platform. This hub was the
first hub to join the Binder Federation, a global network of general purpose,
public BinderHubs.


* `Deployment repository <https://github.com/jupyterhub/mybinder.org-deploy>`__
* `BinderHub link <https://ovh.mybinder.org/>`__
