from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import unittest

from .. import go_rules
from ..go_rules import (
        Color, EmptyPointLibertiesException, IllegalMoveException, Stone,
        board_from, count_liberties, update_board_with_move
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

class TestBoardFrom(unittest.TestCase):

    def test_setup_stones_can_be_one_move_ahead(self):
        """Regression: need to process setup stones for move following the last
        one, eg. if there are setup stones before move 0 but no move 0 yet."""
        moves = []
        setup = {0: [Stone(white, 2, 3),
                     Stone(black, 3, 4)]}
        board = board_from(moves, setup)
        self.assertEqual(board[(2, 3)], white)
        self.assertEqual(board[(3, 4)], black)


    def test_simple_moves_and_setup(self):
        moves = [Stone(black, 0, 1),
                 Stone(white, 1, 2)]
        setup = {0: [Stone(white, 2, 3),
                     Stone(black, 3, 4)]}
        board = board_from(moves, setup)
        self.assertEqual(board[(0, 0)], empty)
        self.assertEqual(board[(0, 1)], black)
        self.assertEqual(board[(1, 2)], white)
        self.assertEqual(board[(2, 3)], white)
        self.assertEqual(board[(3, 4)], black)

    def test_exception_on_simple_illegal_move(self):
        moves = [Stone(black, 1, 1),
                 Stone(white, 1, 1)]
        with self.assertRaises(IllegalMoveException) as cm:
            board_from(moves, {})
        e = cm.exception
        self.assertEqual(e.move_no, 1)

class TestUpdateBoardWithMove(unittest.TestCase):

    def test_single_stone_capture(self):
        board = board_from_strings(['.b.',
                                    'bw.',
                                    '.b.'])
        update_board_with_move(board, Stone(black, 1, 2))
        self.assertEqual(board[(1, 1)], empty)

    def test_group_capture(self):
        board = board_from_strings(['.bb.',
                                    'bwwb',
                                    '.b..'])
        update_board_with_move(board, Stone(black, 2, 2))
        self.assertEqual(board[(1, 1)], empty)
        self.assertEqual(board[(1, 2)], empty)

class TestCountLiberties(unittest.TestCase):

    def test_exception_on_empty_point(self):
        board = board_from_strings(['.'])
        with self.assertRaises(EmptyPointLibertiesException):
            count_liberties(board, 0, 0)

    def test_groups_share_liberties(self):
        board = board_from_strings(['bb..',
                                    'bww.',
                                    '.b..'])
        top_left = count_liberties(board, 0, 1)
        self.assertEqual(top_left, 2)
        middle_white = count_liberties(board, 1, 1)
        self.assertEqual(middle_white, 3)
