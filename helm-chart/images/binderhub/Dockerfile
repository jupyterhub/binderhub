# We use a build stage to package binderhub and pycurl into a wheel which we
# then install by itself in the final image which is relatively slimmed.
ARG DIST=buster


# The build stage
# ---------------
FROM python:3.8-$DIST as build-stage
# ARG DIST is defined again to be made available in this build stage's scope.
# ref: https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG DIST

# Install node as required to package binderhub to a wheel
RUN echo "deb http://deb.nodesource.com/node_14.x $DIST main" > /etc/apt/sources.list.d/nodesource.list \
 && curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN apt-get update \
 && apt-get install --yes \
        nodejs \
 && rm -rf /var/lib/apt/lists/*

# Copy the whole git repository to /tmp/binderhub
COPY . /tmp/binderhub
WORKDIR /tmp/binderhub

# Build the binderhub python library into a wheel and save it to the ./dist
# folder. There are no pycurl wheels so we build our own in the build stage.
RUN python setup.py bdist_wheel
RUN pip wheel pycurl --wheel-dir ./dist


# The final stage
# ---------------
FROM python:3.8-slim-$DIST
WORKDIR /

# The slim version doesn't include git as required by binderhub
RUN apt-get update \
 && apt-get install --yes \
        git \
 && rm -rf /var/lib/apt/lists/*


# Copy the built wheels from the build-stage. Also copy the image
# requirements.txt built from the binderhub package requirements.txt and the
# requirements.in file using the ./dependency script.
COPY --from=build-stage /tmp/binderhub/dist/*.whl pre-built-wheels/
COPY helm-chart/images/binderhub/requirements.txt .

# Install pre-built wheels and the generated requirements.txt for the image.
RUN pip install --no-cache-dir \
        pre-built-wheels/*.whl \
        -r requirements.txt

# When using the ./dependency script to output a frozen environment, we do it
# from within this container. So below we conditionally install pip-tools for
# use by the ./dependency script.
ARG PIP_TOOLS=
RUN test -z "$PIP_TOOLS" || pip install --no-cache pip-tools==$PIP_TOOLS

ENTRYPOINT ["python3", "-m", "binderhub"]
CMD ["--config", "/etc/binderhub/config/binderhub_config.py"]
ENV PYTHONUNBUFFERED=1
EXPOSE 8585
