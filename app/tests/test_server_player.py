from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import unittest

from .. import main

class TestServerPlayer(unittest.TestCase):
    def test_server_player(self):
        number_games = main.server_player_act()
        self.assertEqual(number_games, 0)
