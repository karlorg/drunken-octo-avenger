from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

from flask import Flask, render_template, request, url_for

from collections import namedtuple


app = Flask(__name__)

@app.route('/game')
def game():
    img_path = '/static/images/goban/e.gif'
    goban = [None] * 19
    for i in xrange(len(goban)):
        goban[i] = [img_path] * 19
    stone = get_stone_if_args_good(args=request.args, moves=[])
    if stone is not None:
        goban[stone.row][stone.column] = '/static/images/goban/b.gif'
    return render_template("game.html", move_no=0, goban=goban)


def init_db():
    pass


Stone = namedtuple('Stone', ['row', 'column', 'color'])
def get_stone_if_args_good(args, moves):
    try:
        move_no = int(args['move_no'])
        row = int(args['row'])
        column = int(args['column'])
    except (KeyError, ValueError):
        return None
    if move_no != len(moves):
        return None
    color = ('black', 'white')[move_no % 2]
    return Stone(row=row, column=column, color=color)
