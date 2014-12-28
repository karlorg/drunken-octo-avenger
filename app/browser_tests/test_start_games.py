from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

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
