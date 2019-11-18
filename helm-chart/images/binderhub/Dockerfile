# Using multi-stage builds
# ref: https://docs.docker.com/develop/develop-images/multistage-build/
FROM buildpack-deps:stretch as build-stage

RUN echo 'deb http://deb.nodesource.com/node_8.x artful main' > /etc/apt/sources.list.d/nodesource.list \
 && curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -

RUN apt-get update && \
    apt-get install --yes \
        nodejs \
        python3 \
        python3-pip \
        python3-wheel \
        python3-setuptools

# Copy the whole git repository to /tmp/binderhub
COPY . /tmp/binderhub
WORKDIR /tmp/binderhub

# Build binderhub the python library
RUN python3 setup.py bdist_wheel

# The final stage
# ---------------
FROM python:3.6-stretch
WORKDIR /

# Copy the built binderhub python wheel from the build-stage
# to the current directory within the container.
COPY --from=build-stage /tmp/binderhub/dist/*.whl .

# Copy the additional Python requirements for our Docker container from the
# build context. These can be certain pinned versions or peer dependencies.
COPY helm-chart/images/binderhub/requirements.txt .
RUN pip install --no-cache-dir \
        *.whl \
        -r requirements.txt

# Copy the binderhub configuration to use.
# FUTURE: Follow the approach taken in Z2JH:
#         https://github.com/jupyterhub/zero-to-jupyterhub-k8s/pull/1478
COPY helm-chart/images/binderhub/binderhub_config.py .

CMD ["python3", "-m", "binderhub"]
ENV PYTHONUNBUFFERED=1
EXPOSE 8585
