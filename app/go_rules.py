from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from enum import Enum

class Color(Enum):
    empty = 0
    black = 1
    white = 2

class EmptyPointLibertiesException(Exception):
    pass

class IllegalMoveException(Exception):
    def __init__(self, message, move_no=None):
        super().__init__(message)
        self.move_no = move_no

def empty_board(size=19):
    return {(r, c): Color.empty for r in range(size) for c in range(size)}

def update_board_with_move(board, color, r, c, move_no=None):
    """Update `board` to the state it should be in after the move is played.

    Modifies its argument `board`.
    """
    def process_captures(board, r, c):
        for (r0, c0) in get_neighbours(board, r, c):
            if board[(r0, c0)] is not Color.empty:
                if count_liberties(board, r0, c0) == 0:
                    board[(r0, c0)] = Color.empty

    if board[(r, c)] == Color.empty:
        board[(r, c)] = color
    else:
        raise IllegalMoveException("point already occupied", move_no)
    process_captures(board, r, c)

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
