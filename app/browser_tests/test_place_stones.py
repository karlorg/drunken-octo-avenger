from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from .base import SeleniumTest


class PlaceStonesTest(SeleniumTest):

    def get_point(self, x, y):
        return self.browser.find_element_by_css_selector(
                ".col-{x}.row-{y}".format(x=str(x), y=str(y)))


    def test_place_stones(self):
        """Temporary: test the test helper facility for creating games with
        pre-set stones."""

        def find_your_turn_games():
            return self.browser.find_element_by_id('your_turn_games')

        ONE_EMAIL = 'player@one.com'
        TWO_EMAIL = 'playa@dos.es'
        ## create a couple of games
        self.clear_games_for_player(ONE_EMAIL)
        self.clear_games_for_player(TWO_EMAIL)
        self.create_game(
                black_email=ONE_EMAIL, white_email=TWO_EMAIL,
                stones=[
                    ".b.",
                    "bw.",
                    ".b."])

        # -- PLAYER ONE
        # player one logs in and gets the front page; should see a page listing
        # games
        self.create_login_session(ONE_EMAIL)
        self.browser.get(self.get_server_url())

        your_turn_games = self.wait_for(find_your_turn_games)
        # select the most recent game
        game_links = (
                your_turn_games.find_elements_by_partial_link_text('Game ')
        )
        latest_game_link = game_links[-1]
        latest_game_link.click()

        # on the game page is a table with class 'goban'
        def check_goban_exists():
            self.browser.find_element_by_css_selector('table.goban')
        self.wait_for(check_goban_exists)

        # the 3x3 block at top left is as we specified
        assert 'nostone' in self.get_point(0, 0).get_attribute('class')
        assert 'blackstone' in self.get_point(1, 0).get_attribute('class')
        assert 'nostone' in self.get_point(2, 0).get_attribute('class')
        assert 'blackstone' in self.get_point(0, 1).get_attribute('class')
        assert 'whitestone' in self.get_point(1, 1).get_attribute('class')
        assert 'nostone' in self.get_point(2, 1).get_attribute('class')
        assert 'nostone' in self.get_point(0, 2).get_attribute('class')
        assert 'blackstone' in self.get_point(1, 2).get_attribute('class')
        assert 'nostone' in self.get_point(2, 2).get_attribute('class')
