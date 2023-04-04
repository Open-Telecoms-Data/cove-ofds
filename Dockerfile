FROM python:3.9-bullseye

# Setup

WORKDIR /app
COPY . .

RUN mkdir -p /app/static

# Python

RUN pip install -r requirements.txt

RUN python manage.py collectstatic --noinput

# Webserver

RUN apt-get update
RUN apt-get --assume-yes install nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Run

EXPOSE 80

# No run command - they are in Procfile and docker-compose.dev.yml
