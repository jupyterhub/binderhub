[binderhub][]
=============

*This project is under active development and subject to change.*

Collections of Jupyter notebooks are becoming more common in scientific research
and data science. The ability to serve these collections on demand enhances the
usefulness of these notebooks.

Similar in spirit to the existing Binder service, [binderhub][] ties together:

- [JupyterHub](https://github.com/jupyterhub/jupyterhub) to provides
  a scalable system for authenticating users and spawning single users
  notebook servers, and

- Red Hat's [source-to-image project from OpenShift](https://github.com/openshift/source-to-image)
  build the actual image for a notebook collection

BinderHub is created using Python, kubernetes, tornado, and traitlets. As such,
it should be a familiar technical foundation for Jupyter developers.

Installation
------------

**BinderHub** is based on Python 3, and it can be installed using pip:

    pip install binderhub

License
-------

See `LICENSE` file in this repository.

[binderhub]: https://github.com/jupyterhub/binderhub
