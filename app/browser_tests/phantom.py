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
import multiprocessing

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

class PhantomTest(object):

    def create_app(self):
        ## for some reason the SQL Alchemy URI is removed between setup in the
        ## main app and here
        app.config.from_object('config')
        # running the server in debug mode during testing fails for some reason
        app.config['DEBUG'] = False
        app.config['TESTING'] = True
        return app

    def run(self):
        self.app = self.create_app()

        # We need to create a context in order for extensions to catch up
        self._ctx = self.app.test_request_context()
        self._ctx.push()

        try:
            self._spawn_live_server()
            self.run_phantom_test()
        finally:
            self._post_teardown()
            self._terminate_live_server()

    def _spawn_live_server(self):
        self._process = None
        self.port = self.app.config.get('LIVESERVER_PORT', 5000)

        worker = lambda app, port: app.run(port=port, use_reloader=False)

        self._process = multiprocessing.Process(
            target=worker, args=(self.app, self.port)
        )

        self._process.start()

        # we must wait for the server to start listening with a maximum timeout of 5 seconds
        timeout = 5
        while timeout > 0:
            time.sleep(1)
            try:
                urlopen(self.get_server_url())
                timeout = 0
            except:
                timeout -= 1

    def _post_teardown(self):
        if getattr(self, '_ctx', None) is not None:
            self._ctx.pop()
            del self._ctx

    def _terminate_live_server(self):
        if self._process:
            self._process.terminate()

    def run_phantom_test(self):
        os.system("cake build")
        os.system("phantomjs app/static/tests/phantom.js")
        
if __name__ == "__main__":
    tester = PhantomTest()
    tester.run()
