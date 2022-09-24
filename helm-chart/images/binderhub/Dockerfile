# syntax = docker/dockerfile:1.3


# The build stage
# ---------------
#
# NOTE: If the image version is updated, also update it in ci/refreeze!
#
FROM python:3.9-bullseye as build-stage
WORKDIR /build-stage

# install node as required to build a binderhub wheel
RUN echo "deb https://deb.nodesource.com/node_16.x bullseye main" > /etc/apt/sources.list.d/nodesource.list \
 && curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN apt-get update \
 && apt-get install --yes \
        nodejs \
 && rm -rf /var/lib/apt/lists/*

# build wheels to be mounted through a cache in the final stage
ARG PIP_CACHE_DIR=/tmp/pip-cache
COPY . .
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    pip install build \
 && pip wheel \
       . \
       pycurl \
       -r helm-chart/images/binderhub/requirements.txt


# The final stage
# ---------------
FROM python:3.9-slim-bullseye

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
ARG PIP_CACHE_DIR=/tmp/pip-cache
COPY helm-chart/images/binderhub/requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    --mount=type=cache,from=build-stage,source=/build-stage,target=/tmp/wheels \
    pip install --find-links=/tmp/wheels/ \
        binderhub \
        pycurl \
        -r /tmp/requirements.txt

# verify success of previous step
RUN python -c "import pycurl, binderhub.app"

EXPOSE 8585
ENTRYPOINT ["tini", "--", "python", "-m", "binderhub"]
CMD ["--config", "/etc/binderhub/config/binderhub_config.py"]
