virtualenv -p /usr/bin/python3.4 ../venv3.4
. develop.fish
pip install -r p3req.txt
python manage.py db upgrade
npm install phantomjs
npm install casperjs
