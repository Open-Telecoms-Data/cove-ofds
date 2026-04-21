FROM python:3.11-bullseye

# Setup

WORKDIR /app

RUN mkdir -p /app/static

# Webserver
RUN apt-get update
RUN apt-get --assume-yes install nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Allow git to run on a repo owned by another user
RUN git config --global --add safe.directory /app

# Copy most of the files near the end so we don't have to redo all the above steps when any of them change
COPY . .
RUN python manage.py collectstatic --noinput


# Run

EXPOSE 80

# No run command - they are in Procfile and docker-compose.dev.yml
