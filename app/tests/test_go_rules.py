from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import unittest

from .. import go_rules
from ..go_rules import (
        Color, Coord, EmptyPointGroupException, EmptyPointLibertiesException,
        IllegalMoveException,
)

empty = Color.empty
white = Color.white
black = Color.black

def board_from_strings(rows):
    """Convenience function for setting up positions easily"""
    board = go_rules.Board(len(rows[0]))
    for r, row in enumerate(rows):
        for c, char in enumerate(row):
            if char == 'b':
                board[Coord(c, r)] = black
            elif char == 'w':
                board[Coord(c, r)] = white
    return board

class MockMove(object):
    def __init__(self, color, row, column, move_no=None):
        self.color = color
        self.row = row
        self.column = column
        self.move_no = move_no

class TestUpdateBoardWithMove(unittest.TestCase):

    def test_place_stone(self):
        board = board_from_strings(['..', '..'])
        board.update_with_move(MockMove(black, 0, 0))
        self.assertEqual(board[Coord(0, 0)], black)

    def test_single_stone_capture(self):
        board = board_from_strings(['.b.',
                                    'bw.',
                                    '.b.'])
        board.update_with_move(MockMove(black, 1, 2))
        self.assertEqual(board[Coord(1, 1)], empty)

    def test_regression_single_capture_with_non_identity(self):
        # check for case where color of stone to be captured is equal to, but
        # not identical to (`==`, not `is`), the enemy color
        board = board_from_strings(['.b.',
                                    'bw.',
                                    '.b.'])
        board[Coord(1, 1)] = int(Color.white)
        board.update_with_move(MockMove(black, 1, 2))
        self.assertEqual(board[Coord(1, 1)], empty)

    def test_group_capture(self):
        board = board_from_strings(['.bb.',
                                    'bwwb',
                                    '.b..'])
        board.update_with_move(MockMove(black, 2, 2))
        self.assertEqual(board[Coord(1, 1)], empty)
        self.assertEqual(board[Coord(x=2, y=1)], empty)

    def test_group_capture_with_self_capture(self):
        # to avoid false passes depending on the order in which neighbours are
        # inspected for captures, do this twice rotated 180 degrees
        board = board_from_strings(['.bb..',
                                    'bwwb.',
                                    'b.wb.',
                                    'wbbw.',
                                    '.ww..'])
        board.update_with_move(MockMove(white, 2, 1))
        self.assertEqual(board[Coord(x=1, y=1)], white)
        self.assertEqual(board[Coord(x=2, y=2)], white)
        self.assertEqual(board[Coord(x=1, y=3)], empty)
        self.assertEqual(board[Coord(x=2, y=3)], empty)

        board = board_from_strings(['.ww..',
                                    'wbbw.',
                                    'bw.b.',
                                    'bwwb.',
                                    '.bb..'])
        board.update_with_move(MockMove(white, 2, 2))
        self.assertEqual(board[Coord(x=1, y=2)], white)
        self.assertEqual(board[Coord(x=2, y=3)], white)
        self.assertEqual(board[Coord(x=1, y=1)], empty)
        self.assertEqual(board[Coord(x=2, y=1)], empty)

    def test_exception_on_simple_illegal_move(self):
        board = board_from_strings(['..', '.b'])
        with self.assertRaises(IllegalMoveException) as cm:
            board.update_with_move(MockMove(black, 1, 1, move_no=1))
        e = cm.exception
        self.assertEqual(e.move_no, 1)

    def test_playing_into_no_liberties_is_illegal(self):
        board = board_from_strings(['.w.',
                                    'w.w',
                                    '.w.'])
        with self.assertRaises(IllegalMoveException) as cm:
            board.update_with_move(MockMove(black, 1, 1, move_no=1))
        e = cm.exception
        self.assertEqual(e.move_no, 1)
        # also, the board should not have changed
        self.assertEqual(board[Coord(1, 1)], empty)

class TestCountLiberties(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(EmptyPointLibertiesException):
            board._count_liberties(Coord(0, 0))

    def test_groups_share_liberties(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = board._count_liberties(Coord(0, 1))
        self.assertEqual(top_left, 2)
        middle_white = board._count_liberties(Coord(1, 1))
        self.assertEqual(middle_white, 3)

class TestGetGroup(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(EmptyPointGroupException):
            board._get_group(Coord(0, 0))

    def test_identifies_sample_groups(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = board._get_group(Coord(1, 0))
        self.assertEqual(top_left, set([Coord(0, 0), Coord(1, 0), Coord(0, 1)]))
        middle_white = board._get_group(Coord(1, 1))
        self.assertEqual(middle_white, set([Coord(1, 1), Coord(x=2, y=1)]))
        bottom_black = board._get_group(Coord(x=1, y=2))
        self.assertEqual(bottom_black, set([Coord(x=1, y=2)]))
