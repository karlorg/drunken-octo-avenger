from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)
from future import standard_library
standard_library.install_aliases()

import logging
import os
import sys
import time
import unittest

from flask.ext.testing import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from collections import namedtuple

from ..main import app
import manage
from . import server_tools

# importing main enables logging, we switch it off again here to prevent
# selenium debug lines from flooding the test output
logging.disable(logging.CRITICAL)

class SeleniumTest(LiveServerTestCase):

    def __call__(self, result=None):
        """LiveServerTestCase sets up the server in its __call__ method

        Override to allow testing against remote servers using the LIVESERVER
        environment variable.
        """
        try:
            server = os.environ['LIVESERVER']
        except KeyError:
            server = ''
        if server != '':
            self.server_host = server
            self.server_url = 'http://' + server
            self.against_remote = True
            # if you change this safety guard of requiring 'staging' in the
            # hostname, please try to replace it with something that still
            # prevents testing against the live site
            if 'staging' in server:
                # skipping LiveServerTestCase, which would create the testing
                # app, and going straight to unittest to run the tests
                unittest.TestCase.__call__(self, result)
                # skip usual setup
                return
            else:
                print("'staging' not found in host name, aborting")
                sys.exit(1)
        else:
            self.server_host = None
            self.server_url = None
            self.against_remote = False
            # super().__call__ runs the tests, so we need to set server_url
            # first
            super().__call__(result)

    def get_server_url(self):
        """Return the url of the test server

        Overrides the method from flask-testing
        """
        if self.server_url is not None:
            return self.server_url
        else:
            return super(SeleniumTest, self).get_server_url()

    def create_app(self):
        ## for some reason the SQL Alchemy URI is removed between setup in the
        ## main app and here
        app.config.from_object('config')
        # running the server in debug mode during testing fails for some reason
        app.config['DEBUG'] = False
        app.config['TESTING'] = True
        return app

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    # credit to Harry Percival for this wait_for
    # from his book, Test-Driven Development with Python
    def wait_for(self, function_with_assertion, timeout=5):
        """Keep trying `function_with_assertion` for `timeout` seconds."""
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

    def create_login_session(self, email):
        """Set a cookie for a pre-authenticated login session.

        If running locally, simply call the internal login session creator.  If
        running against a remote server, use the server tools to create the
        session remotely.
        """
        if self.against_remote:
            cookie = server_tools.create_session_on_server(
                    self.server_host, email)
        else:
            cookie = manage.create_login_session_internal(email)
        # to set a cookie we need to load a page; 404 loads fastest
        self.browser.get(self.get_server_url() + "/404_no_such_url")
        self.browser.add_cookie(dict(
            name=cookie['name'],
            value=cookie['value'],
            path=cookie['path'],
        ))

    def create_game(self, black_email, white_email, stones=None):
        """Create a custom game in the database without using the web.

        Go via fabric if testing against a remote server.
        """
        if self.against_remote:
            server_tools.create_game_on_server(
                    self.server_host, black_email, white_email, stones)
        else:
            manage.create_game_internal(black_email, white_email, stones)

    def clear_games_for_player(self, email):
        """Clear all of `email`'s games from the database.

        Go via fabric if testing against a remote server.
        """
        if self.against_remote:
            server_tools.clear_games_for_player_on_server(
                    self.server_host, email)
        else:
            manage.clear_games_for_player_internal(email)

    Count = namedtuple('Count', ['white', 'black', 'empty'])
    """Return type for count_stones_and_points"""

    def count_stones_and_points(self):
        """Count the images in the page for empty points and stones."""
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
