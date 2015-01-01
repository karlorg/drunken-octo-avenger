from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)
from future.standard_library import install_aliases  # for urlopen
install_aliases()

from urllib.request import urlopen

from .base import SeleniumTest


class GameTest(SeleniumTest):

    def test_game_page(self):
        """Test game display and placing stones through the web interface."""

        ONE_EMAIL = 'player@one.com'
        TWO_EMAIL = 'playa@dos.es'
        ## create a couple of games
        self.clear_games_for_player(ONE_EMAIL)
        self.clear_games_for_player(TWO_EMAIL)
        self.create_game(black_email=ONE_EMAIL, white_email=TWO_EMAIL)
        self.create_game(black_email=ONE_EMAIL, white_email=TWO_EMAIL)

        # -- PLAYER ONE
        # player one logs in and gets the front page; should see a page listing
        # games
        self.create_login_session(ONE_EMAIL)
        self.browser.get(self.get_server_url())

        def find_your_turn_games():
            return self.browser.find_element_by_id('your_turn_games')
        your_turn_games = self.wait_for(find_your_turn_games)
        # select the most recent game
        latest_game_link = (
                your_turn_games.find_elements_by_partial_link_text('Game ')[-1]
        )
        latest_game_text = latest_game_link.text
        latest_game_link.click()

        # on the game page is a table with class 'goban'
        def check_goban_exists():
            self.browser.find_element_by_css_selector('table.goban')
        self.wait_for(check_goban_exists)

        # on the game page are 19x19 imgs representing board points/stones
        empty = self.count_stones_and_points().empty
        self.assertEqual(19*19, empty, "did not find 19x19 board imgs")

        ## check one of those images can be loaded
        img = self.browser.find_element_by_css_selector('table.goban a img')
        response = urlopen(img.get_attribute('src'))
        self.assertEqual(response.getcode(), 200)
        try:
            self.assertNotIn(
                'Exception', response.read().decode(),
                'image load returns exception'
            )
        except UnicodeDecodeError:
            pass  ## fine, we got image data

        # user clicks an empty spot, which is a link
        try:
            self.find_empty_point_to_click().click()
        except (AssertionError, AttributeError):
            self.fail('no clickable board point found')

        # now on the board is one black stone and 19x19 - 1 empty points
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, 19*19-1)
        self.assertEqual(counts.black, 1)

        # since it's not player one's turn any more, there should be no
        # clickable links
        try:
            self.find_empty_point_to_click()
        except AssertionError:
            pass
        else:
            self.fail("clickable board links found off-turn")

        # -- PLAYER TWO
        # now the white player logs in and visits the same game
        self.create_login_session(TWO_EMAIL)
        self.browser.get(self.get_server_url())
        self.browser.find_element_by_link_text(latest_game_text).click()

        # user clicks another empty spot
        try:
            self.find_empty_point_to_click().click()
        except (AssertionError, AttributeError):
            self.fail('no clickable board point found')

        # now one black stone, one white, rest empty
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, 19*19-2)
        self.assertEqual(counts.black, 1)
        self.assertEqual(counts.white, 1)

        # reload front page and get the other game
        self.browser.get(self.get_server_url())
        self.wait_for(find_your_turn_games)
        # select the most recent game
        link = self.browser.find_elements_by_partial_link_text('Game ')[-2]
        link.click()

        # we should be back to an empty board
        self.wait_for(check_goban_exists)
        empty = self.count_stones_and_points().empty
        self.assertEqual(19*19, empty, "second board not empty")

        # with no clickable links, since we're white in this game
        try:
            self.find_empty_point_to_click()
        except AssertionError:
            pass
        else:
            self.fail("clickable board links found off-turn")
