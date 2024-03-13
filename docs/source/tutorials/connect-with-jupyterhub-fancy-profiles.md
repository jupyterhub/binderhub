# Connect with jupyterhub-fancy-profiles

The [jupyterhub-fancy-profiles](https://github.com/yuvipanda/jupyterhub-fancy-profiles)
project provides a user facing frontend for connecting the JupyterHub to BinderHub,
allowing users to build their own images the same way they would on `mybinder.org`!

The following steps describe how to connect your `binderhub-service` [](installation) to `jupyterhub-fancy-profiles`

1. First, we need to install the `jupyterhub-fancy-profiles` package in the container
   that is running the JupyterHub process itself (not the user containers). The
   easiest way to do this is to use one of the pre-built images provided by
   the `jupyterhub-fancy-profiles` project. In the [list of tags](https://quay.io/repository/yuvipanda/z2jh-hub-with-fancy-profiles?tab=tags),
   select the latest tag that also includes the version of the z2jh chart you are
   using (the `version` specified in step 4 of the previous step). This is _most likely_
   the tag on the top of the page, and looks something like `z2jh-v{{ z2jh version }}-fancy-profiles-sha-{{ some string}}`.

   Once you find the tag, _modify_ the `z2jh-config.yaml` file to enable `jupyterhub-fancy-profiles`.
   While it is hidden here for clarity, make sure to preserve the `hub.services` section that
   you added in step 3 of the previous section while editing this file.

   ```yaml
   hub:
     services: ...
     image:
       # from https://quay.io/repository/yuvipanda/z2jh-hub-with-fancy-profiles?tab=tags
       name: quay.io/yuvipanda/z2jh-hub-with-fancy-profiles
       tag: "<tag>" # example: "z2jh-v3.2.1-fancy-profiles-sha-5874628"

     extraConfig:
       enable-fancy-profiles: |
         from jupyterhub_fancy_profiles import setup_ui
         setup_ui(c)
   ```

2. Since `jupyterhub-fancy-profiles` adds on to the [profileList](https://z2jh.jupyter.org/en/stable/jupyterhub/customizing/user-environment.html#using-multiple-profiles-to-let-users-select-their-environment)
   feature of KubeSpawner, we need to configure a profile list here as well.
   Add this to the `z2jh-config.yaml` file:

   ```yaml
   singleuser:
     profileList:
       - display_name: "Only Profile Available, this info is not shown in the UI"
         slug: only-choice
         profile_options:
           image:
             display_name: Image
             unlisted_choice:
               enabled: True
               display_name: "Custom image"
               validation_regex: "^.+:.+$"
               validation_message: "Must be a publicly available docker image, of form <image-name>:<tag>"
               display_name_in_choices: "Specify an existing docker image"
               description_in_choices: "Use a pre-existing docker image from a public docker registry (dockerhub, quay, etc)"
               kubespawner_override:
                 image: "{value}"
             choices:
               pangeo:
                 display_name: Pangeo Notebook Image
                 description: "Python image with scientific, dask and geospatial tools"
                 kubespawner_override:
                   image: pangeo/pangeo-notebook:2023.09.11
               scipy:
                 display_name: Jupyter SciPy Notebook
                 slug: scipy
                 kubespawner_override:
                   image: jupyter/scipy-notebook:2023-06-26
   ```

3. Deploy, using the command from step 5 of the section above.

4. Access the JupyterHub itself, using the external IP you got from step 5 of the section
   above (not `{{ hub IP }}/services/binder/`). Once you log in (you can use _any_ username
   and password), you should see a UI that allows you to choose two pre-existing
   images (pangeo and scipy), specify your own image, or 'build' your own image.
   The last option lets you access the binder functionality! Test it out :)

From now on, you can customize this JupyterHub as you would any other JupyterHub set up
using z2jh. The [customization guide](https://z2jh.jupyter.org/en/stable/jupyterhub/customization.html)
contains many helpful examples of how you can customize your hub. In particular,
you probably want to set up more restrictive
[authentication](https://z2jh.jupyter.org/en/stable/administrator/authentication.html)
so not everyone can log in to your hub!
