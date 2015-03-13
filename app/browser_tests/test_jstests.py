from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from selenium.common.exceptions import WebDriverException

from .base import SeleniumTest


class JSTestsTest(SeleniumTest):

    def test_js_tests(self):
        """Run JS tests and ensure they pass."""
        self.browser.get(
                self.get_server_url() + "/static/tests/tests.html")
        try:
            self.wait_for(
                    lambda:
                    self.browser.find_element_by_css_selector('.qunit-pass'))
            # if that raised no exception, we're done
            return
        except WebDriverException:
            try:
                self.browser.find_element_by_css_selector('.qunit-fail')
            except Exception:
                assert False, "couldn't detect pass or fail for JS tests"
            else:
                assert False, "JS tests failed"
