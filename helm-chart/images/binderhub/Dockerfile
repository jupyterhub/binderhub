FROM ubuntu:17.04

RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
            git \
            python3 \
            python3-setuptools \
            python3-pip && \
    apt-get clean

RUN pip3 install --no-cache-dir git+https://github.com/jupyterhub/binderhub.git@1d6f130b3b
ADD binderhub_config.py /etc

WORKDIR /etc

CMD python3 -m binderhub

EXPOSE 8585
