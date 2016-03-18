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
            self.browser.find_element_by_id('login_form')
        except NoSuchElementException:
            pass  ## we expect no such element
        else:
            self.fail('found login link, should not exist')
        return logout_link