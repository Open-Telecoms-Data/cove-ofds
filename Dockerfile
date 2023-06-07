FROM python:3.9-bullseye

# Setup

WORKDIR /app
COPY . .

RUN mkdir -p /app/static

# Python

# Build our own copy of lxml using Ubuntu's libraries
# https://opendataservices.plan.io/issues/36790
RUN apt-get update
RUN apt-get --assume-yes install libxml2-dev libxslt-dev
RUN pip install --no-binary lxml -r requirements.txt

RUN python manage.py collectstatic --noinput

# Webserver

RUN apt-get --assume-yes install nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Run

EXPOSE 80

# No run command - they are in Procfile and docker-compose.dev.yml
