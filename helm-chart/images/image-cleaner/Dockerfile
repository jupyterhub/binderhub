ARG DIST=slim-buster
FROM python:3.7-$DIST

ADD requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

ADD image-cleaner.py /usr/local/bin/image-cleaner.py
# set PYTHONUNBUFFERED to ensure output is produced
ENV PYTHONUNBUFFERED=1
CMD image-cleaner.py
