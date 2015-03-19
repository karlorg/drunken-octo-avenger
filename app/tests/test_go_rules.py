from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import unittest

from .. import go_rules
from ..go_rules import (
        Color, EmptyPointGroupException, EmptyPointLibertiesException,
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
            if char is 'b':
                board.set_point(r, c, black)
            elif char is 'w':
                board.set_point(r, c, white)
    return board

class TestUpdateBoardWithMove(unittest.TestCase):

    def test_single_stone_capture(self):
        board = board_from_strings(['.b.',
                                    'bw.',
                                    '.b.'])
        board.update_with_move(black, 1, 2)
        self.assertEqual(board.get_point(1, 1), empty)

    def test_group_capture(self):
        board = board_from_strings(['.bb.',
                                    'bwwb',
                                    '.b..'])
        board.update_with_move(black, 2, 2)
        self.assertEqual(board.get_point(1, 1), empty)
        self.assertEqual(board.get_point(1, 2), empty)

    def test_group_capture_with_self_capture(self):
        # to avoid false passes depending on the order in which neighbours are
        # inspected for captures, do this twice rotated 180 degrees
        board = board_from_strings(['.bb..',
                                    'bwwb.',
                                    'b.wb.',
                                    'wbbw.',
                                    '.ww..'])
        board.update_with_move(white, 2, 1)
        self.assertEqual(board.get_point(1, 1), white)
        self.assertEqual(board.get_point(2, 2), white)
        self.assertEqual(board.get_point(3, 1), empty)
        self.assertEqual(board.get_point(3, 2), empty)

        board = board_from_strings(['.ww..',
                                    'wbbw.',
                                    'bw.b.',
                                    'bwwb.',
                                    '.bb..'])
        board.update_with_move(white, 2, 2)
        self.assertEqual(board.get_point(2, 1), white)
        self.assertEqual(board.get_point(3, 2), white)
        self.assertEqual(board.get_point(1, 1), empty)
        self.assertEqual(board.get_point(1, 2), empty)

    def test_exception_on_simple_illegal_move(self):
        board = board_from_strings(['..', '.b'])
        with self.assertRaises(IllegalMoveException) as cm:
            board.update_with_move(black, 1, 1, move_no=1)
        e = cm.exception
        self.assertEqual(e.move_no, 1)

    def test_playing_into_no_liberties_is_illegal(self):
        board = board_from_strings(['.w.',
                                    'w.w',
                                    '.w.'])
        with self.assertRaises(IllegalMoveException) as cm:
            board.update_with_move(black, 1, 1, move_no=1)
        e = cm.exception
        self.assertEqual(e.move_no, 1)
        # also, the board should not have changed
        self.assertEqual(board.get_point(1, 1), empty)

class TestCountLiberties(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(EmptyPointLibertiesException):
            board._count_liberties(0, 0)

    def test_groups_share_liberties(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = board._count_liberties(0, 1)
        self.assertEqual(top_left, 2)
        middle_white = board._count_liberties(1, 1)
        self.assertEqual(middle_white, 3)

class TestGetGroup(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(EmptyPointGroupException):
            board._get_group(0, 0)

    def test_identifies_sample_groups(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = board._get_group(0, 1)
        self.assertEqual(top_left, set([(0, 0), (0, 1), (1, 0)]))
        middle_white = board._get_group(1, 1)
        self.assertEqual(middle_white, set([(1, 1), (1, 2)]))
        bottom_black = board._get_group(2, 1)
        self.assertEqual(bottom_black, set([(2, 1)]))
