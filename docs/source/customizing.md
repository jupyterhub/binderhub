# Customizing your BinderHub deployment

```{important}
In this section, we assume that you are deploying BinderHub to Kubernetes using Helm as documented in [](#zero-to-binderhub).
```

## Frontend

BinderHub's frontend is built using [React](https://react.dev/).
We prepared the key parts of the BinderHub's frontend as re-usable components available as [`@jupyterhub/binderhub-react-components` on NPM](https://www.npmjs.com/package/@jupyterhub/binderhub-react-components`).
Some customization might require changes in the re-usable components or the way the are connected.

### Banner customization

By default BinderHub shows a banner at the top of all pages. You can define the content of the banner by setting the `banner_message` configuration option to the raw HTML you would like to add.

#### Example

The banner was configured at <https://mybinder.org> using `banner_message`:

```{code-block} yaml
:caption: Snippet from <https://github.com/jupyterhub/mybinder.org-deploy/blob/114ba49335ee3d258654e264b544b67ab270f953/mybinder/values.yaml#L182-L187>

banner_message: |
  <a class="btn" style="width:fit-content;height:fit-content;padding:10px;background-color:#e66581;color:white;font-weight:bold;position:absolute;right:4px;"
    onmouseover="this.style.backgroundColor='#d15b75'" onmouseout="this.style.backgroundColor='#e66581'"
    href="https://jupyter.org/about#donate" target="_blank">
      🤍 Donate to mybinder.org!
  </a>
```

### About page customization

BinderHub's frontend is configured with simple about page at `https://BINDERHOST/about`. By default this shows the version of BinderHub you are running. You can add additional HTML to the page by setting the `about_message` configuration option to the raw HTML you would like to add. You can use this to display contact information or other details about your deployment.

#### Example

The about page was configured at <https://mybinder.org/about> using `about_message`:

```{code-block} yaml
:caption: Snippet from <https://github.com/jupyterhub/mybinder.org-deploy/blob/114ba49335ee3d258654e264b544b67ab270f953/mybinder/values.yaml#L194-L200>

about_message: |
  <p>mybinder.org is public infrastructure operated by the <a href="https://jupyterhub-team-compass.readthedocs.io/en/latest/team.html#binder-team">Binder Project team</a>.<br /><br />
  The Binder Project is a member of <a href="https://jupyter.org">Project Jupyter</a>.
  Donations are managed by <a href="https://lf-charities.org">LF Charities</a>, a US 501c3 non-profit.<br /><br />
  For abuse please email: <a href="mailto:binder-team@googlegroups.com">binder-team@googlegroups.com</a>, to report a
  security vulnerability please see: <a href="https://mybinder.readthedocs.io/en/latest/faq.html#where-can-i-report-a-security-issue">Where can I report a security issue</a><br /><br />
  For more information about the Binder Project, see <a href="https://mybinder.readthedocs.io/en/latest/about.html">the About Binder page</a></p>
```

### `window.pageConfig`

```{warning}
This should be used **only** when providing a BinderHub frontend without the BinderHub backend.
```

Some customization is **exposed** using the `window.pageConfig` JavaScript variable, including

- `aboutMessage`
- `badgeBaseUrl`
- `bannerHtml`
- `baseUrl`
- `logoUrl`
- `logoWidth`
- `repoProviders`

Change the value of the above keys will change how the BinderHub's frontend works.

### Extra JavaScript

