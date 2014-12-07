from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)
from future.standard_library import install_aliases  # for urlopen
install_aliases()

from collections import namedtuple
import unittest
from urllib.request import urlopen

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .base import SeleniumTest


class GameTest(SeleniumTest):

    Count = namedtuple('Count', ['white', 'black', 'empty'])
    def count_stones_and_points(self):
        imgs = self.browser.find_elements_by_tag_name('img')
        empty = 0
        black = 0
        white = 0
        for img in imgs:
            if 'e.gif' in img.get_attribute('src'):
                empty += 1
            elif 'b.gif' in img.get_attribute('src'):
                black += 1
            elif 'w.gif' in img.get_attribute('src'):
                white += 1
        return GameTest.Count(empty=empty, black=black, white=white)


    def find_empty_point_to_click(self):
        links = self.browser.find_elements_by_css_selector('table.goban a')
        target_link = None
        for link in links:
            if ('e.gif' in
                    link.find_element_by_tag_name('img').get_attribute('src')):
                target_link = link
                break
        return target_link

    def test_game_page(self):
        self.browser.get(self.get_server_url() + '/game')
        ## just to make sure page is loaded
        self.wait_for(lambda: self.assertIn('Go', self.browser.title))

        # on the game page is a table with class 'goban'
        table = self.browser.find_element_by_css_selector('table.goban')
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


if __name__ == '__main__':
    unittest.main()
