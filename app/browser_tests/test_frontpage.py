from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

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

    def test_persona_login(self):
        # loading the site's base url for the first time shows a button
        # to log in with Mozilla Persona
        self.browser.get(self.get_server_url())
        persona_button = self.browser.find_element_by_id('persona-login')
        # push the button and enter mockmyid login details
        persona_button.click()
        self.switch_to_new_window('Mozilla Persona')
        email_input = self.browser.find_element_by_id('authentication_email')
        ## mockmyid.com will approve any email in its domain
        self.careful_keys(email_input, 'test@mockmyid.com')
        self.browser.find_element_by_tag_name('button').click()
        # the Persona window closes
        self.switch_to_new_window('Go')
        # our email address is now shown on the page
        email_display = self.browser.find_element_by_class_name(
                'logged-in-user')
        assert 'test@mockmyid.com' in email_display.text()
