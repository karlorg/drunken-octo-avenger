from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()

import os
from subprocess import Popen
import time
import unittest

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

PORT_NO = 5000


class SeleniumTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Starting test server...")
        os.chdir(os.path.dirname(os.path.realpath(__file__)) + '/..')
        cls.server_process = Popen(
            ['python', 'main.py'],
            #stdout=DEVNULL, stderr=DEVNULL
        )
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.server_process.terminate()

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.server_url = 'localhost:' + str(PORT_NO)

    def tearDown(self):
        self.browser.quit()

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
