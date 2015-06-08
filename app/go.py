from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from collections import namedtuple
from enum import IntEnum

from app import sgftools

class Color(IntEnum):
    empty = 0
    black = 1
    white = 2

class ValidationException(Exception):
    def __init__(self, message, move_no=None):
        super().__init__(message)
        self.move_no = move_no

def is_sgf_passed_twice(sgf):
    nodes = _GameTree.from_sgf(sgf).main_line
    if len(nodes) < 2:
        return False
    for node in nodes[-2:]:
        if not node.is_pass:
            return False
    return True

def check_continuation(old_sgf, new_sgf, allowed_new_moves=1):
    new_is_valid = _is_valid(new_sgf)
    new_continues_old = _is_continuation(old_sgf, new_sgf)
    return new_is_valid and new_continues_old

def _is_valid(sgf):
    nodes = _GameTree.from_sgf(sgf).main_line
    board = _Board()
    move_no = 0
    for node in nodes:
        if node.is_setup:
            for coord in node.setup_coords_black:
                board[coord] = Color.black
            for coord in node.setup_coords_white:
                board[coord] = Color.white
        elif node.is_move:
            board.update_with_move(node.move_coord, node.move_color, move_no)
            move_no += 1
    # if none of those updates raised, it's a valid sequence
    return True

def _is_continuation(old_sgf, new_sgf, allowed_new_moves=1):
    assert allowed_new_moves == 1, "(allowed_new_moves != 1) not implemented"
    old_nodes = _GameTree.from_sgf(old_sgf).main_line
    new_nodes = _GameTree.from_sgf(new_sgf).main_line
    if len(old_nodes) >= len(new_nodes):
        raise ValidationException("no new node",
                                  move_no=len(new_nodes))
    if len(new_nodes) - len(old_nodes) > 1:
        raise ValidationException("too many new moves",
                                  move_no=len(old_nodes) + 1)
    if old_nodes != new_nodes[:-1]:
        raise ValidationException("games don't match",
                                  move_no=0)
    return True

def next_move_no(sgf):
    game_tree = _GameTree.from_sgf(sgf)
    no = 1
    for node in game_tree.main_line:
        if node.is_action:
            no += 1
    return no

# helper facilities for playing out a simulated game on a board and checking
# legality

_Coord = namedtuple("Coord", ["x", "y"])

