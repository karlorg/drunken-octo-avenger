from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

from app.main import app


if __name__ == '__main__':
    app.debug = True
    app.run()
