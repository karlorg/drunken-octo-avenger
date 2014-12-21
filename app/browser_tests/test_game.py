from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)
from future.standard_library import install_aliases  # for urlopen
install_aliases()

from urllib.request import urlopen

from .base import SeleniumTest
from .. import main


class GameTest(SeleniumTest):

    def test_game_page(self):
        ## clear database; should only be necessary until we have multiple
        ## games
        main.db.drop_all()
        main.db.create_all()

        # start a new game
        self.browser.get(self.get_server_url() + '/newgame')

        # should see a page listing games
        def find_game_links():
            self.browser.find_element_by_partial_link_text('Game ')
        self.wait_for(find_game_links)
        # select the most recent game
        link = self.browser.find_elements_by_partial_link_text('Game ')[-1]
        link.click()

        ## just to make sure page is loaded
        self.wait_for(lambda: self.assertIn('Go', self.browser.title))

        # on the game page is a table with class 'goban'
        self.browser.find_element_by_css_selector('table.goban')
        ## should not raise

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
        except AttributeError:
            self.fail('no clickable board point found')

        # now on the board is one black stone and 19x19 - 1 empty points
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, 19*19-1)
        self.assertEqual(counts.black, 1)

        # user clicks another empty spot
        try:
            self.find_empty_point_to_click().click()
        except AttributeError:
            self.fail('no clickable board point found')

        # now one black stone, one white, rest empty
        counts = self.count_stones_and_points()
        self.assertEqual(counts.empty, 19*19-2)
        self.assertEqual(counts.black, 1)
        self.assertEqual(counts.white, 1)