BinderHUb tries to be neutral regarding [web analytics](https://en.wikipedia.org/wiki/Web_analytics). You should be able to configure any web analytics tools using `extra_header_html` and `extra_footer_scripts`.

#### Example

[Plausible](https://plausible.io/) was configured at <https://mybinder.org> using `extra_header_html`:

```{code-block} yaml
:caption: Snippet from <https://github.com/jupyterhub/mybinder.org-deploy/blob/114ba49335ee3d258654e264b544b67ab270f953/mybinder/values.yaml#L202-L205>

extra_header_html:
  01-plausible: |
    <script defer data-domain="mybinder.org" src="https://plausible.io/js/script.file-downloads.outbound-links.js"></script>
    <script>window.plausible = window.plausible || function() { (window.plausible.q = window.plausible.q || []).push(arguments) }</script>
```

### Header and Footer customization

BinderHub uses [Jinja](https://jinja.palletsprojects.com/en/stable/) as template engine to process the page template (default is [binderhub/templates/page.html](https://github.com/jupyterhub/binderhub/blob/main/binderhub/templates/page.html)). To add a custom header and footer,

1.  copy `binderhub/templates/page.html` into `files/custom-page.html`

2.  edit `files/custom-page.html` to include the desired header and footer. For example:

    ```html
    <body>
      <header>My Own BinderHub</header>
      <div id="root"></div>
      <footer>Powered by BinderHub</footer>
    </body>
    ```

    It is important to include `<div id="root"></div>` because this is the HTML node that React will use to build the launch form.

3.  copy `files/custom-page.html` into `extraFiles` in the Helm configuration file. For example:

    ```yaml
    extraFiles:
      custom-page:
        mountPath: files/custom-page.html
        stringData: |
          ...
          <body>
          <header>
            My Own BinderHub
          </header>
          <div id="root"></div>
          <footer>
            Powered by BinderHub
          </footer>
          </body>
          ...
    ```

4.  change `template_file` in the Helm configuration file. For example:

    ```yaml
    config:
      BinderHub:
        template_file: files/custom-page.html
    ```

## JupyterHub customization

Because BinderHub uses JupyterHub to manage all user sessions, you can customize many aspects of the resources available to the user. This is primarily done by modifications to your BinderHub\'s Helm chart (`config.yaml`).

To make edits to your JupyterHub deplyoment via `config.yaml`, use the following pattern:

```yaml
binderhub:
  jupyterhub: <JUPYTERHUB-CONFIG-YAML>
```

For example, see [this section of the mybinder.org Helm Chart](https://github.com/jupyterhub/mybinder.org-deploy/blob/a7d83838aea24a4f143a2b8630f4347fa722a6b3/mybinder/values.yaml#L192).

For information on how to configure your JupyterHub deployment, see the [JupyterHub for Kubernetes Customization Guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/#customization-guide).

If you want to customise the spawner you can subclass it in `extraConfig`. For example:

```yaml
binderhub:
  jupyterhub:
    hub:
      extraConfig:
        10-binder-customisations: |
          class MyCustomBinderSpawner(BinderSpawner):
              ...

          c.JupyterHub.spawner_class = MyCustomBinderSpawner
```

BinderHub uses the [jupyterhub.hub.extraConfig setting](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/advanced.html#hub-extraconfig) to customise JupyterHub. For example, `BinderSpawner` is defined under the `00-binder` key. Keys are evaluated in alphanumeric order, so later keys such as `10-binder-customisations` can use objects defined in earlier keys.

(repo-specific-config)=

## Custom configuration for specific repositories

Sometimes you would like to provide a repository-specific configuration. For example, if you\'d like certain repositories to have **higher pod quotas** than others, or if you\'d like to provide certain resources to a subset of repositories.

To override the configuration for a specific repository, you can provide a list of dictionaries that allow you to provide a pattern to match against each repository\'s specification, and override configuration values for any repositories that match this pattern.

```{note}
If you provide **multiple patterns that match a single repository** in your spec-specific configuration, then **later values in the list will override earlier values**.
```

To define this list of patterns and configuration overrides, use the following pattern in your Helm Chart (here we show an example using `GitHubRepoProvider`, but this works for other RepoProviders as well):

```yaml
config:
    GitHubRepoProvider:
      spec_config:
        - pattern: ^ines/spacy-binder.*:
          config:
             key1: value1
        - pattern: pattern2
          config:
             key1: othervalue1
             key2: othervalue2
```

For example, the following specification configuration will assign a pod quota of 999 to the spacy-binder repository, and a pod quota of 1337 to any repository in the JupyterHub organization.

```yaml
config:
    GitHubRepoProvider:
      spec_config:
        - pattern: ^ines/spacy-binder.*:
          config:
             quota: 999
        - pattern: ^jupyterhub.*
          config:
             quota: 1337
```

## Banning specific repositories

You may want to exclude certain repositories from your BinderHub instance. You can do this by providing a list of **banned_spec** patterns. BinderHub will not accept URLs matching any of the banned patterns.

For example, the following configuration will prevent notebooks in the spacy-binder repository and the ml-training repository from launching.

```yaml
config:
  GitHubRepoProvider:
    # Add banned repositories to the list below
    # They should be strings that will match "^<org-name>/<repo-name>.*"
    banned_specs:
      - ^ines/spacy-binder.*
      - ^aschen/ml-training.*
```

You can also use a negative lookahead. For example, the following configuration will prevent all notebooks except those in repositories in the myorg organization from launching.

```yaml
config:
  GitHubRepoProvider:
    banned_specs:
      - ^(?!myorg\/.*).*$
```
