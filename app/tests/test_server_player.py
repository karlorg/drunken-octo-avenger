from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import unittest

from .. import main

class TestServerPlayer(unittest.TestCase):
    def test_server_player(self):
        test_player_email = "serverplayer@localhost"
        test_opponent_email = "serverplayermock@localhost"

        main.clear_games_for_player_internal(test_player_email)
        main.create_game_internal(test_player_email, test_opponent_email)
        number_games = main.server_player_act(test_player_email)
        self.assertEqual(number_games, 1)
