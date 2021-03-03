#!/bin/bash

until pg_isready -h postgres -p 5432
do
  echo "Waiting for postgres at: $pg_uri"
  sleep 2;
done

# Now able to connect to postgres
echo "Starting flask app..."

while true; do flask run --host 0.0.0.0; sleep 5; done