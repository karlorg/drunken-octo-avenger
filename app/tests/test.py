from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

import os
from mock import ANY, Mock, patch
import unittest
import tempfile

from flask import render_template

from .. import main


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


class TestGetStoneIfArgsGood(TestWithTestingApp):

    def test_returns_none_for_missing_args(self):
        assert main.get_stone_if_args_good(args = {}, moves = []) is None
        assert main.get_stone_if_args_good(
                args = {'move_no': 0, 'row': 0}, moves = []) is None
        assert main.get_stone_if_args_good(
                args = {'move_no': 0, 'column': 0}, moves = []) is None
        assert main.get_stone_if_args_good(
                args = {'column': 0, 'row': 0}, moves = []) is None

    def test_returns_none_if_move_no_bad(self):
        stone = main.get_stone_if_args_good(
                moves=[{'row': 9, 'column': 9}],
                args={'move_no': 0, 'row': 3, 'column': 3})
        assert stone is None
        stone = main.get_stone_if_args_good(
                moves=[{'row': 9, 'column': 9}],
                args={'move_no': 2, 'row': 3, 'column': 3})
        assert stone is None

    def test_returns_black_stone_as_first_move(self):
        stone = main.get_stone_if_args_good(moves=[],
                args={'move_no': 0, 'row': 9, 'column': 9})
        assert stone.row == 9
        assert stone.column == 9
        assert stone.color == 'black'

    def test_returns_white_stone_as_second_move(self):
        stone = main.get_stone_if_args_good(
                moves=[{'row': 9, 'column': 9}],
                args={'move_no': 1, 'row': 3, 'column': 3})
        assert stone.row == 3
        assert stone.column == 3
        assert stone.color == 'white'
