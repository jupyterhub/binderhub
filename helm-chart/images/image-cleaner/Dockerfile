FROM python:3.6-alpine3.6

ADD image-cleaner.py /usr/local/bin/image-cleaner.py

RUN pip3 install --no-cache-dir docker==3.2.1
# set PYTHONUNBUFFERED to ensure output is produced
ENV PYTHONUNBUFFERED=1
CMD image-cleaner.py
