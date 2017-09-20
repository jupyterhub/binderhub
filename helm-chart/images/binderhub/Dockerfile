FROM python:3.6-alpine@sha256:00320c25fa72df54c7ef0181c9e55f59f58b1facb943cb825e4c65fb572ac74b

# FIXME: temporary ref pending binderhub#110
RUN pip install --no-cache-dir https://github.com/minrk/binderhub/archive/b5d005a.zip
ADD binderhub_config.py /etc

WORKDIR /etc

CMD python3 -m binderhub

EXPOSE 8585
