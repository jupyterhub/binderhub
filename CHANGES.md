# Changes in BinderHub

_Note: the [BinderHub repository](https://github.com/jupyterhub/binderhub) does not
follow a traditional "semver" release schedule. Updates to this repository are
deployed to production at mybinder.org quickly after they are merged
(see [this blogpost on the henchbot for more information](https://blog.jupyter.org/automating-mybinder-org-dependency-upgrades-in-10-steps-bb5e38542059)).
As such, this changelog is broken up by dates, not versions, and is just to
make it easier to track what has changed over time_

# 0.2.0...HEAD

([full changelog](https://github.com/jupyterhub/binderhub/compare/0.2.0...HEAD))

## Breaking changes

### `binderhub_config.py` is mounted at runtime

The `binderhub_config.py` file is now mounted at runtime instead of being built into the BinderHub image
[#1165](https://github.com/jupyterhub/binderhub/pull/1165/).
If you have custom configuration you should add it using the `extraConfig` Helm chart property.

### `cors` configuration properties have been moved to `BinderHub` and `BinderSpawner`

`cors` chart parameters have been moved into Traitlets configurable properties
[#1351](https://github.com/jupyterhub/binderhub/pull/1351):

- `cors.allowedOrigin` ➡️ `config.BinderHub.cors_allow_origin`
- `jupyterhub.custom.cors.allowedOrigin` ➡️ `jupyterhub.hub.config.BinderSpawner.cors_allow_origin`

### Kubernetes 1.23+ is required

Older versions of Kubernetes are no longer supported
[#1493](https://github.com/jupyterhub/binderhub/pull/1493)
[#1609](https://github.com/jupyterhub/binderhub/pull/1609)
[#1714](https://github.com/jupyterhub/binderhub/pull/1714).

### `dind.enabled` replaced by `imageBuilderType: dind`

The BinderHub builder has been generalised to support non-docker implementations
[#1531](https://github.com/jupyterhub/binderhub/pull/1531).
If you are using Docker-in-Docker replace:

- `dind.enabled: true` ➡️ `imageBuilderType: dind`

The `component: dind` pod builder label is changed to `component: image-builder`
[#1543](https://github.com/jupyterhub/binderhub/pull/1543)

### `imageCleaner.host.enabled` replaced by`imageCleaner.enabled`

When Docker-in-Docker (dind) is enabled the image cleaner used to be run in Docker-in-Docker and on the host Docker.
This is no longer the case, the image cleaner is only run in one place
[#1588](https://github.com/jupyterhub/binderhub/pull/1588).
If you were previously disabling the image cleaner replace:

- `imageCleaner.host.enabled: false` ➡️ `imageCleaner.enabled: false`

### `binderhub.build.Build` class replaced by `binderhub.build.KubernetesBuildExecutor`

The `binderhub.build.Build` class is replaced by the Traitlets based `binderhub.build.KubernetesBuildExecutor` class
[#1518](https://github.com/jupyterhub/binderhub/pull/1518),
[#1521](https://github.com/jupyterhub/binderhub/pull/1521).

The following build configuration properties should be set using Traitlets in the BinderHub configuration:

- `c.BinderHub.appendix` ➡️ `c.BuildExecutor.appendix`
- `c.BinderHub.sticky_builds` ➡️ `c.KubernetesBuildExecutor.sticky_builds`
- `c.BinderHub.log_tail_lines` ➡️ `c.KubernetesBuildExecutor.log_tail_lines`
- `c.BinderHub.push_secret` ➡️ `c.BuildExecutor.push_secret`
- `c.BinderHub.build_memory_request` ➡️ `c.KubernetesBuildExecutor.memory_request`
- `c.BinderHub.build_memory_limit` ➡️ `c.BuildExecutor.memory_limit`
- `c.BinderHub.build_docker_host` ➡️ `c.KubernetesBuildExecutor.docker_host`
- `c.BinderHub.build_namespace` ➡️ `c.KubernetesBuildExecutor.namespace`
- `c.BinderHub.build_image` ➡️ `c.KubernetesBuildExecutor.build_image`
- `c.BinderHub.build_node_selector` ➡️ `c.KubernetesBuildExecutor.node_selector`

If you have subclassed `binderhub.build.Build` you must update your subclass (including `__init__()` if defined) to inherit from `binderhub.build.KubernetesBuildExecutor`.
The behaviour of the class is otherwise unchanged.

### Z2JH 3 and JupyterHub 4

The Z2JH dependency has been updated from 1.2.0 to 3.0.0 which includes JupyterHub 4
[#1544](https://github.com/jupyterhub/binderhub/pull/1544) [#1714](https://github.com/jupyterhub/binderhub/pull/1714).

See [Z2JH's upgrade notes](https://z2jh.jupyter.org/en/stable/administrator/upgrading/index.html)
and [changelog](https://z2jh.jupyter.org/en/latest/changelog.html) for breaking
changes in the upgrade from 1.2.0 to 2.0.0, and then from 2.0.0 to 3.0.0.

### Python versions have been increased

The minimum Python version is 3.8, and the Helm Chart BinderHub image has been upgraded to 3.11
[#1610](https://github.com/jupyterhub/binderhub/pull/1610)
[#1611](https://github.com/jupyterhub/binderhub/pull/1611).

### Default image registry changed to Quay.io

We now publish the chart's docker images to both [Quay.io] and [Docker Hub] and
the chart is from now configured to use the images at Quay.io by default.

The change is to ensure that images can be pulled without a [Docker Hub rate
limit] even if the [JupyterHub organization on Docker Hub] wouldn't be sponsored
by Docker Hub in the future, something we need to apply for each year.

[docker hub]: https://hub.docker.com
[docker hub rate limit]: https://docs.docker.com/docker-hub/download-rate-limit/
[jupyterhub organization on docker hub]: https://hub.docker.com/u/jupyterhub
[quay.io]: https://quay.io

# 0.2.0

# master@{2019-07-01}...master@{2019-10-01}

([full changelog](https://github.com/jupyterhub/binderhub/compare/01b1c59b9e7dc81250c1ed579c492ec2fd6baaf6...a168d069772012c52f9ac7056ec22d779927ae69))

## Enhancements made

- added Authorization header if access_token provided [#954](https://github.com/jupyterhub/binderhub/pull/954) ([@kaseyhackspace](https://github.com/kaseyhackspace))
- Add Figshare to UI [#951](https://github.com/jupyterhub/binderhub/pull/951) ([@nuest](https://github.com/nuest))
- add "sticky builds" functionality [#949](https://github.com/jupyterhub/binderhub/pull/949) ([@betatim](https://github.com/betatim))
- A small docs update [#945](https://github.com/jupyterhub/binderhub/pull/945) ([@nuest](https://github.com/nuest))
- Make git_credentials configurable [#940](https://github.com/jupyterhub/binderhub/pull/940) ([@chicocvenancio](https://github.com/chicocvenancio))
- Fix up description of helm chart contents [#935](https://github.com/jupyterhub/binderhub/pull/935) ([@betatim](https://github.com/betatim))
- adding jupyterlab file paths for preview [#925](https://github.com/jupyterhub/binderhub/pull/925) ([@choldgraf](https://github.com/choldgraf))
- Add more loading messages [#924](https://github.com/jupyterhub/binderhub/pull/924) ([@betatim](https://github.com/betatim))
- adding help text loop to loading page [#917](https://github.com/jupyterhub/binderhub/pull/917) ([@choldgraf](https://github.com/choldgraf))
- Add extraArgs to dind [#916](https://github.com/jupyterhub/binderhub/pull/916) ([@enolfc](https://github.com/enolfc))
- Serve pod usage information in `/health` handler [#912](https://github.com/jupyterhub/binderhub/pull/912) ([@betatim](https://github.com/betatim))
- Make docker registry check smarter [#911](https://github.com/jupyterhub/binderhub/pull/911) ([@betatim](https://github.com/betatim))
- disable continuous-image-puller [#909](https://github.com/jupyterhub/binderhub/pull/909) ([@bitnik](https://github.com/bitnik))
- adding social meta tags to binder pages [#906](https://github.com/jupyterhub/binderhub/pull/906) ([@choldgraf](https://github.com/choldgraf))
- update documentation for "GitHub API limit" [#905](https://github.com/jupyterhub/binderhub/pull/905) ([@bitnik](https://github.com/bitnik))
- Add a /health endpoint to BinderHub [#904](https://github.com/jupyterhub/binderhub/pull/904) ([@betatim](https://github.com/betatim))
- Per spec configuration [#888](https://github.com/jupyterhub/binderhub/pull/888) ([@choldgraf](https://github.com/choldgraf))
- adding federation page [#868](https://github.com/jupyterhub/binderhub/pull/868) ([@choldgraf](https://github.com/choldgraf))
- DinD documentation [#838](https://github.com/jupyterhub/binderhub/pull/838) ([@jhamman](https://github.com/jhamman))

## Bugs fixed

- Fix node affinity selector [#963](https://github.com/jupyterhub/binderhub/pull/963) ([@betatim](https://github.com/betatim))
- Fix node affinity label name [#962](https://github.com/jupyterhub/binderhub/pull/962) ([@betatim](https://github.com/betatim))
- Check if nbviewer URL would show an error [#934](https://github.com/jupyterhub/binderhub/pull/934) ([@betatim](https://github.com/betatim))
- Fix docker registry health check [#932](https://github.com/jupyterhub/binderhub/pull/932) ([@betatim](https://github.com/betatim))
- Fixes and tests for git unresolved ref support [#921](https://github.com/jupyterhub/binderhub/pull/921) ([@hugokerstens](https://github.com/hugokerstens))

## Other merged PRs

- Update repo2docker to 0.10.0 [#958](https://github.com/jupyterhub/binderhub/pull/958) ([@enolfc](https://github.com/enolfc))
- GitLab CE repository was moved to GitLab Foss [#956](https://github.com/jupyterhub/binderhub/pull/956) ([@betatim](https://github.com/betatim))
- install jupyterhub 1.0.0 in binderhub image [#944](https://github.com/jupyterhub/binderhub/pull/944) ([@bitnik](https://github.com/bitnik))
- Update Z2JH helm chart [#936](https://github.com/jupyterhub/binderhub/pull/936) ([@betatim](https://github.com/betatim))
- fixing binder social logo design [#931](https://github.com/jupyterhub/binderhub/pull/931) ([@choldgraf](https://github.com/choldgraf))
- Try to resolve an image name to determine registry health [#929](https://github.com/jupyterhub/binderhub/pull/929) ([@betatim](https://github.com/betatim))
- determine chart version with last change in project root [#927](https://github.com/jupyterhub/binderhub/pull/927) ([@bitnik](https://github.com/bitnik))
- Automatically open the log while building a repository [#923](https://github.com/jupyterhub/binderhub/pull/923) ([@betatim](https://github.com/betatim))
- tweaks to social link [#915](https://github.com/jupyterhub/binderhub/pull/915) ([@choldgraf](https://github.com/choldgraf))
- updating social tweaks [#913](https://github.com/jupyterhub/binderhub/pull/913) ([@choldgraf](https://github.com/choldgraf))
- tweaks to social images [#910](https://github.com/jupyterhub/binderhub/pull/910) ([@choldgraf](https://github.com/choldgraf))
- absolute URL for social image [#907](https://github.com/jupyterhub/binderhub/pull/907) ([@choldgraf](https://github.com/choldgraf))
- Bump JupyterHub chart [#901](https://github.com/jupyterhub/binderhub/pull/901) ([@chicocvenancio](https://github.com/chicocvenancio))
- Use git ls-remote to resolve refs for git provider [#895](https://github.com/jupyterhub/binderhub/pull/895) ([@hugokerstens](https://github.com/hugokerstens))

## Contributors for this release (commentors + issue/PR authors)

([GitHub contributors page for this release](https://github.com/jupyterhub/binderhub/graphs/contributors?from=2019-07-01&to=2019-10-01&type=c))

[@akhmerov](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aakhmerov+updated%3A2019-07-01..2019-10-01&type=Issues) | [@bdrian](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abdrian+updated%3A2019-07-01..2019-10-01&type=Issues) | [@betatim](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abetatim+updated%3A2019-07-01..2019-10-01&type=Issues) | [@bitnik](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abitnik+updated%3A2019-07-01..2019-10-01&type=Issues) | [@chicocvenancio](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Achicocvenancio+updated%3A2019-07-01..2019-10-01&type=Issues) | [@choldgraf](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Acholdgraf+updated%3A2019-07-01..2019-10-01&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3AconsideRatio+updated%3A2019-07-01..2019-10-01&type=Issues) | [@enolfc](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aenolfc+updated%3A2019-07-01..2019-10-01&type=Issues) | [@fm75](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Afm75+updated%3A2019-07-01..2019-10-01&type=Issues) | [@hugokerstens](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ahugokerstens+updated%3A2019-07-01..2019-10-01&type=Issues) | [@ingodahn](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aingodahn+updated%3A2019-07-01..2019-10-01&type=Issues) | [@jhamman](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ajhamman+updated%3A2019-07-01..2019-10-01&type=Issues) | [@jpivarski](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ajpivarski+updated%3A2019-07-01..2019-10-01&type=Issues) | [@kaseyhackspace](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Akaseyhackspace+updated%3A2019-07-01..2019-10-01&type=Issues) | [@koldLight](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3AkoldLight+updated%3A2019-07-01..2019-10-01&type=Issues) | [@lesteve](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Alesteve+updated%3A2019-07-01..2019-10-01&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Amanics+updated%3A2019-07-01..2019-10-01&type=Issues) | [@meeseeksmachine](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ameeseeksmachine+updated%3A2019-07-01..2019-10-01&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aminrk+updated%3A2019-07-01..2019-10-01&type=Issues) | [@nuest](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Anuest+updated%3A2019-07-01..2019-10-01&type=Issues) | [@pdurbin](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Apdurbin+updated%3A2019-07-01..2019-10-01&type=Issues) | [@sgibson91](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Asgibson91+updated%3A2019-07-01..2019-10-01&type=Issues) | [@stklik](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Astklik+updated%3A2019-07-01..2019-10-01&type=Issues) | [@Xarthisius](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3AXarthisius+updated%3A2019-07-01..2019-10-01&type=Issues) | [@zchef2k](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Azchef2k+updated%3A2019-07-01..2019-10-01&type=Issues)

# master@{2019-04-01}...master@{2019-07-01}

([full changelog](https://github.com/jupyterhub/binderhub/compare/1835d07222388da2a23765899cd006e6f6462827...472890149128ad350c2cf7bd934de1075fe3e3a8))

## Enhancements made

- adding whitelisted specs [#883](https://github.com/jupyterhub/binderhub/pull/883) ([@choldgraf](https://github.com/choldgraf))
- Add basic news header to the HTML templates [#881](https://github.com/jupyterhub/binderhub/pull/881) ([@betatim](https://github.com/betatim))
- Manually list BinderHub dependencies in docs requirements [#879](https://github.com/jupyterhub/binderhub/pull/879) ([@betatim](https://github.com/betatim))
- Add instructions for setting up an Azure Container Registry [#878](https://github.com/jupyterhub/binderhub/pull/878) ([@sgibson91](https://github.com/sgibson91))
- document launch schema version 3 [#876](https://github.com/jupyterhub/binderhub/pull/876) ([@bitnik](https://github.com/bitnik))
- Add Zenodo provider [#870](https://github.com/jupyterhub/binderhub/pull/870) ([@betatim](https://github.com/betatim))
- Add extraEnv to the BinderHub deployment [#867](https://github.com/jupyterhub/binderhub/pull/867) ([@betatim](https://github.com/betatim))
- Make base badge URL available in the loading screen as well [#865](https://github.com/jupyterhub/binderhub/pull/865) ([@betatim](https://github.com/betatim))
- rename variable and restructure API docs [#860](https://github.com/jupyterhub/binderhub/pull/860) ([@nuest](https://github.com/nuest))
- Make the URL used to generate launch badges configurable [#859](https://github.com/jupyterhub/binderhub/pull/859) ([@betatim](https://github.com/betatim))
- Discuss indentation of configuration files in debugging docs [#847](https://github.com/jupyterhub/binderhub/pull/847) ([@sgibson91](https://github.com/sgibson91))
- Update to Docs: Clarify where in secret.yaml GitHub Personal Access Token should be added [#835](https://github.com/jupyterhub/binderhub/pull/835) ([@sgibson91](https://github.com/sgibson91))
- Write an estimate how long it takes to load [#830](https://github.com/jupyterhub/binderhub/pull/830) ([@certik](https://github.com/certik))
- Update the contributer guide [#824](https://github.com/jupyterhub/binderhub/pull/824) ([@betatim](https://github.com/betatim))
- Allow git_credentials to be configurable [#823](https://github.com/jupyterhub/binderhub/pull/823) ([@katylava](https://github.com/katylava))
- Add a handler to expose what versions this hub uses [#821](https://github.com/jupyterhub/binderhub/pull/821) ([@betatim](https://github.com/betatim))
- Support basic (htpasswd) authentication for registry [#818](https://github.com/jupyterhub/binderhub/pull/818) ([@dylex](https://github.com/dylex))

## Bugs fixed

- Revert "Update to Docs: Clarify where in secret.yaml GitHub Personal Access Token should be added" [#841](https://github.com/jupyterhub/binderhub/pull/841) ([@sgibson91](https://github.com/sgibson91))
- removing extra docs buttons [#829](https://github.com/jupyterhub/binderhub/pull/829) ([@choldgraf](https://github.com/choldgraf))

## Other merged PRs

- Fix typo in OVH link [#873](https://github.com/jupyterhub/binderhub/pull/873) ([@betatim](https://github.com/betatim))
- Add 'origin' field to launch events [#872](https://github.com/jupyterhub/binderhub/pull/872) ([@yuvipanda](https://github.com/yuvipanda))
- Add OVH BinderHub to list of known deployments [#866](https://github.com/jupyterhub/binderhub/pull/866) ([@betatim](https://github.com/betatim))
- Tweak loading messages [#858](https://github.com/jupyterhub/binderhub/pull/858) ([@betatim](https://github.com/betatim))
- fix tolerations in dind daemonset and add tolerations to image-cleaner [#857](https://github.com/jupyterhub/binderhub/pull/857) ([@jhamman](https://github.com/jhamman))
- add user tolerations to dind daemonset [#856](https://github.com/jupyterhub/binderhub/pull/856) ([@jhamman](https://github.com/jhamman))
- add default toleration to build pods [#853](https://github.com/jupyterhub/binderhub/pull/853) ([@jhamman](https://github.com/jhamman))
- Removing note about breaking changes [#837](https://github.com/jupyterhub/binderhub/pull/837) ([@choldgraf](https://github.com/choldgraf))
- Add pod anti-affinity rule to build pods [#834](https://github.com/jupyterhub/binderhub/pull/834) ([@betatim](https://github.com/betatim))
- Stop always pulling the repo2docker image [#828](https://github.com/jupyterhub/binderhub/pull/828) ([@betatim](https://github.com/betatim))
- No more beta for BinderHub [#826](https://github.com/jupyterhub/binderhub/pull/826) ([@betatim](https://github.com/betatim))
- bump jupyterhub chart c83896f...03215dd [#822](https://github.com/jupyterhub/binderhub/pull/822) ([@minrk](https://github.com/minrk))
- Generate coverage while running tests [#820](https://github.com/jupyterhub/binderhub/pull/820) ([@betatim](https://github.com/betatim))
- use chartpress 0.3 [#784](https://github.com/jupyterhub/binderhub/pull/784) ([@minrk](https://github.com/minrk))

## Contributors for this release (commentors + issue/PR authors)

([GitHub contributors page for this release](https://github.com/jupyterhub/binderhub/graphs/contributors?from=2019-04-01&to=2019-07-01&type=c))

[@ageorgou](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aageorgou+updated%3A2019-04-01..2019-07-01&type=Issues) | [@alexmorley](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aalexmorley+updated%3A2019-04-01..2019-07-01&type=Issues) | [@arnim](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aarnim+updated%3A2019-04-01..2019-07-01&type=Issues) | [@banesullivan](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abanesullivan+updated%3A2019-04-01..2019-07-01&type=Issues) | [@betatim](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abetatim+updated%3A2019-04-01..2019-07-01&type=Issues) | [@bitnik](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abitnik+updated%3A2019-04-01..2019-07-01&type=Issues) | [@certik](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Acertik+updated%3A2019-04-01..2019-07-01&type=Issues) | [@choldgraf](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Acholdgraf+updated%3A2019-04-01..2019-07-01&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3AconsideRatio+updated%3A2019-04-01..2019-07-01&type=Issues) | [@dylex](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Adylex+updated%3A2019-04-01..2019-07-01&type=Issues) | [@jhamman](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ajhamman+updated%3A2019-04-01..2019-07-01&type=Issues) | [@katylava](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Akatylava+updated%3A2019-04-01..2019-07-01&type=Issues) | [@kteich-oreilly](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Akteich-oreilly+updated%3A2019-04-01..2019-07-01&type=Issues) | [@lukasheinrich](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Alukasheinrich+updated%3A2019-04-01..2019-07-01&type=Issues) | [@meeseeksmachine](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ameeseeksmachine+updated%3A2019-04-01..2019-07-01&type=Issues) | [@memeplex](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Amemeplex+updated%3A2019-04-01..2019-07-01&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aminrk+updated%3A2019-04-01..2019-07-01&type=Issues) | [@nuest](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Anuest+updated%3A2019-04-01..2019-07-01&type=Issues) | [@sg-s](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Asg-s+updated%3A2019-04-01..2019-07-01&type=Issues) | [@sgibson91](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Asgibson91+updated%3A2019-04-01..2019-07-01&type=Issues) | [@shibbas](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ashibbas+updated%3A2019-04-01..2019-07-01&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ayuvipanda+updated%3A2019-04-01..2019-07-01&type=Issues) | [@zaembraal](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Azaembraal+updated%3A2019-04-01..2019-07-01&type=Issues)

# master@{2019-01-01}...master@{2019-04-01}

([full changelog](https://github.com/jupyterhub/binderhub/compare/7eb80f137e141e3751ffe544f0fbb3589330fb07...6b2908d7aaf4a7ec62beed0019de54db06494214))

## Enhancements made

- Docs Improvement | Setup BinderHub [#804](https://github.com/jupyterhub/binderhub/pull/804) ([@sgibson91](https://github.com/sgibson91))
- updating instructions and adding badges [#791](https://github.com/jupyterhub/binderhub/pull/791) ([@choldgraf](https://github.com/choldgraf))
- docs for private repo access [#783](https://github.com/jupyterhub/binderhub/pull/783) ([@minrk](https://github.com/minrk))
- adding link to gcloud install [#782](https://github.com/jupyterhub/binderhub/pull/782) ([@choldgraf](https://github.com/choldgraf))
- Docs link in building page [#781](https://github.com/jupyterhub/binderhub/pull/781) ([@choldgraf](https://github.com/choldgraf))
- Add liveness probe to binderhub helm chart [#773](https://github.com/jupyterhub/binderhub/pull/773) ([@betatim](https://github.com/betatim))
- document template customization [#767](https://github.com/jupyterhub/binderhub/pull/767) ([@bitnik](https://github.com/bitnik))
- documentation for authentication [#707](https://github.com/jupyterhub/binderhub/pull/707) ([@bitnik](https://github.com/bitnik))

## Bugs fixed

- Docs update: Change | symbol in DockerHub config to 'OR' [#813](https://github.com/jupyterhub/binderhub/pull/813) ([@sgibson91](https://github.com/sgibson91))
- enable registry to use oauth 2.0 as well. [#797](https://github.com/jupyterhub/binderhub/pull/797) ([@shibbas](https://github.com/shibbas))
- badge typo [#792](https://github.com/jupyterhub/binderhub/pull/792) ([@choldgraf](https://github.com/choldgraf))
- Prevent scroll to top on dropdown click [#779](https://github.com/jupyterhub/binderhub/pull/779) ([@captainsafia](https://github.com/captainsafia))
- set HubOAuth.hub_host correctly [#771](https://github.com/jupyterhub/binderhub/pull/771) ([@bitnik](https://github.com/bitnik))
- fix for when extra_static_url_prefix is absolute [#766](https://github.com/jupyterhub/binderhub/pull/766) ([@bitnik](https://github.com/bitnik))
- some fixes in documentation [#765](https://github.com/jupyterhub/binderhub/pull/765) ([@bitnik](https://github.com/bitnik))

## Other merged PRs

- update gist repoprovider [#802](https://github.com/jupyterhub/binderhub/pull/802) ([@bitnik](https://github.com/bitnik))
- Use different command name in Windows setup [#801](https://github.com/jupyterhub/binderhub/pull/801) ([@captainsafia](https://github.com/captainsafia))
- bump default repo2docker to 0.8 [#796](https://github.com/jupyterhub/binderhub/pull/796) ([@minrk](https://github.com/minrk))
- bump dind image to 18.09.2 [#795](https://github.com/jupyterhub/binderhub/pull/795) ([@minrk](https://github.com/minrk))
- relax default liveness probe to 10s [#790](https://github.com/jupyterhub/binderhub/pull/790) ([@minrk](https://github.com/minrk))
- Add badges to README [#780](https://github.com/jupyterhub/binderhub/pull/780) ([@consideRatio](https://github.com/consideRatio))
- Move badge and path functions out of megafile [#778](https://github.com/jupyterhub/binderhub/pull/778) ([@captainsafia](https://github.com/captainsafia))
- Move Image class to separate file [#776](https://github.com/jupyterhub/binderhub/pull/776) ([@captainsafia](https://github.com/captainsafia))
- add base_url into livenessProbe.httpGet.path [#775](https://github.com/jupyterhub/binderhub/pull/775) ([@bitnik](https://github.com/bitnik))
- Update authentication tests [#770](https://github.com/jupyterhub/binderhub/pull/770) ([@bitnik](https://github.com/bitnik))
- upgrade pip, setuptools, requirements on travis; switch to pytest-asyncio [#768](https://github.com/jupyterhub/binderhub/pull/768) ([@minrk](https://github.com/minrk))

## Contributors for this release (commentors + issue/PR authors)

([GitHub contributors page for this release](https://github.com/jupyterhub/binderhub/graphs/contributors?from=2019-01-01&to=2019-04-01&type=c))

[@ageorgou](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aageorgou+updated%3A2019-01-01..2019-04-01&type=Issues) | [@alexmorley](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aalexmorley+updated%3A2019-01-01..2019-04-01&type=Issues) | [@andrewjohnlowe](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aandrewjohnlowe+updated%3A2019-01-01..2019-04-01&type=Issues) | [@banesullivan](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abanesullivan+updated%3A2019-01-01..2019-04-01&type=Issues) | [@betatim](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abetatim+updated%3A2019-01-01..2019-04-01&type=Issues) | [@bitnik](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Abitnik+updated%3A2019-01-01..2019-04-01&type=Issues) | [@captainsafia](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Acaptainsafia+updated%3A2019-01-01..2019-04-01&type=Issues) | [@Carreau](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3ACarreau+updated%3A2019-01-01..2019-04-01&type=Issues) | [@chenyg0911](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Achenyg0911+updated%3A2019-01-01..2019-04-01&type=Issues) | [@choldgraf](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Acholdgraf+updated%3A2019-01-01..2019-04-01&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3AconsideRatio+updated%3A2019-01-01..2019-04-01&type=Issues) | [@drj11](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Adrj11+updated%3A2019-01-01..2019-04-01&type=Issues) | [@fm75](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Afm75+updated%3A2019-01-01..2019-04-01&type=Issues) | [@ggorman](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aggorman+updated%3A2019-01-01..2019-04-01&type=Issues) | [@jhamman](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ajhamman+updated%3A2019-01-01..2019-04-01&type=Issues) | [@jzf2101](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ajzf2101+updated%3A2019-01-01..2019-04-01&type=Issues) | [@lesteve](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Alesteve+updated%3A2019-01-01..2019-04-01&type=Issues) | [@ltetrel](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Altetrel+updated%3A2019-01-01..2019-04-01&type=Issues) | [@meeseeksmachine](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ameeseeksmachine+updated%3A2019-01-01..2019-04-01&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Aminrk+updated%3A2019-01-01..2019-04-01&type=Issues) | [@mrocklin](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Amrocklin+updated%3A2019-01-01..2019-04-01&type=Issues) | [@psychemedia](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Apsychemedia+updated%3A2019-01-01..2019-04-01&type=Issues) | [@rgaiacs](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Argaiacs+updated%3A2019-01-01..2019-04-01&type=Issues) | [@rgbkrk](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Argbkrk+updated%3A2019-01-01..2019-04-01&type=Issues) | [@sgibson91](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Asgibson91+updated%3A2019-01-01..2019-04-01&type=Issues) | [@shibbas](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ashibbas+updated%3A2019-01-01..2019-04-01&type=Issues) | [@stklik](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Astklik+updated%3A2019-01-01..2019-04-01&type=Issues) | [@taylorreiter](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ataylorreiter+updated%3A2019-01-01..2019-04-01&type=Issues) | [@williamfgc](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Awilliamfgc+updated%3A2019-01-01..2019-04-01&type=Issues) | [@willingc](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Awillingc+updated%3A2019-01-01..2019-04-01&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Fbinderhub+involves%3Ayuvipanda+updated%3A2019-01-01..2019-04-01&type=Issues)
