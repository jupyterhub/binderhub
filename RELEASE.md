# How to make a release

`binderhub-service` is a Helm chart available in the Helm chart repository
`https://2i2c.org/binderhub-service`.

## Pre-requisites

- Push rights to [2i2c-org/binderhub-service]

## Steps to make a release

1. Create a PR updating `docs/source/changelog.md` with [github-activity] and
   continue only when its merged.

   ```shell
   pip install github-activity

   github-activity --heading-level=3 2i2c-org/binderhub-service
   ```

1. Checkout main and make sure it is up to date.

   ```shell
   git checkout main
   git fetch origin main
   git reset --hard origin/main
   ```

1. Update the version, make commits, and push a git tag with `tbump`.

   ```shell
   pip install tbump
   tbump --dry-run ${VERSION}

   tbump ${VERSION}
   ```

   Following this, the [CI system] will build and publish a release.

1. Reset the version back to dev, e.g. `1.1.0-0.dev` after releasing `1.0.0`

   ```shell
   tbump --no-tag ${NEXT_VERSION}-0.dev
   ```

[2i2c-org/binderhub-service]: https://github.com/2i2c-org/binderhub-service
[github-activity]: https://github.com/executablebooks/github-activity
[ci system]: https://github.com/2i2c-org/binderhub-service/actions/workflows/release.yaml
