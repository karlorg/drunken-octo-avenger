from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (  # noqa
        ascii, bytes, chr, dict, filter, hex, input, str, super, zip)
from future import standard_library
standard_library.install_aliases()

import time

from flask.ext.testing import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from collections import namedtuple

from ..main import app


class SeleniumTest(LiveServerTestCase):

    def create_app(self):
        ## for some reason the SQL Alchemy URI is removed between setup in the
        ## main app and here
        app.config.from_object('config')
        return app

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()
        time.sleep(0.5)

    # credit to Harry Percival for this wait_for
    # from his book, Test-Driven Development with Python
    def wait_for(self, function_with_assertion, timeout=5):
        start_time = time.time()
        while time.time() < start_time + timeout:
            try:
                return function_with_assertion()
            except (AssertionError, WebDriverException):
                time.sleep(0.1)
        # one more try, which will raise any errors if they are outstanding
        return function_with_assertion()

    def careful_keys(self, target, text):
        """Send keys in small groups.

        For some reason this gets around crazy send_keys behaviour on karl's
        system."""
        group_size = 10
        remaining = text
        while len(remaining) > 0:
            target.send_keys(remaining[:group_size])
            remaining = remaining[group_size:]

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
        return SeleniumTest.Count(empty=empty, black=black, white=white)

    def find_empty_point_to_click(self):
        """On a game board page, return a clickable board point.

        If no such point, raise AssertionError so that wait_for can retry this.
        """
        links = self.browser.find_elements_by_css_selector('table.goban a')
        target_link = None
        for link in links:
            if ('e.gif' in
                    link.find_element_by_tag_name('img').get_attribute('src')):
                target_link = link
                break
        else:
            raise AssertionError
        return target_link
