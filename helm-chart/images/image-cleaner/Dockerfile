FROM python:3.6-alpine3.6

ADD *.py /srv/image-cleaner/
WORKDIR /srv/image-cleaner

RUN pip3 install --no-cache-dir docker-py

ENTRYPOINT ['/srv/image-cleaner/image-cleaner.py']