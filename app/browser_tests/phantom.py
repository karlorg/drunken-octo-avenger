from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)
from future import standard_library
standard_library.install_aliases()

import logging
import multiprocessing
import os
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen

from ..main import app

# importing main enables logging, we switch it off again here to prevent
# selenium debug lines from flooding the test output
logging.disable(logging.CRITICAL)

class PhantomTest(unittest.TestCase):

    def create_app(self):
        ## for some reason the SQL Alchemy URI is removed between setup in the
        ## main app and here
        app.config.from_object('config')
        # running the server in debug mode during testing fails for some reason
        app.config['DEBUG'] = False
        app.config['TESTING'] = True
        return app

    def get_server_url(self):
        return self._server_url

    def test_run(self):
        self.app = self.create_app()
        # We need to create a context in order for extensions to catch up
        self._ctx = self.app.test_request_context()
        self._ctx.push()
        # now run the server and tests
        try:
            self._spawn_live_server()
            self.run_phantom_test()
        finally:
            self._post_teardown()
            self._terminate_live_server()

    def _spawn_live_server(self):
        self._process = None
        self.port = self.app.config.get('LIVESERVER_PORT', 5000)
        self._server_url = 'http://localhost:{}'.format(self.port)

        worker = lambda app, port: app.run(port=port, use_reloader=False)

        self._process = multiprocessing.Process(
            target=worker, args=(self.app, self.port)
        )
        self._process.start()

        # wait a few seconds for the server to start listening
        timeout = 5
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            try:
                urlopen(self.get_server_url())
            except URLError:
                pass
            else:
                break

    def _post_teardown(self):
        if getattr(self, '_ctx', None) is not None:
            self._ctx.pop()
            del self._ctx

    def _terminate_live_server(self):
        if self._process:
            self._process.terminate()

    def run_phantom_test(self):
        os.system("cake build")
        os.system("./node_modules/.bin/casperjs test"
                  " app/static/tests/browser.js")

if __name__ == "__main__":
    tester = PhantomTest()
    tester.run()
