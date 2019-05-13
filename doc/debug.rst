Debugging BinderHub
===================

If BinderHub isn't behaving as you'd expect, you'll need to debug your
kubernetes deployment of the JupyterHub and BinderHub services. For a
guide on how to debug in Kubernetes, see the `Zero to JupyterHub debugging
guide <https://zero-to-jupyterhub.readthedocs.io/en/latest/debug.html>`_.

Indentation in Config Files
---------------------------

Probably the most common cause of unexplained behaviour from a BinderHub is an incorrectly indented key in one of the configuration files.
Indentation levels can change depending on how the BinderHub was deployed.
Or in other words, the structure of the values is dictated by the chart being configured.

If you deployed BinderHub by following `Zero to BinderHub <https://binderhub.readthedocs.io/en/latest/index.html#zero-to-binderhub>`_, then you probably have ``secret.yaml`` and ``config.yaml`` files.
This is the case where one chart includes another.
Here, the BinderHub chart includes the JupyterHub chart.
The included chart values are loaded from a key with the chart's name, within the parent ``config.yaml`` file.::

  # BinderHub chart config is top-level
  registry:
    username: "a-username"
    password: "xxxx"

  # JupyterHub chart config is now under "jupyterhub" key
  # This key is dictated by the name of the included chart
  jupyterhub:
    hub:
      resources:
        memory:
          limit: '1G'

If you were deploying only a JupyterHub, it only has one chart and so many of the Hub-related keys become top-level, such as "hub", "singleuser", "auth" and so on.::

  auth:
    type: "github"

  hub:
    resources:
      memory:
        limit: "1G"

If you are using the `JupyterHub for Kubernetes Customization Guide <https://zero-to-jupyterhub.readthedocs.io/en/latest/#customization-guide>`_, then this is an important difference to note.
Any keys you add **to the BinderHub** from this guide, should go under the ``jupyterhub`` key in ``config.yaml`` file as they are specific to the JupyterHub chart included within BinderHub.

For completeness, another case is how `mybinder.org <https://github.com/jupyterhub/mybinder.org-deploy>`_ itself is deployed.
The BinderHub serving mybinder.org is deployed as a dependency of a local chart and so ``binderhub`` `becomes the top-level key <https://github.com/jupyterhub/mybinder.org-deploy/blob/b34c7980caddb4e422136bf3e1d95c25cabcc078/mybinder/values.yaml#L24>`_ with ``jupyterhub`` nested below.::

  binderhub:
    registry:
      ...

    jupyterhub:
      hub:
        ...

Such kinds of "nested" chart dependencies are managed by a special file called ``requirements.yaml``.
More info on using such a file can be found in the `related Helm docs <https://helm.sh/docs/developing_charts/#managing-dependencies-with-requirements-yaml>`_.

Ok so now that we've ascertained that indentation errors are the most likely cause of undesirable behaviour, how can we prevent them?

One tool that can be used to combat this is `helm diff <https://github.com/databus23/helm-diff>`_ which shows what would change in the chart between upgrades, releases, etc.
If you think something should change but the diff is empty, that's probably a good clue something is misplaced!

An automated script to check linting may also be of appeal.
The Jupyter Team have a `lint script <https://github.com/jupyterhub/zero-to-jupyterhub-k8s/blob/eaf87a217fca1834e299a0567a1ef87d813369b7/tools/templates/lint-and-validate.py>`_ to check the validity of the JupyterHub chart.
It runs ``yamllint``, ``helm lint`` and ``kubeval``.

For further discussion on this topic or to join the conversation, you can visit `this Discourse thread <https://discourse.jupyter.org/t/nesting-levels-in-config-yml-file/1037>`_ or `this GitHub issue <https://github.com/jupyterhub/binderhub/issues/845>`_.

Changing the helm chart
-----------------------
If you make changes to your Helm Chart (e.g., while debugging), you should
run an upgrade on your Kubernetes deployment like so::

     helm upgrade binder jupyterhub/binderhub --version=<commit-hash> -f secret.yaml -f config.yaml

where ``<commit-hash>`` can be found `here <https://jupyterhub.github.io/helm-chart/#development-releases-binderhub>`_.
