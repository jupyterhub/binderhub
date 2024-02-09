# binderhub-service

The binderhub-service is a Helm chart and guide to run BinderHub (the Python
software), as a standalone service to build and push images with repo2docker,
possibly configured for use with a JupyterHub chart installation.

## Background

The [binderhub chart]'s main use case has been to build images and launch
servers based on them for anonymous users without persistent home folder
storage. The binderhub chart does this by installing the [jupyterhub chart]
opinionatedly configured to not authenticate and provide users with home folder
storage.

There are use cases for putting binderhub behind authentication though, so
support for that [was added]. There are also use cases for providing users with
persistent home folders, and this led to [persistent binderhub chart] being
developed. The persistent binderhub chart, by depending on the binderhub chart,
depending on the jupyterhub chart, is even more complex than the binderhub chart
though. Currently, the project isn't actively maintained.

Could a new chart be developed to deploy binderhub next to an existing
jupyterhub instead, or even entirely on its own without the part where the built
image is launched in a jupyterhub? Could this enable existing jupyterhub chart
installations to add on binderhub like functionality? This is what this project
is exploring!

## Project scope

This project is currently developed to provide a Helm chart and documentation to
deploy and configure BinderHub the Python software for use either by itself, or
next to a JupyterHub Helm chart installation.

The documentation should help configure the BinderHub service to:

- run behind JupyterHub authentication and authorization
- in one or more ways be able to launch built images
- in one or more ways handle the issue repo2docker building an image with data
  put where JupyterHub user home folders typically is mounted

[binderhub chart]: https://github.com/jupyterhub/binderhub
[jupyterhub chart]: https://github.com/jupyterhub/zero-to-jupyterhub-k8s
[persistent binderhub chart]: https://github.com/gesiscss/persistent_binderhub
[was added]: https://github.com/jupyterhub/binderhub/pull/666

## Installation

1. Add the `binderhub-service` chart repository to helm:

   ```bash
   helm repo add binderhub-service https://2i2c.org/binderhub-service
   helm repo update
   ```

   Note this URL will change eventually, as binderhub-service is designed
   to be a generic service, not something for use only by 2i2c.

2. Install the latest development version of `binderhub-service` into a
   namespace.

   ```bash
   helm upgrade \
    --install \
    --create-namespace \
    --devel \
    --wait \
    --namespace <namespace> \
    <name> \
    binderhub-service/binderhub-service
   ```

   This sets up a binderhub service, but not in a publicly visible way.

