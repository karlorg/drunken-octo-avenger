from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import unittest

from .. import main

class TestServerPlayer(unittest.TestCase):
    def assert_status_list_lengths(self, email, your_turns, not_your_turns):
        main.get_player_games(email)
        your_turn_games, not_your_turn_games = main.get_status_lists(email)
        self.assertEqual(len(your_turn_games), your_turns)
        self.assertEqual(len(not_your_turn_games), not_your_turns)
    def test_server_player(self):
        test_player_email = "serverplayer@localhost"
        test_opponent_email = "serverplayermock@localhost"

        main.clear_games_for_player_internal(test_player_email)
        main.clear_games_for_player_internal(test_opponent_email)
        main.create_game_internal(test_player_email, test_opponent_email)
        self.assert_status_list_lengths(test_player_email, 1, 0)
        main.server_player_act(test_player_email)
        self.assert_status_list_lengths(test_player_email, 0, 1)
