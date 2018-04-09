FROM buildpack-deps:stretch

RUN echo 'deb http://deb.nodesource.com/node_8.x artful main' > /etc/apt/sources.list.d/nodesource.list

RUN curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN apt-get update && \
    apt-get install --yes nodejs python3 python3-pip python3-wheel python3-setuptools

COPY . /tmp/binderhub
WORKDIR /tmp/binderhub

RUN python3 setup.py bdist_wheel

FROM python:3.6-stretch

COPY --from=0 /tmp/binderhub/dist/*.whl .
ADD helm-chart/images/binderhub/binderhub_config.py .
ADD helm-chart/images/binderhub/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir *.whl -r /tmp/requirements.txt

CMD ["python3", "-m", "binderhub"]
EXPOSE 8585
