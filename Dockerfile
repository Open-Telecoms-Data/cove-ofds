FROM python:3.9-bullseye

WORKDIR /app
COPY . .

RUN mkdir -p /app/static

RUN pip install -r requirements.txt

RUN python manage.py collectstatic

EXPOSE 80

CMD gunicorn --bind 0.0.0.0:80 cove_project.wsgi:application
