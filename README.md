[builderhub][]
==============

*This project is under active development and subject to change.*

Collections of Jupyter notebooks are becoming more common in scientific research
and data science. The ability to serve these collections on demand enhances the
usefulness of these notebooks.

Similar in spirit to the existing Binder service, [builderhub][] ties together:

- [JupyterHub](https://github.com/jupyterhub/jupyterhub) to provides
  a scalable system for authenticating users and spawning single users
  notebook servers, and

- Red Hat's [source-to-image project from OpenShift](https://github.com/openshift/source-to-image)
  build the actual image for a notebook collection

Builderhub is created using Python, kubernetes, tornado, and traitlets. As such,
it should be a familiar technical foundation for Jupyter developers.

Installation
------------

**builderhub** is based on Python 3, and it can be installed using pip:

    pip install builderhub

License
-------

See `LICENSE` file in this repository.


[builderhub]: https://github.com/yuvipanda/builderhub
