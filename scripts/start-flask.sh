#!/bin/bash


# 
until pg_isready -h $1 -p 5432 --username $(echo $DATABASE_URI | awk -F '@|://|:' '{print $2}')
do
 echo "Waiting for postgres at: $DATABASE_URI"
 sleep 2;
done

# Now able to connect to postgres
echo "Starting flask app..."

while true; do flask run --host 0.0.0.0; sleep 5; done
