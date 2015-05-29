from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from collections import namedtuple
from enum import IntEnum

class Color(IntEnum):
    empty = 0
    black = 1
    white = 2

Coord = namedtuple("Coord", ["x", "y"])

class Board(object):
    """Emulates a dict mapping `Coord`s to `Color`s."""

    def __init__(self, size=19):
        self._points = {Coord(x, y): Color.empty
                        for x in range(size)
                        for y in range(size)}

    def __getitem__(self, coord):
        return self._points[coord]

    def __setitem__(self, coord, color):
        self._points[coord] = color

    def __iter__(self):
        return self._points.__iter__()

    def items(self):
        return self._points.items()

    def update_with_move(self, move):
        """Update board to the state it should be in after the move is played.

        Modifies self.

        :param move: an object with column, row, and color attributes.
                     color is an instance of the Color enum.
        """
        try:
            enemy = {Color.white: Color.black,
                     Color.black: Color.white}.get(move.color)
        except:  # pragma: no cover
            assert False, "attempted board update with invalid color"

        def process_captures(coord):
            for n_coord in self._get_neighbours(coord):
                if self[n_coord] == enemy:
                    if self._count_liberties(n_coord) == 0:
                        for p in self._get_group(n_coord):
                            self[p] = Color.empty

        move_coord = Coord(x=move.column, y=move.row)
        if self[move_coord] == Color.empty:
            self[move_coord] = move.color
        else:
            raise IllegalMoveException("point already occupied", move.move_no)
        process_captures(move_coord)

        if self._count_liberties(move_coord) == 0:
            # thankfully, if we still have no liberties then no captures have
            # occurred, so we can revert the board position simply by removing
            # the stone we just played
            self[move_coord] = Color.empty
            raise IllegalMoveException("playing into no liberties",
                                       move.move_no)

    def _get_group(self, coord):
        """Return the group of the stone at coord as an iterable of coords.

        Pure function.
        """
        ally = self[coord]
        if ally is Color.empty:
            raise EmptyPointGroupException

        def get_group_recursive(coord, group_so_far):
            # group_so_far is a set
            group_so_far |= set([coord])
            neighbours_to_recurse = filter(
                lambda p: self[p] is ally and p not in group_so_far,
                self._get_neighbours(coord)
            )
            for n_coord in neighbours_to_recurse:
                group_so_far |= get_group_recursive(n_coord, group_so_far)
            return group_so_far

        return get_group_recursive(coord, set())

    def _get_neighbours(self, coord):
        """Return the neighbouring points of coord as an iterable of coords.

        Pure function.
        """
        x = coord.x
        y = coord.y
        return (Coord(x=x0, y=y0)
                for x0, y0 in ((x, y-1), (x+1, y), (x, y+1), (x-1, y))
                if Coord(x=x0, y=y0) in self)

    def _count_liberties(self, coord):
        """Count the liberties of the group containing the stone (r,c).

        Pure function.
        """
        if self[coord] is Color.empty:
            raise EmptyPointLibertiesException
        liberties = set()
        for g_coord in self._get_group(coord):
            liberties |= set(n_coord
                             for n_coord in self._get_neighbours(g_coord)
                             if self[n_coord] == Color.empty)
        return len(liberties)


class EmptyPointGroupException(Exception):
    pass

class EmptyPointLibertiesException(Exception):
    pass

class IllegalMoveException(Exception):
    def __init__(self, message, move_no=None):
        super().__init__(message)
        self.move_no = move_no
