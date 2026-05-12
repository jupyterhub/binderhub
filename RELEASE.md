\# How to make a release



`binderhub` is a package available on \[PyPI](https://pypi.org/project/binderhub/).



These are the instructions on how to make a release.



\## Pre-requisites



\- Push rights to this GitHub repository



\## Steps to make a release



1\. Create a PR updating `docs/source/changelog.md` with \[github-activity](https://github.com/executablebooks/github-activity) and continue when its merged.

&#x20;  For details about this, see the \[team-compass documentation](https://jupyterhub-team-compass.readthedocs.io/en/latest/practices/releases.html) about it.



2\. Checkout main and make sure it is up to date.



```bash

&#x20;  git checkout main

&#x20;  git fetch origin main

&#x20;  git reset --hard origin/main

```



3\. Tag the release using `versioneer` and push the tag.



```bash

&#x20;  # Example versions to set: 1.0.0, 1.0.0b1

&#x20;  VERSION=

&#x20;  git tag ${VERSION}

&#x20;  git push origin ${VERSION}

```



4\. Following the tag push, the CI system will build and publish the release to PyPI automatically once the release workflow is configured.



5\. Following the release to PyPI, an automated PR should arrive within 24 hours to \[conda-forge/binderhub-feedstock](https://github.com/conda-forge/binderhub-feedstock) with instructions on releasing to conda-forge.

