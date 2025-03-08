# syntax = docker/dockerfile:1.3


# The build stage
# ---------------
# This stage is building Python wheels for use in later stages by using a base
# image that has more pre-requisites to do so, such as a C++ compiler.
#
# NOTE: If the image version is updated, also update it in ci/refreeze!
#
FROM python:3.13-bookworm as build-stage

RUN apt-get update \
 && apt-get install --yes \
        nodejs npm \
 && rm -rf /var/lib/apt/lists/*

# Build wheels
#
# We set pip's cache directory and expose it across build stages via an
# ephemeral docker cache (--mount=type=cache,target=${PIP_CACHE_DIR}). We use
# the same technique for the directory /tmp/wheels.
#
COPY . /src
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    pip wheel \
        --wheel-dir=/tmp/wheels \
        # pycurl wheels for 7.45.3 have problems finding CAs
        # https://github.com/pycurl/pycurl/issues/834
        --no-binary pycurl \
        -r /src/helm-chart/images/binderhub/requirements.txt

# The final stage
# ---------------
# This stage is built and published as quay.io/2i2c/binderhub.
#
FROM python:3.13-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get upgrade --yes \
 && apt-get install --yes \
        git \
              # required by binderhub
        libcurl4 \
              # required by pycurl, an optional binderhub dependency
        tini \
              # tini is used as an entrypoint to not loose track of SIGTERM
              # signals as sent before SIGKILL, for example when "docker stop"
              # or "kubectl delete pod" is run. By doing that the pod can
              # terminate very quickly.
 && rm -rf /var/lib/apt/lists/*

COPY helm-chart/images/binderhub/requirements.txt requirements.txt
# Even though a binderhub wheel is built by the build stage, the requirements.txt
# file produced by pip-compile will still refer to `file:///src` as the source for it.
# We run this sed to tell it to just look for a package named `binderhub` instead, which
# will show up as a wheel in `/tmp/wheels`
RUN sed -i -E 's/binderhub @ file.+/binderhub/' requirements.txt

# install wheels built in the build stage
ARG PIP_CACHE_DIR=/tmp/pip-cache
# --no-index ensures _only_ wheels from the build stage are installed
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    --mount=type=cache,from=build-stage,source=/tmp/wheels,target=/tmp/wheels \
    pip install \
        --no-index \
        --find-links=/tmp/wheels/ \
        -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 8585
ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "binderhub", "--config", "/etc/binderhub/mounted-secret/binderhub_config.py"]
