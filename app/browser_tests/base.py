from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)
from future import standard_library
standard_library.install_aliases()

import time

from flask.ext.testing import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from collections import namedtuple

from ..main import app, db, Game, Move


class SeleniumTest(LiveServerTestCase):

    def create_app(self):
        ## for some reason the SQL Alchemy URI is removed between setup in the
        ## main app and here
        app.config.from_object('config')
        return app

    def setUp(self):
        self.active_browsers = []
        self.browser = self.get_new_browser()

    def tearDown(self):
        for browser in self.active_browsers:
            browser.quit()
        time.sleep(0.5)

    def get_new_browser(self):
        """Return a new browser object that will be cleaned up on teardown"""
        browser = webdriver.Firefox()
        self.active_browsers.append(browser)
        return browser

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
        """Set a cookie for a pre-authenticated login session."""
        interface = app.session_interface
        session = interface.session_class()
        session['email'] = email
        # the following process for creating the cookie value is copied from
        # the Flask source; if the cookies created by this method stop
        # working, see if a Flask update has changed the cookie creation
        # procedure in flask/sessions.py -> SecureCookieSessionInterface
        # (currently the default) -> save_session
        cookie_value = (
                interface.get_signing_serializer(app).dumps(dict(session))
        )
        # to set a cookie we need to load a page; 404 loads fastest
        self.browser.get(self.get_server_url() + "/404_no_such_url")
        self.browser.add_cookie(dict(
            name=app.session_cookie_name,
            value=cookie_value,
            path=interface.get_cookie_path(app),
        ))

    def create_game(self, black_email, white_email):
        """Create a custom game in the database without using the web.

        This is separated into a method primarily to ease making this a remote
        command when we get to testing against a staging server."""
        game = Game()
        game.black = black_email
        game.white = white_email
        db.session.add(game)
        db.session.commit()

    def clear_games_for_player(self, email):
        """Clear all of `email`'s games from the database.

        This is separated into a method primarily to ease making this a remote
        command when we get to testing against a staging server."""
        games_as_black = Game.query.filter(Game.black == email).all()
        games_as_white = Game.query.filter(Game.white == email).all()
        games = games_as_black + games_as_white
        moves = Move.query.filter(Move.game in games).all()
        for move in moves:
            db.session.delete(move)
        for game in games:
            db.session.delete(game)
        db.session.commit()

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
