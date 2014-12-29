from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import time

from selenium.common.exceptions import NoSuchElementException

from .base import SeleniumTest


class FrontPageTest(SeleniumTest):

    def switch_to_new_window(self, text_in_title, timeout=5):
        retries = timeout / 0.5
        while retries > 0:
            for handle in self.browser.window_handles:
                self.browser.switch_to.window(handle)
                if text_in_title in self.browser.title:
                    return
            retries -= 1
            time.sleep(0.5)
        self.fail('could not find window')

    def confirm_logged_in_and_get_logout_link(
            self, expected_email='test@mockmyid.com'
    ):
        """Asserts logged in with expected_email and returns logout link."""
        # the page has a logout link
        def find_logout():
            return self.browser.find_element_by_id('logout')
        logout_link = self.wait_for(find_logout, timeout=15)
        # our email address is now shown on the page
        email_display = self.browser.find_element_by_class_name(
                'logged_in_user')
        assert expected_email in email_display.text
        # and there is now no login link
        try:
            self.browser.find_element_by_id('persona_login')
        except NoSuchElementException:
            pass  ## we expect no such element
        else:
            self.fail('found login link, should not exist')
        return logout_link

    def test_persona_login(self):
        ## we won't use the fake login session creator for this test; we want
        ## to test the actual login procedure.

        # loading the site's base url for the first time shows a button
        # to log in with Mozilla Persona
        self.browser.get(self.get_server_url())
        persona_button = self.browser.find_element_by_id('persona_login')
        # push the button and enter mockmyid login details
        persona_button.click()
        self.switch_to_new_window('Mozilla Persona')
        email_input = self.browser.find_element_by_id('authentication_email')
        ## mockmyid.com will approve any email in its domain
        self.careful_keys(email_input, 'test@mockmyid.com')
        self.browser.find_element_by_tag_name('button').click()
        # the Persona window closes
        self.switch_to_new_window('Go')
        # and we're logged in
        plogout_link = self.confirm_logged_in_and_get_logout_link()

        # we try another page, we're still logged in there
        # TODO: once we have a non-frontpage to browse to, go there
        self.browser.get(self.get_server_url() + "/")
        plogout_link = self.confirm_logged_in_and_get_logout_link()

        # now we log out again
        plogout_link.click()
        # we're back to a login link...

        def find_login():
            return self.browser.find_element_by_id('persona_login')
        persona_button = self.wait_for(find_login, timeout=15)
        # and no email display...
        try:
            email_display = self.browser.find_element_by_class_name(
                    'logged_in_user')
        except NoSuchElementException:
            pass
        else:
            assert 'test@mockmyid.com' not in email_display.text
        # and no logout link
        try:
            self.browser.find_element_by_id('logout')
        except NoSuchElementException:
            pass  ## we expect no such element
        else:
            self.fail('found logout link, should not exist')
