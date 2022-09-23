#!/bin/sh
python manage.py makemigrations --noinput
python manage.py makemigrations administrator
python manage.py makemigrations agency
python manage.py makemigrations creator
python manage.py migrate
gunicorn adifect.wsgi:application --bind 0.0.0.0:8000  --timeout 600 
