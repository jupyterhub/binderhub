(installation)=

# Installation

The following steps describe how to install the `binderhub-service` helm chart.

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

4. Create a docker repository for binderhub to push built images to. In this tutorial, we will be using Google Artifact Registry, but [binderhub supports using other registries](https://binderhub.readthedocs.io/en/latest/zero-to-binderhub/setup-registry.html#set-up-the-container-registry).

   Create a new Artifact Registry ([via this URL](https://console.cloud.google.com/artifacts/create-repo). Make sure you're in the correct project (look at the drop
   down in the top bar). If this is the first time you are using Artifact Registry, it may ask you to enable the service.

   In the repository creation page, give it a name (ideally same name you are using for
   dedicated to the chart installation), select 'Docker' as the format, 'Standard' as the mode, 'Region'
   as the location type and select the same region your kubernetes cluster is in. The
   settings about encryption and other options can be left in their default. Click "Create".

5. Find the full path of the repository you just created, by opening it in the list
   and looking for the small 'copy' icon next to the name of the repository. If you
   click it, it should copy something like `<region>-docker.pkg.dev/<project-name>/<repository-name>`.
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
