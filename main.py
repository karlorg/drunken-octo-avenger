from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

from flask import Flask, render_template, url_for


app = Flask(__name__)

@app.route('/game')
def game():
    img_path = '/static/images/goban/e.gif'
    return render_template("game.html", move_no=0, 
            goban=[[img_path] * 19] * 19)


def init_db():
    pass

if __name__ == '__main__':
    app.debug = True
    app.run()
