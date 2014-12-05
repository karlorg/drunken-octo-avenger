from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

import os
from mock import ANY, Mock, patch
import unittest
import tempfile

from flask import render_template

import main


class TestWithDb(unittest.TestCase):

    def setUp(self):
        self.db_fd, main.app.config['DATABASE'] = tempfile.mkstemp()
        main.app.config['TESTING'] = True
        self.app = main.app.test_client()
        main.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(main.app.config['DATABASE'])


class TestGameIntegrated(TestWithDb):

    def test_uses_game_template(self):
        mock_render = Mock(wraps=render_template)
        with patch('main.render_template', mock_render):
            self.app.get('/game')
        args, _ = mock_render.call_args  ## _ would be keyword args
        assert args[0] == "game.html"


if __name__ == '__main__':
    unittest.main()
