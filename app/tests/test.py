from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

import os
from mock import ANY, Mock, patch
import unittest
import tempfile

from flask import render_template

from app import main


class TestWithTestingApp(unittest.TestCase):

    def setUp(self):
        main.app.config['TESTING'] = True
        self.app = main.app.test_client()

class TestWithDb(TestWithTestingApp):

    def setUp(self):
        super().setUp()
        self.db_fd, main.app.config['DATABASE'] = tempfile.mkstemp()
        main.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(main.app.config['DATABASE'])
        super().tearDown()


class TestGameIntegrated(TestWithTestingApp):

    def test_passes_correct_goban_format_to_template(self):
        mock_render = Mock(wraps=render_template)
        with patch('app.main.render_template', mock_render):
            self.app.get('/game')
        args, kwargs = mock_render.call_args
        assert args[0] == "game.html"

        goban = kwargs['goban']
        assert goban[0][0] == str(goban[0][0])
        assert kwargs['move_no'] == int(kwargs['move_no'])


class TestGameUnit(TestWithTestingApp):

    pass


if __name__ == '__main__':
    unittest.main()
