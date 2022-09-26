#!/bin/sh

while ! python manage.py flush --no-input 2>&1; do
  echo "Flusing django manage command"
  sleep 3
done

echo "Migrate the Database at startup of project"

# Wait for few minute and run db migraiton
while ! python manage.py migrate  2>&1; do
   echo "Migration is in progress status"
   sleep 5
done

exec "$@"

#python manage.py migrate

gunicorn adifect.wsgi:application --bind 0.0.0.0:8000  --timeout 600
