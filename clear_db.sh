#! /bin/sh

rm -r hyper/migrations
mkdir hyper/migrations
touch hyper/migrations/__init__.py 

rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations hyper
python manage.py migrate hyper
