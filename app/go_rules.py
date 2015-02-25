from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from collections import namedtuple
from enum import Enum

class Color(Enum):
    empty = 0
    black = 1
    white = 2

Stone = namedtuple('Stone', ['color', 'row', 'column'])

def empty_board():
    return {(r, c): Color.empty for r in range(19) for c in range(19)}

def board_from(moves, setup_stones):
    """Return a board given a list of moves and a dict of setup stones.

    `setup_stones` is indexed by move number and each value is a list of
    stones.  The setup stones for a move will be placed before that move is
    played.
    """
    board = empty_board()

    def process_stone(n):
        try:
            stones = setup_stones[n]
        except KeyError:
            pass
        else:
            for stone in stones:
                board[(stone.row, stone.column)] = stone.color

    for n, move in enumerate(moves):
        process_stone(n)
        board[(move.row, move.column)] = move.color
    process_stone(len(moves))
    return board
