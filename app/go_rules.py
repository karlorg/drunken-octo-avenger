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

class EmptyPointGroupException(Exception):
    pass

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
                    for p in get_group(board, r0, c0):
                        board[p] = Color.empty

    if board[(r, c)] == Color.empty:
        board[(r, c)] = color
    else:
        raise IllegalMoveException("point already occupied", move_no)
    process_captures(board, r, c)

def get_group(board, r, c):
    """Return the group of the stone at (r,c) as an iterable of coords.

    Pure function.
    """
    ally = board[(r, c)]
    if ally is Color.empty:
        raise EmptyPointGroupException

    def get_group_recursive(r, c, group_so_far):
        # group_so_far is a set
        group_so_far |= set([(r, c)])
        neighbours_to_recurse = filter(
            lambda p: board[p] is ally and p not in group_so_far,
            get_neighbours(board, r, c)
        )
        for (r0, c0) in neighbours_to_recurse:
            group_so_far |= get_group_recursive(r0, c0, group_so_far)
        return group_so_far

    return get_group_recursive(r, c, set())

def get_neighbours(board, r, c):
    """Return the neighbouring points of (r,c) as an iterable of coords.

    Pure function.
    """
    return filter(lambda p: p in board,
                  ((r-1, c), (r, c+1), (r+1, c), (r, c-1)))

def count_liberties(board, r, c):
    """Count the liberties of the group containing the stone (r,c).

    Pure function.
    """
    if board[(r, c)] is Color.empty:
        raise EmptyPointLibertiesException

    liberties = set()
    for (r0, c0) in get_group(board, r, c):
        liberties |= set(filter(
                lambda p: board[p] == Color.empty,
                get_neighbours(board, r0, c0)
        ))

    return len(liberties)
