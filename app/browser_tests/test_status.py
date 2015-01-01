from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from .base import SeleniumTest


class StatusTest(SeleniumTest):

    def test_status_page_game_listings(self):
        """Test appearance of games in appropriate lists on status page."""

        ONE_EMAIL = 'playa@uno.es'
        TWO_EMAIL = 'player@two.co.uk'
        THREE_EMAIL = 'plagxo@tri.eo'
        # clear games for these players, and create new games
        self.clear_games_for_player(ONE_EMAIL)
        self.clear_games_for_player(TWO_EMAIL)
        self.clear_games_for_player(THREE_EMAIL)
        self.create_game(black_email=ONE_EMAIL, white_email=TWO_EMAIL)
        self.create_game(black_email=ONE_EMAIL, white_email=THREE_EMAIL)
        self.create_game(black_email=THREE_EMAIL, white_email=ONE_EMAIL)

        def find_your_turn_games():
            return (
                    self.browser.find_element_by_id('your_turn_games')
                    .find_elements_by_partial_link_text('Game ')
            )

        def find_other_games():
            return (
                    self.browser.find_element_by_id('not_your_turn_games')
                    .find_elements_by_partial_link_text('Game ')
            )

        def assert_on_num_games(player_email, your_turn, other):
            self.create_login_session(player_email)
            self.browser.get(self.get_server_url())
            your_turn_games = self.wait_for(find_your_turn_games)
            other_games = find_other_games()
            self.assertEqual(len(your_turn_games), your_turn)
            self.assertEqual(len(other_games), other)

        # player one has two games in which it's her turn, and one other
        assert_on_num_games(ONE_EMAIL, 2, 1)
        # player two has no games in which it's her turn, and one other
        assert_on_num_games(TWO_EMAIL, 0, 1)
        # player three has one game in which it's her turn, and one other
        assert_on_num_games(THREE_EMAIL, 1, 1)
