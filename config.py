from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import os
basedir = os.path.abspath(os.path.dirname(__file__))

DOMAIN = os.environ.get('TESUJI_CHARM_DOMAIN', 'localhost')
MAILGUN_SANDBOX = os.environ.get('MAILGUN_SANDBOX')
MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
admin_string = os.environ.get('TESUJI_CHARM_ADMINS', 'allan.clark@gmail.com')
ADMINS = admin_string.split(',')

DEBUG = True

LIVESERVER_PORT = 5000

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '../db.sqlite')

SECRET_KEY = ':\x8dkR\xf9\x05\xc2\xd2,\xd4t\x0f\x0bvB\xbb\x1a.\xce\xbd\x0b\x17\xdc\xb7'  # noqa
