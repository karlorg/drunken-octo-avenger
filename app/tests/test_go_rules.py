from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import unittest

from ..go_rules import Color, Stone, board_from

empty = Color.empty
white = Color.white
black = Color.black

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
