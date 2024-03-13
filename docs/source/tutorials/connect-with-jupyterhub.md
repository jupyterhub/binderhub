# Connect with a JupyterHub installation

The next steps describe how to connect the [`binderhub-service` installation](installation) to a JupyterHub set up via [z2jh](https://z2jh.jupyter.org/). While any JupyterHub that can run containers will work with this, the _most common_ setup is to use this with z2jh.

The first few steps are lifted directly from the [install JupyterHub](https://z2jh.jupyter.org/en/stable/jupyterhub/installation.html) section of z2jh.

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
   needing a dedicated ingress / loadbalancer for BinderHub.

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

   This should output a few columns. Look for the version under **CHART VERSION** (not _APP VERSION_)
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

   - `<helm-release-name>` is any name you can use to refer to this image
     (like `jupyterhub`)

   - `<namespace>` is the _same_ namespace used for the BinderHub install

   - `<chart-version>` is the latest stable version of the JupyterHub
     helm chart, determined in the previous step.

6. Find the external IP on which the JupyterHub is accessible:

   ```bash
   kubectl -n <namespace> get svc proxy-public
   ```

7. Access the binder service by going to `http://{{ external ip from step 5}}/services/binder/` (the
   trailing slash is _important_). You should see an unstyled, somewhat broken
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
   is _important_!) again, and you should see a _styled_ 404 page! Success -
   this means BinderHub is now connected to JupyterHub, even if the end users
   can't see it yet. Let's connect them!
