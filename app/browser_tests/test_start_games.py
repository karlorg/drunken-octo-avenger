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
        challenge_link = self.wait_for(
                shindou.find_element_by_link_text('Challenge')
        )
        challenge_link.click()
