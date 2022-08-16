# We use a build stage to package binderhub and pycurl into a wheel which we
# then install by itself in the final image which is relatively slimmed.
ARG DIST=bullseye


# The build stage
# ---------------
FROM python:3.9-$DIST as build-stage
# ARG DIST is defined again to be made available in this build stage's scope.
# ref: https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG DIST

# Install node as required to package binderhub to a wheel
RUN echo "deb https://deb.nodesource.com/node_16.x $DIST main" > /etc/apt/sources.list.d/nodesource.list \
 && curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN apt-get update \
 && apt-get install --yes \
        nodejs \
 && rm -rf /var/lib/apt/lists/*

# Copy the whole git repository to /tmp/binderhub
COPY . /tmp/binderhub
WORKDIR /tmp/binderhub

# Build the binderhub python library into a wheel and save it to the ./dist
# folder. There are no pycurl or ruamel.yaml.clib wheels so we build our own in
# the build stage.
RUN python -mpip install build && python -mbuild --wheel .
RUN pip wheel --wheel-dir ./dist \
       pycurl \
       ruamel.yaml.clib

# We download tini from here were we have wget available.
RUN ARCH=$(uname -m); \
    if [ "$ARCH" = x86_64 ]; then ARCH=amd64; fi; \
    if [ "$ARCH" = aarch64 ]; then ARCH=arm64; fi; \
    wget -qO /tini "https://github.com/krallin/tini/releases/download/v0.19.0/tini-$ARCH" \
 && chmod +x /tini

# The final stage
# ---------------
FROM python:3.9-slim-$DIST
WORKDIR /

# We use tini as an entrypoint to not loose track of SIGTERM signals as sent
# before SIGKILL when "docker stop" or "kubectl delete pod" is run. By doing
# that the pod can terminate very quickly.
COPY --from=build-stage /tini /tini

# The slim version doesn't include git as required by binderhub
# or libcurl required by pycurl
RUN apt-get update \
 && apt-get install --yes \
        git \
        libcurl4 \
 && rm -rf /var/lib/apt/lists/*

# Copy the built wheels from the build-stage. Also copy the image
# requirements.txt built from the binderhub package requirements.txt and the
# requirements.in file using pip-compile.
COPY --from=build-stage /tmp/binderhub/dist/*.whl pre-built-wheels/
COPY helm-chart/images/binderhub/requirements.txt .

# Install pre-built wheels and the generated requirements.txt for the image.
# make sure that imports work,
# because wheels were built in the build-stage
RUN pip install --no-cache-dir \
        pre-built-wheels/*.whl \
        -r requirements.txt \
 && python3 -c "import pycurl, binderhub.app"

ENTRYPOINT ["/tini", "--", "python3", "-m", "binderhub"]
CMD ["--config", "/etc/binderhub/config/binderhub_config.py"]
ENV PYTHONUNBUFFERED=1
EXPOSE 8585
