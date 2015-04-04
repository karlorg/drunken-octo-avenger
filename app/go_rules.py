from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from enum import IntEnum

class Color(IntEnum):
    empty = 0
    black = 1
    white = 2

class Board(object):
    def __init__(self, size=19):
        self._points = {(r, c): Color.empty
                        for r in range(size)
                        for c in range(size)}

    def __getitem__(self, coords):
        """ Coords should be a pair consisting of row and column numbers """
        return self._points[coords]

    def __setitem__(self, coords, color):
        """ As above, coords should be a pair consisting of row and column """
        self._points[coords] = color

    def items(self):
        return self._points.items()

    def update_with_move(self, move):
        """Update board to the state it should be in after the move is played.

        Modifies self.
        """
        try:
            enemy = {Color.white: Color.black,
                     Color.black: Color.white}.get(move.color)
        except:  # pragma: no cover
            assert False, "attempted board update with invalid color"

        def process_captures(r, c):
            for (r0, c0) in self._get_neighbours(r, c):
                if self._points[(r0, c0)] is enemy:
                    if self._count_liberties(r0, c0) == 0:
                        for p in self._get_group(r0, c0):
                            self._points[p] = Color.empty

        if self._points[(move.row, move.column)] == Color.empty:
            self._points[(move.row, move.column)] = move.color
        else:
            raise IllegalMoveException("point already occupied", move.move_no)
        process_captures(move.row, move.column)

        if self._count_liberties(move.row, move.column) == 0:
            # thankfully, if we still have no liberties then no captures have
            # occurred, so we can revert the board position simply by removing
            # the stone we just played
            self._points[(r, c)] = Color.empty
            raise IllegalMoveException("playing into no liberties", move_no)

    def _get_group(self, r, c):
        """Return the group of the stone at (r,c) as an iterable of coords.

        Pure function.
        """
        ally = self._points[(r, c)]
        if ally is Color.empty:
            raise EmptyPointGroupException

        def get_group_recursive(r, c, group_so_far):
            # group_so_far is a set
            group_so_far |= set([(r, c)])
            neighbours_to_recurse = filter(
                lambda p: self._points[p] is ally and p not in group_so_far,
                self._get_neighbours(r, c)
            )
            for (r0, c0) in neighbours_to_recurse:
                group_so_far |= get_group_recursive(r0, c0, group_so_far)
            return group_so_far

        return get_group_recursive(r, c, set())

    def _get_neighbours(self, r, c):
        """Return the neighbouring points of (r,c) as an iterable of coords.

        Pure function.
        """
        return filter(lambda p: p in self._points,
                      ((r-1, c), (r, c+1), (r+1, c), (r, c-1)))

    def _count_liberties(self, r, c):
        """Count the liberties of the group containing the stone (r,c).

        Pure function.
        """
        if self._points[(r, c)] is Color.empty:
            raise EmptyPointLibertiesException

        liberties = set()
        for (r0, c0) in self._get_group(r, c):
            liberties |= set(filter(
                    lambda p: self._points[p] == Color.empty,
                    self._get_neighbours(r0, c0)
            ))

        return len(liberties)


class EmptyPointGroupException(Exception):
    pass

class EmptyPointLibertiesException(Exception):
    pass

class IllegalMoveException(Exception):
    def __init__(self, message, move_no=None):
        super().__init__(message)
        self.move_no = move_no
