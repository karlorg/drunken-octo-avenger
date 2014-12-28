from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from functools import partial

from .base import SeleniumTest


class StartGamesTest(SeleniumTest):

    def test_start_games(self):
        # two users, Shindou and Touya, are both logged in on their browsers
        shindou = self.browser
        touya = self.get_new_browser()
        self.create_login_session('shindou@ki-in.jp', browser=shindou)
        self.create_login_session('touyajr@ki-in.jp', browser=touya)
        # Shindou opens the front page and follows a link to create a new game
        shindou.get(self.get_server_url())

        def find_challenge():
            return shindou.find_element_by_partial_link_text('Challenge')
        challenge_link = self.wait_for(find_challenge)
        challenge_link.click()
        # on the following form he enters Touya's email and clicks 'Send
        # challenge'

        def find_opponent_email():
            return shindou.find_element_by_id('opponent_email')
        opponent_input = self.wait_for(find_opponent_email)
        self.careful_keys(opponent_input, 'touyajr@ki-in.jp')
        shindou.find_element_by_id('send_challenge').click()

        # TODO: instead of simply creating a game, Touya should receive a
        # challenge, which he has to accept

        # both players load the front page and see links to the same game

        def find_game_link(browser):
            return browser.find_element_by_partial_link_text('Game')
        touya.get(self.get_server_url())
        touyas_game_link = self.wait_for(partial(find_game_link, touya))
        shindou.get(self.get_server_url())
        shindous_game_link = self.wait_for(partial(find_game_link, shindou))
        assert touyas_game_link.text == shindous_game_link.text
        assert (
                touyas_game_link.get_attribute('href')
                == shindous_game_link.get_attribute('href')
        )
