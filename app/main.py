from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

from collections import namedtuple
from enum import IntEnum

from flask import Flask, render_template, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

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


class Move(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    row = db.Column(db.Integer)
    column = db.Column(db.Integer)
    move_no = db.Column(db.Integer)
    
    class Color(IntEnum):
        black = 0
        white = 1
    color = db.Column(db.Integer)

    def __init__(self, move_no, row, column, color):
        self.move_no = move_no
        self.row = row
        self.column = column
        self.color = color

    def __repr__(self):
        return '<Move {0}: {1} at ({2},{3})>'.format(
                self.move_no, Color(self.color).name,
                self.column, self.row)
