from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

from flask import Flask, render_template


app = Flask(__name__)

@app.route('/game')
def game():
    return render_template("game.html", foo="bar")


def init_db():
    pass

if __name__ == '__main__':
    app.debug = True
    app.run()
