from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '../db.sqlite')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'migrations')
