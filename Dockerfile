FROM python:3.6-alpine

WORKDIR /app

COPY requirements.txt /app
RUN apk add --no-cache bash build-base wget bzip2 postgresql-dev
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
