# syntax = docker/dockerfile:1.3


# The build stage
# ---------------
# This stage is building Python wheels for use in later stages by using a base
# image that has more pre-requisites to do so, such as a C++ compiler.
#
# NOTE: If the image version is updated, also update it in ci/refreeze!
#
FROM python:3.11-bullseye as build-stage

# Build wheels
#
# We set pip's cache directory and expose it across build stages via an
# ephemeral docker cache (--mount=type=cache,target=${PIP_CACHE_DIR}). We use
# the same technique for the directory /tmp/wheels.
#
# assumes `python3 -m build .` has been run to create the wheel
# in the top-level dist directory
COPY helm-chart/images/binderhub/requirements.txt ./
COPY dist .
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    pip install build \
 && pip wheel --wheel-dir=/tmp/wheels \
        -r ./requirements.txt \
        ./binderhub*.whl


# The final stage
# ---------------
# This stage is built and published as jupyterhub/k8s-binderhub.
#
FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get upgrade --yes \
 && apt-get install --yes \
        git \
              # required by binderhub
        libcurl4 \
              # required by pycurl
        tini \
              # tini is used as an entrypoint to not loose track of SIGTERM
              # signals as sent before SIGKILL, for example when "docker stop"
              # or "kubectl delete pod" is run. By doing that the pod can
              # terminate very quickly.
 && rm -rf /var/lib/apt/lists/*

# install wheels built in the build stage
COPY helm-chart/images/binderhub/requirements.txt /tmp/requirements.txt
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    --mount=type=cache,from=build-stage,source=/tmp/wheels,target=/tmp/wheels \
    pip install --no-deps /tmp/wheels/* \
    # validate pip install since it's not resolving dependencies
 && pip check \
    # verify success of previous step
 && python -c "import pycurl, binderhub.app"

EXPOSE 8585
ENTRYPOINT ["tini", "--", "python", "-m", "binderhub"]
CMD ["--config", "/etc/binderhub/config/binderhub_config.py"]
