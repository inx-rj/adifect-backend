#!/bin/sh
python manage.py makemigrations authentication  --noinput
python manage.py makemigrations administrator  --noinput
python manage.py makemigrations agency  --noinput
python manage.py makemigrations creator  --noinput

python manage.py migrate
gunicorn adifect.wsgi:application --bind 0.0.0.0:8000  --timeout 600 
