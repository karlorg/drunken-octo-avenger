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

    def assert_no_clickable_board_points(self):
        try:
            self.find_empty_point_to_click()
        except (AssertionError, AttributeError):
            return
        self.fail('clickable board points found off-turn')

    def assert_and_click_clickable_board_point(self):
        try:
            self.find_empty_point_to_click().click()
        except (AssertionError, AttributeError):
            self.fail('no clickable board point found')

    def get_point(self, x, y):
        return self.browser.find_element_by_css_selector(
                ".col-{x}.row-{y}".format(x=str(x), y=str(y)))

    def find_confirm_button(self):
        """On a game board page, return the Confirm button.

        If the button is not available, raise AssertionError so that `wait_for`
        can retry this.
        """
        buttons = self.browser.find_elements_by_tag_name('button')
        for button in buttons:
            if 'Confirm' in button.text:
                return button
        else:
            raise AssertionError

    def assert_and_get_confirm_button(self):
        try:
            button = self.find_confirm_button()
        except (AssertionError, AttributeError):
            self.fail('Confirm button not found')
        return button


    def test_game_page(self):
        """Test game display and placing stones through the web interface."""

        def find_your_turn_games():
            return self.browser.find_element_by_id('your_turn_games')

        ONE_EMAIL = 'player@one.com'
        TWO_EMAIL = 'playa@dos.es'
        ## create a couple of games
        self.clear_games_for_player(ONE_EMAIL)
        self.clear_games_for_player(TWO_EMAIL)
        self.create_game(black_email=ONE_EMAIL, white_email=TWO_EMAIL)
        self.create_game(
                black_email=ONE_EMAIL, white_email=TWO_EMAIL, stones=[
                    'wwb',
                    'b..'
                ])
        initial_empty_count = 19*19-4

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
        latest_game_text = latest_game_link.text
        other_game_text = game_links[-2].text
        latest_game_link.click()

        # on the game page is a table with class 'goban'
        def check_goban_exists():
            self.browser.find_element_by_css_selector('table.goban')
        self.wait_for(check_goban_exists)

        # on the game page are 19x19 imgs representing board points/stones
        # counts depend on the stone setup above
        empty = self.count_stones_and_points().empty
        self.assertEqual(
                initial_empty_count, empty,
                "did not find expected # of empty imgs")

        ## check one of those images can be loaded
        img = self.browser.find_element_by_css_selector('table.goban img')
        response = urlopen(img.get_attribute('src'))
        self.assertEqual(response.getcode(), 200)
        try:
            self.assertNotIn(
                'Exception', response.read().decode(),
                'image load returns exception'
            )
        except UnicodeDecodeError:
            pass  ## fine, we got image data

        # no (usable) confirm button appears yet
        try:
            button = self.assert_and_get_confirm_button()
        except AssertionError:
            pass
        else:
            if not button.get_attribute('disabled'):
                self.fail("Confirm button clickable before stone placed")

        # user clicks an empty point; the board updates to show a stone there
        # and other stones captured
        self.get_point(1, 1).click()
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, initial_empty_count+1)
        self.assertEqual(counts.white, 0)
        self.assertEqual(counts.black, 3)
        # a Confirm button is now available
        self.assert_and_get_confirm_button()
        # user clicks an empty spot, which is a link
        self.get_point(15, 3).click()
        # now on the board is one more black stone and one less empty point
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, initial_empty_count-1)
        self.assertEqual(counts.white, 2)
        self.assertEqual(counts.black, 3)
        # we click the capturing point again, as we'll want to see what happens
        # when we confirm a capturing move.
        self.get_point(1, 1).click()
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, initial_empty_count+1)
        self.assertEqual(counts.white, 0)
        self.assertEqual(counts.black, 3)
        # we confirm this new move
        self.assert_and_get_confirm_button().click()
        # now we're taken back to the status page
        self.wait_for(find_your_turn_games)

        # -- PLAYER TWO
        # now the white player logs in and visits the same game
        self.create_login_session(TWO_EMAIL)
        self.browser.get(self.get_server_url())
        self.browser.find_element_by_link_text(latest_game_text).click()

        # the captured stones are still captured
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, initial_empty_count+1)
        self.assertEqual(counts.white, 0)
        self.assertEqual(counts.black, 3)
        # clicking a point with a black stone does nothing
        self.get_point(1, 1).click()
        # still one black stone, no white, rest empty
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, initial_empty_count+1)
        self.assertEqual(counts.white, 0)
        self.assertEqual(counts.black, 3)

        # user clicks an empty spot
        self.get_point(3, 3).click()
        # now one black stone, one white, rest empty
        counts = self.count_stones_and_points()
        self.assertEqual(counts.white, 1)

        # confirm move
        self.assert_and_get_confirm_button().click()

        # reload front page and get the other game
        self.browser.get(self.get_server_url())
        self.wait_for(find_your_turn_games)
        # select the most recent game
        link = self.browser.find_element_by_link_text(other_game_text)
        link.click()

        # we should be back to an empty board
        self.wait_for(check_goban_exists)
        empty = self.count_stones_and_points().empty
        self.assertEqual(19*19, empty, "second board not empty")

        # with no clickable links, since we're white in this game
        self.assert_no_clickable_board_points()
