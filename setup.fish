virtualenv -p /usr/bin/python3.4 generated/venv3.4
. develop.fish
pip install -r requirements.txt
python manage.py db upgrade
npm install phantomjs
npm install casperjs
npm install coffee-script
npm install coffeelint
