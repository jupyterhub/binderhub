# syntax = docker/dockerfile:1.3


# The build stage
# ---------------
# This stage is building Python wheels for use in later stages by using a base
# image that has more pre-requisites to do so, such as a C++ compiler.
#
# NOTE: If the image version is updated, also update it in ci/refreeze!
#
FROM python:3.11-bookworm as build-stage

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
COPY requirements.txt requirements.txt
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    pip wheel \
        --wheel-dir=/tmp/wheels \
        # pycurl wheels for 7.45.3 have problems finding CAs
        # https://github.com/pycurl/pycurl/issues/834
        --no-binary pycurl \
        -r requirements.txt


# The final stage
# ---------------
# This stage is built and published as quay.io/2i2c/binderhub-service.
#
FROM python:3.11-slim-bookworm

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

# install wheels built in the build stage
COPY requirements.txt requirements.txt
# FIXME: As long as we reference git in requirements.txt (via requirements.in),
#        we need to make sure we don't end up re-installing from git here but
#        using the built wheel.
#
#        This sed replace operation removes the " @ git+..." stuff, remove it
#        when we reference version controlled releases of binderhub.
#
RUN sed -i -E 's/binderhub @ git.+/binderhub/' requirements.txt
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    --mount=type=cache,from=build-stage,source=/tmp/wheels,target=/tmp/wheels \
    pip install --find-links=/tmp/wheels/ \
        -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 8585
ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "binderhub", "--config", "/etc/binderhub/mounted-secret/binderhub_config.py"]