class _Board(object):
    """Emulates a dict mapping `_Coord`s to `Color`s."""

    def __init__(self, size=19):
        self._points = {_Coord(x, y): Color.empty
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

    def update_with_move(self, coord, color, move_no):
        """Update board to the state it should be in after the move is played.

        Modifies self.
        """
        try:
            enemy = {Color.white: Color.black,
                     Color.black: Color.white}.get(color)
        except:  # pragma: no cover
            assert False, "attempted board update with invalid color"

        def process_captures(coord0):
            for n_coord in self._get_neighbours(coord0):
                if self[n_coord] == enemy:
                    if self._count_liberties(n_coord) == 0:
                        for p in self.get_group(n_coord):
                            self[p] = Color.empty

        if self[coord] == Color.empty:
            self[coord] = color
        else:
            raise ValidationException("point already occupied", move_no)
        process_captures(coord)

        if self._count_liberties(coord) == 0:
            # thankfully, if we still have no liberties then no captures have
            # occurred, so we can revert the board position simply by removing
            # the stone we just played
            self[coord] = Color.empty
            raise ValidationException("playing into no liberties",
                                      move_no)

    def get_group(self, coord, include=None):
        """Return the group of the stone at coord as an iterable of coords.

        Pure function.
        """
        if include is None:
            include = [self[coord]]
            if include[0] is Color.empty:
                raise EmptyPointGroupException

        def get_group_recursive(coord, group_so_far):
            # group_so_far is a set
            group_so_far |= set([coord])
            neighbours_to_recurse = (
                n for n in self._get_neighbours(coord)
                if self[n] in include and n not in group_so_far)
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
        return (_Coord(x=x0, y=y0)
                for x0, y0 in ((x, y-1), (x+1, y), (x, y+1), (x-1, y))
                if _Coord(x=x0, y=y0) in self)

    def _count_liberties(self, coord):
        """Count the liberties of the group containing the stone (r,c).

        Pure function.
        """
        if self[coord] is Color.empty:
            raise EmptyPointLibertiesException
        liberties = set()
        for g_coord in self.get_group(coord):
            liberties |= set(n for n in self._get_neighbours(g_coord)
                             if self[n] == Color.empty)
        return len(liberties)


class EmptyPointGroupException(Exception):
    pass

class EmptyPointLibertiesException(Exception):
    pass

# GameTree abstraction of a parsed game

class _GameTree(object):
    """An abstract representation of a game history.

    Use `.main_line` to obtain a list of _GameNodes.  A node is either
    a move, a pass, or setup stones.
    """

    def __init__(self, sgf_tree):
        """Don't call directly please, may change.

        Use classmethod instantiators instead.
        """
        self.nodes = self._nodes_from_sgf_nodes(sgf_tree.main_line)
        self.main_line = self.nodes

    @classmethod
    def from_sgf(cls, sgf):
        sgf_tree = sgftools.parse(sgf)
        return cls(sgf_tree)

    @classmethod
    def from_sgf_tree(cls, sgf_tree):
        return cls(sgf_tree)

    @staticmethod
    def _nodes_from_sgf_nodes(sgf_nodes):
        result = []
        for node in sgf_nodes:
            result.extend(_GameNode.from_sgf_node(node))
        return result


class _GameNode(object):

    def __init__(self):
        """Not for use by client code"""
        self.is_move = False
        """Does this node represent a stone played at a coordinate?"""
        self.is_pass = False
        """Does this node represent a pass?"""
        self.is_setup = False
        """Does this node place setup stones outside the game rules?"""

    @classmethod
    def _make_setup(cls, sgf_node):
        result = cls()
        result.is_setup = True
        result.setup_coords_black = set(cls._decode_or_invalid(chars)
                                        for chars in sgf_node.get('AB', []))
        result.setup_coords_white = set(cls._decode_or_invalid(chars)
                                        for chars in sgf_node.get('AW', []))
        return result

    @classmethod
    def _make_move_or_pass(cls, color, tag_value):
        result = cls()
        result.move_color = color
        coord = result._decode_or_none(tag_value[0])
        if coord:
            result.move_coord = coord
            result.is_move = True
        else:
            result.is_pass = True
        return result

    @classmethod
    def _decode_or_none(cls, chars):
        try:
            return cls._decode_or_invalid(chars)
        except ValidationException:
            return None

    @staticmethod
    def _decode_or_invalid(chars):
        try:
            x, y = sgftools.decode_coord(chars)
        except ValueError:
            raise ValidationException(
                "unparseable coordinate {c}".format(c=chars))
        else:
            return _Coord(x=x, y=y)

    @classmethod
    def from_sgf_node(cls, sgf_node):
        """Return a list of nodes built from the given SGF node."""
        result = []
        if 'AB' in sgf_node or 'AW' in sgf_node:
            result.append(cls._make_setup(sgf_node))
        if 'B' in sgf_node:
            result.append(cls._make_move_or_pass(Color.black, sgf_node['B']))
        elif 'W' in sgf_node:
            result.append(cls._make_move_or_pass(Color.white, sgf_node['W']))
        return result

    @property
    def is_action(self):
        """True if this node should count toward the move count."""
        return self.is_move or self.is_pass

    def __eq__(self, other):
        if self.is_setup:
            if not other.is_setup:
                return False
            return (self.setup_coords_black == other.setup_coords_black
                    and self.setup_coords_white == other.setup_coords_white)

        if self.move_color != other.move_color:
            return False
        if self.is_pass and other.is_pass:
            return True
        if self.is_move != other.is_move:
            return False
        if self.is_move and (self.move_coord != other.move_coord):
            return False
        return True
