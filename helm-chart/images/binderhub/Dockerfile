FROM python:3.6-alpine@sha256:00320c25fa72df54c7ef0181c9e55f59f58b1facb943cb825e4c65fb572ac74b

RUN pip install --no-cache-dir \
    https://github.com/jupyterhub/binderhub/archive/1e3dd8e.zip
ADD binderhub_config.py /etc

WORKDIR /etc

CMD python3 -m binderhub

EXPOSE 8585
