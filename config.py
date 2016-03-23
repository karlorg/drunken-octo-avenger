import os
basedir = os.path.abspath(os.path.dirname(__file__))

DOMAIN = os.environ.get('TESUJI_CHARM_DOMAIN', 'localhost')
MAILGUN_SANDBOX = os.environ.get('MAILGUN_SANDBOX')
MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
admin_string = os.environ.get('TESUJI_CHARM_ADMINS', 'allan.clark@gmail.com')
ADMINS = admin_string.split(',')

DEBUG = True

LIVESERVER_PORT = 5000

sqlite_database_file = os.path.join(basedir, 'generated/db.sqlite')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + sqlite_database_file

SECRET_KEY = ':\x8dkR\xf9\x05\xc2\xd2,\xd4t\x0f\x0bvB\xbb\x1a.\xce\xbd\x0b\x17\xdc\xb7'  # noqa
