FROM python:3.8-slim-buster

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY image-cleaner.py /usr/local/bin/image-cleaner.py
# set PYTHONUNBUFFERED to ensure output is produced
ENV PYTHONUNBUFFERED=1
CMD image-cleaner.py
