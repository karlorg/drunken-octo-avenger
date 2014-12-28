from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from selenium.common.exceptions import NoSuchElementException

from .base import SeleniumTest


class StartGamesTest(SeleniumTest):

    def test_start_games(self):
        SHINDOU_EMAIL = 'shindou@ki-in.jp'
        TOUYA_EMAIL = 'touya@ki-in.jp'
        OCHI_EMAIL = 'ochino1@ki-in.jp'
        # Shindou opens the front page and follows a link to create a new game
        self.create_login_session(SHINDOU_EMAIL)
        self.browser.get(self.get_server_url())

        def find_challenge():
            return self.browser.find_element_by_partial_link_text('Challenge')
        challenge_link = self.wait_for(find_challenge)
        challenge_link.click()
        # on the following form he enters Touya's email and clicks 'Send
        # challenge'

        def find_opponent_email():
            return self.browser.find_element_by_id('opponent_email')
        opponent_input = self.wait_for(find_opponent_email)
        self.careful_keys(opponent_input, TOUYA_EMAIL)
        self.browser.find_element_by_id('send_challenge').click()

        # TODO: instead of simply creating a game, Touya should receive a
        # challenge, which he has to accept

        # both players load the front page and see links to the same game

        def find_game_links():
            return self.browser.find_elements_by_partial_link_text('Game')
        # Shindou
        self.browser.get(self.get_server_url())
        shindous_game_link = self.wait_for(find_game_links)[-1]
        shindous_game_link_text = shindous_game_link.text
        shindous_game_link_target = shindous_game_link.get_attribute('href')
        # Touya
        self.create_login_session(TOUYA_EMAIL)
        self.browser.get(self.get_server_url())
        touyas_game_link = self.wait_for(find_game_links)[-1]
        touyas_game_link_text = touyas_game_link.text
        touyas_game_link_target = touyas_game_link.get_attribute('href')

        assert touyas_game_link_text == shindous_game_link_text
        assert shindous_game_link_target == touyas_game_link_target

        # a third user, Ochi, logs in.  The new game is not on his list.
        self.create_login_session(OCHI_EMAIL)
        self.browser.get(self.get_server_url())
        self.wait_for(find_game_links)
        try:
            self.browser.find_element_by_link_text(shindous_game_link_text)
        except NoSuchElementException:
            pass  ## we expect no such element to be found
        else:
            assert False
