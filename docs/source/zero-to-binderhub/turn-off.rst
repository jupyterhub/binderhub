Tear down your Binder deployment
================================

Deconstructing a Binder deployment can be a little bit confusing because
users may have caused new cloud containers to be created. It is important
to remember to delete each of these containers or else they will continue
to exist (and cost money!).

Contracting the size of your cluster
------------------------------------

If you would like to shrink the size of your cluster, refer to the
`Expanding and contracting the size of your cluster <https://zero-to-jupyterhub.readthedocs.io/en/latest/user-resources.html#expanding-and-contracting-the-size-of-your-cluster>`_
section of the `Zero to JupyterHub`_ documentation. Resizing the cluster to
zero nodes could be used if you wish to temporarily reduce the cluster (and
save costs) without deleting the cluster.

Deleting the cluster
--------------------

To delete a Binder cluster, follow the instructions in the
`Turning Off JupyterHub and Computational Resources <https://zero-to-jupyterhub.readthedocs.io/en/latest/turn-off.html>`_
section of the `Zero to JupyterHub`_ documentation.

.. important::

    Double check your cloud provider account to make sure all resources have been
    deleted as expected. Double checking is a good practice and will help
    prevent unwanted charges.

.. _Zero to JupyterHub: https://zero-to-jupyterhub.readthedocs.io
