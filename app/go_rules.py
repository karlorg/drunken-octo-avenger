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

class IllegalMoveException(Exception):
    def __init__(self, message, move_no):
        super().__init__(message)
        self.move_no = move_no

def empty_board():
    return {(r, c): Color.empty for r in range(19) for c in range(19)}

def board_from(moves, setup_stones):
    """Return a board given a list of moves and a dict of setup stones.

    `setup_stones` is indexed by move number and each value is a list of
    stones.  The setup stones for a move will be placed before that move is
    played.
    """

    def process_stone(n):
        if n in setup_stones:
            for stone in setup_stones[n]:
                board[(stone.row, stone.column)] = stone.color

    def process_captures(board, r, c):
        for (r0, c0) in get_neighbours(board, r, c):
            if count_liberties(board, r0, c0) == 0:
                board[(r0, c0)] = Color.empty

    board = empty_board()
    for n, move in enumerate(moves):
        process_stone(n)
        if board[(move.row, move.column)] == Color.empty:
            board[(move.row, move.column)] = move.color
        else:
            raise IllegalMoveException("point already occupied", n)
        process_captures(board, move.row, move.column)
    process_stone(len(moves))
    return board

def get_neighbours(board, r, c):
    return filter(lambda p: p in board,
                  ((r-1, c), (r, c+1), (r+1, c), (r, c-1)))

def count_liberties(board, r, c):
    return len(list(filter(lambda p: board[p] is Color.empty,
                           get_neighbours(board, r, c))))
