#!/bin/sh
python manage.py makemigrations authentication
python manage.py makemigrations administrator
python manage.py makemigrations agency
python manage.py makemigrations creator
sleep 5

echo "Migrate the Database at startup of project"

# Wait for few minute and run db migraiton
while ! python manage.py migrate  2>&1; do
   echo "Migration is in progress status"
   sleep 5
done

#python manage.py migrate

gunicorn adifect.wsgi:application --bind 0.0.0.0:8000  --timeout 600
