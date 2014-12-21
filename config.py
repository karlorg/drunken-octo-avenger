from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '../db.sqlite')

SECRET_KEY = ':\x8dkR\xf9\x05\xc2\xd2,\xd4t\x0f\x0bvB\xbb\x1a.\xce\xbd\x0b\x17\xdc\xb7'
