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

class EmptyPointLibertiesException(Exception):
    pass

class IllegalMoveException(Exception):
    def __init__(self, message, move_no=None):
        super().__init__(message)
        self.move_no = move_no

def empty_board(size=19):
    return {(r, c): Color.empty for r in range(size) for c in range(size)}

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

    board = empty_board()
    for n, move in enumerate(moves):
        process_stone(n)
        update_board_with_move(board, move, n)
    process_stone(len(moves))
    return board

def update_board_with_move(board, move, move_no=None):
    """Update `board` to the state it should be in after `move` is played.

    Modifies its argument `board`.
    """
    def process_captures(board, r, c):
        for (r0, c0) in get_neighbours(board, r, c):
            if board[(r0, c0)] is not Color.empty:
                if count_liberties(board, r0, c0) == 0:
                    board[(r0, c0)] = Color.empty

    if board[(move.row, move.column)] == Color.empty:
        board[(move.row, move.column)] = move.color
    else:
        raise IllegalMoveException("point already occupied", move_no)
    process_captures(board, move.row, move.column)

def get_neighbours(board, r, c):
    return filter(lambda p: p in board,
                  ((r-1, c), (r, c+1), (r+1, c), (r, c-1)))

def count_liberties(board, r, c):
    ally = board[(r, c)]
    if ally is Color.empty:
        raise EmptyPointLibertiesException

    def find_liberties_internal(r, c, stones_seen):
        neighbours_to_count = list(filter(
            lambda p: board[p] is ally and p not in stones_seen,
            get_neighbours(board, r, c)
        ))
        sub_results = set()
        for (r0, c0) in neighbours_to_count:
            sub_results.update(
                    find_liberties_internal(
                        r0, c0, stones_seen.union([(r, c)])
                    )
            )
        my_liberties = set(filter(lambda p: board[p] is Color.empty,
                                  get_neighbours(board, r, c)))
        return my_liberties | sub_results

    return len(find_liberties_internal(r, c, set()))