3. Test that it's running by port-forwarding to the correct pod:

   ```bash
   kubectl -n <namespace> port-forward $(kubectl -n <namespace> get pod -l app.kubernetes.io/component=binderhub -o name) 8585:8585
   ```

   This should forward requests on port 8585 on your localhost, to the binder service running inside the pod. So if you go
   to [localhost:8585](http://localhost:8585), you should see a binder styled page that says 404. If you do, _success!_.

4. Create a docker repository for binderhub to push built images to. In this tutorial, we will be using Google Artifact Registry,
   but binderhub supports using other registries.

   Create a new Artifact Registry ([via this URL](https://console.cloud.google.com/artifacts/create-repo). Make sure you're in the correct project (look at the drop
   down in the top bar). If this is the first time you are using Artifact Registry, it may ask you to enable the service.

   In the repository creation page, give it a name (ideally same name you are using for
   dedicated to the chart installation), select 'Docker' as the format, 'Standard' as the mode, 'Region'
   as the location type and select the same region your kubernetes cluster is in. The
   settings about encryption and other options can be left in their default. Hit "Create".

5. Find the full path of the repository you just created, by opening it in the list
   and looking for the small 'copy' icon next to the name of the repository. If you
   hit it, it should copy something like `<region>-docker.pkg.dev/<project-name>/<repository-name>`.
   Save this.

6. Create a Google Cloud Service Account that has permissions to push to this
   repository ([via this URL]
   (https://console.cloud.google.com/iam-admin/serviceaccounts/create) - make
   sure you are in the correct project again). You may also need appropriate permissions to set this up. Give it a name (same as the name you used
   for the chart installation, but with a '-pusher' suffix) and click 'Create and Continue'.
   In the next step, select 'Artifact Registry Writer' as a role. Click "Continue". In the final step, just click "Done".

7. Now that the service account is created, find it in the list and open it. You will
   find a tab named 'Keys' once the informational display opens - select that. Click
   'Add Key' -> 'Create New Key'. In the dialog box that pops up, select 'JSON' as the
   key type and click 'Create'. This should download a key file. **Keep this file safe**!

8. Now that we have the appropriate permissions, let's set up our configuration! Create a
   new file named `binderhub-service-config.yaml` with the following contents:

   ```yaml
   config:
     BinderHub:
       use_registry: true
       image_prefix: <repository-path>/binder
       # Temporarily enable the binderhub UI so we can test image building and pushing
       enable_api_only_mode: false
   buildPodsRegistryCredentials:
     server: "https://<region>-docker.pkg.dev"
     username: "_json_key"
     password: |
       <json-key-from-service-account>
   ```

   where:

   1. `<repository-path>` is what you copied from step 5.

   2. `<json-key-from-service-account>` is the JSON file you downloaded in step 7.
      This is a multi-line file and will need to be indented correctly. The `|` after
      `password` allows the value to be multi-line, and each line should be indented at least
      2 spaces from `password`.

   3. `<region>` is the region your artifact repository was created in. You can see
      this in the first part of `<repository-path>` as well.

9. Run a `helm upgrade` to use the new configuration you just created:

   ```bash
   helm upgrade \
    --install \
    --create-namespace \
    --devel \
    --wait \
    --namespace <namespace>
    <name> \
    binderhub-service/binderhub-service \
    --values binderhub-service-config.yaml
   ```

   This should set up binderhub with this custom config. If you run a `kubectl -n <namespace> get pod`,
   you will see that the binderhub pod has restarted - this confirms that the config has been set up!

10. Let's verify that _image building and pushing_ works. Access the binderhub pod by following the
    same instructions as step 3. But this time, you should see a binderhub page very similar to that
    on [mybinder.org](https://mybinder.org). You can test build a repository here - I recommend trying
    out `binder-examples/requirements`. It might take a while to build, but you should be able to see
    logs in the UI. It should succeed at _pushing_ the github image, but will fail to launch. The last
    lines in the log in the UI should look like:

    ```
    Successfully pushed europe-west10-docker.pkg.dev/binderhub-service-development/bh-service-test/binderbinder-2dexamples-2drequirements-55ab5c:50533eb470ee6c24e872043d30b2fee463d6943fBuilt image, launching...
    Launching server...
    Launch attempt 1 failed, retrying...
    Launch attempt 2 failed, retrying...
    ```

    You can also go back to the Google Artifact Registry repository you created earlier to verify that the built
    image is indeed there.

11. Now that we have verified this is working, we can disable the binderhub UI as we will not be using it.
    Remove the `config.BinderHub.enable_api_only_mode` configuration from the binderhub config, and redeploy
    using the command from step 9.

## Connect with a JupyterHub installation

Next, let's connect this to a JupyterHub set up via [z2jh](https://z2jh.jupyter.org/). While any JupyterHub
that can run containers will work with this, the _most common_ setup is to use this with z2jh. The first
few steps are lifted directly from the [install JupyterHub](https://z2jh.jupyter.org/en/stable/jupyterhub/installation.html)
section of z2jh.

1. Add the z2jh chart repository to helm:

   ```
   helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
   helm repo update
   ```

2. We want the binderhub to be available under `http://{{hub url}}/services/binder`, because
   that is what `jupyterhub-fancy-profiles` expects. Eventually we would also want authentication
   to work correctly. For that, we must set up binderhub as a [JupyterHub Service](https://jupyterhub.readthedocs.io/en/stable/reference/services.html).
   This provides two things:

   a. Routing from `{{hub url }}/services/{{ service name }}` to the service, allowing us to
      expose the service to the external world using JupyterHub's ingress / loadbalancer, without
      needint a dedicated ingress / loadbalancer for BinderHub.

   b. (Eventually) Appropriate credentials for authenticated network calls between these two services.

   To make this connection, we need to tell JupyterHub where to find BinderHub. Eventually
   this can be automatic (once [this issue](https://github.com/2i2c-org/binderhub-service/issues/57)
   gets resolved). In the meantime, you can get the name of the BinderHub service by executing
   the following command:

   ```bash
   kubectl -n <namespace> get svc -l app.kubernetes.io/name=binderhub-service
   ```

   Make a note of the name under the `NAME` column, we will use it in the next step.

3. Create a config file, `z2jh-config.yaml`, to hold the config values for the JupyterHub.

   ```yaml
   hub:
      services:
         binder:
            # FIXME: ref https://github.com/2i2c-org/binderhub-service/issues/57
            # for something more readable and requiring less copy-pasting
            url: http://{{ service name from step 2}}
   ```

4. Find the latest version of the z2jh helm chart. The easiest way is to run the
   following command:

   ```bash
   helm search repo jupyterhub
   ```

   This should output a few columns. Look for the version under **CHART VERSION** (not *APP VERSION*)
   for `jupyterhub/jupyterhub`. That's the latest z2jh chart version, and that is what
   we will be using.

5. Install the JupyterHub helm chart with the following command:

   ```bash
   helm upgrade --cleanup-on-fail \
      --install <helm-release-name> jupyterhub/jupyterhub \
      --namespace <namespace> \
      --version=<chart-version> \
      --values z2jh-config.yaml \
      --wait
   ```

   where:

   - `<helm-release-name>` is any name you can use to refer to this imag
     (like `jupyterhub`)

   - `<namespace>` is the _same_ namespace used for the BinderHub install

   - `<chart-version>` is the latest stable version of the JupyterHub
     helm chart, determined in the previous step.

6. Find the external IP on which the JupyterHub is accessible:

   ```bash
   kubectl -n <namespace> get svc proxy-public
   ```

7. Access the binder service by going to `http://{{ external ip from step 5}}/services/binder/` (the
   trailing slash is *important*).  You should see an unstyled, somewhat broken
   404 page. This is great and expected. Let's fix that.

8. Change BinderHub config in `binderhub-service-config.yaml`, telling BinderHub it should now
   be available under `/services/binder`.

   ```yaml
   config:
     BinderHub:
       base_url: /services/binder
   ```

   Deploy this using the `helm upgrade` command from step 9 in the previous section.

9. Test by going to `http://{{ external ip from step 5}}/services/binder/` (the trailing slash
   is *important*!) again, and you should see a _styled_ 404 page! Success -
   this means BinderHub is now connected to JupyterHub, even if the end users
   can't see it yet. Let's connect them!

## Connect with `jupyterhub-fancy-profiles`

The [jupyterhub-fancy-profiles](https://github.com/yuvipanda/jupyterhub-fancy-profiles)
project provides a user facing frontend for connecting the JupyterHub to BinderHub,
allowing them to build their own images the same way they would on `mybinder.org`!

1. First, we need to install the `jupyterhub-fancy-profiles` package in the container
   that is running the JupyterHub process itself (not the user containers). The
   easiest way to do this is to use one of the pre-built images provided by
   the `jupyterhub-fancy-profiles` project. In the [list of tags](https://quay.io/repository/yuvipanda/z2jh-hub-with-fancy-profiles?tab=tags),
   select the latest tag that also includes the version of the z2jh chart you are
   using (the `version` specified in step 4 of the previous step). This is *most likely*
   the tag on the top of the page, and looks something like `z2jh-v{{ z2jh version }}-fancy-profiles-sha-{{ some string}}`.

   Once you find the tag, *modify* the `z2jh-config.yaml` file to enable `jupyterhub-fancy-profiles`.
   While it is hidden here for clarity, make sure to preserve the `hub.services` section that
   you added in step 3 of the previous section while editing this file.

   ```yaml
   hub:
     services:
      ...
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
   above (not `{{ hub IP }}/services/binder/`). Once you log in (you can use *any* username
   and password), you should see a UI that allows you to choose two pre-existing
   images (pangeo and scipy), specify your own image, or 'build' your own image.
   The last option lets you access the binder functionality!  Test it out :)

From now on, you can customize this JupyterHub as you would any other JupyterHub set up
using z2jh. The [customization guide](https://z2jh.jupyter.org/en/stable/jupyterhub/customization.html)
contains many helpful. In particular, you probably want to set up more restrictive
[authentication](https://z2jh.jupyter.org/en/stable/administrator/authentication.html) so
not everyone can log in to your hub!

## Funding

Funded in part by [GESIS](http://notebooks.gesis.org) in cooperation with
NFDI4DS [460234259](https://gepris.dfg.de/gepris/projekt/460234259?context=projekt&task=showDetail&id=460234259&)
and [CESSDA](https://www.cessda.eu).
```
