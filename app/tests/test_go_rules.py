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
        _count_liberties, _get_group, update_board_with_move
)

empty = Color.empty
white = Color.white
black = Color.black

def board_from_strings(rows):
    """Convenience function for setting up positions easily"""
    board = go_rules.empty_board(len(rows[0]))
    for r, row in enumerate(rows):
        for c, char in enumerate(row):
            if char is 'b':
                board[(r, c)] = black
            elif char is 'w':
                board[(r, c)] = white
    return board

class TestUpdateBoardWithMove(unittest.TestCase):

    def test_single_stone_capture(self):
        board = board_from_strings(['.b.',
                                    'bw.',
                                    '.b.'])
        update_board_with_move(board, black, 1, 2)
        self.assertEqual(board[(1, 1)], empty)

    def test_group_capture(self):
        board = board_from_strings(['.bb.',
                                    'bwwb',
                                    '.b..'])
        update_board_with_move(board, black, 2, 2)
        self.assertEqual(board[(1, 1)], empty)
        self.assertEqual(board[(1, 2)], empty)

    def test_group_capture_with_self_atari(self):
        # to avoid false passes depending on the order in which neighbours are
        # inspected for captures, do this twice rotated 180 degrees
        board = board_from_strings(['.bb..',
                                    'bwwb.',
                                    'b.wb.',
                                    'wbbw.',
                                    '.ww..'])
        update_board_with_move(board, white, 2, 1)
        self.assertEqual(board[(1, 1)], white)
        self.assertEqual(board[(2, 2)], white)
        self.assertEqual(board[(3, 1)], empty)
        self.assertEqual(board[(3, 2)], empty)

        board = board_from_strings(['.ww..',
                                    'wbbw.',
                                    'bw.b.',
                                    'bwwb.',
                                    '.bb..'])
        update_board_with_move(board, white, 2, 2)
        self.assertEqual(board[(2, 1)], white)
        self.assertEqual(board[(3, 2)], white)
        self.assertEqual(board[(1, 1)], empty)
        self.assertEqual(board[(1, 2)], empty)

    def test_exception_on_simple_illegal_move(self):
        board = board_from_strings(['..', '.b'])
        with self.assertRaises(IllegalMoveException) as cm:
            update_board_with_move(board, black, 1, 1, move_no=1)
        e = cm.exception
        self.assertEqual(e.move_no, 1)

class TestCountLiberties(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(EmptyPointLibertiesException):
            _count_liberties(board, 0, 0)

    def test_groups_share_liberties(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = _count_liberties(board, 0, 1)
        self.assertEqual(top_left, 2)
        middle_white = _count_liberties(board, 1, 1)
        self.assertEqual(middle_white, 3)

class TestGetGroup(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(EmptyPointGroupException):
            _get_group(board, 0, 0)

    def test_identifies_sample_groups(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = _get_group(board, 0, 1)
        self.assertEqual(top_left, set([(0, 0), (0, 1), (1, 0)]))
        middle_white = _get_group(board, 1, 1)
        self.assertEqual(middle_white, set([(1, 1), (1, 2)]))
        bottom_black = _get_group(board, 2, 1)
        self.assertEqual(bottom_black, set([(2, 1)]))
