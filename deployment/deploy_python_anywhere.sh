#! /bin/sh

echo "Note you should be running this from the directory above migrations"

source setup.sh 3.4 prodvenv3.4
python manage.py coffeebuild
python manage.py db upgrade

echo "Check the wsgi file has the correct domain and then Go."
