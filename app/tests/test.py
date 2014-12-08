from __future__ import (absolute_import, division, print_function,
        unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input, str, super,
        zip)

import os
from mock import ANY, Mock, patch
import tempfile

from flask import render_template
from flask.ext.testing import TestCase

from .. import main
from ..main import Move


class TestWithTestingApp(TestCase):

    def create_app(self):
        main.app.config['TESTING'] = True
        return main.app

    def setUp(self):
        self.test_client = main.app.test_client()

class TestWithDb(TestWithTestingApp):

    def create_app(self):
        main.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        return super().create_app()

    def setUp(self):
        super().setUp()
        main.db.create_all()

    def tearDown(self):
        main.db.session.remove()
        main.db.drop_all()
        super().tearDown()


class TestGameIntegrated(TestWithDb):

    def test_passes_correct_goban_format_to_template(self):
        mock_render = Mock(wraps=render_template)
        with patch('app.main.render_template', mock_render):
            self.test_client.get('/game')
        args, kwargs = mock_render.call_args
        assert args[0] == "game.html"

        goban = kwargs['goban']
        assert goban[0][0] == str(goban[0][0])
        assert kwargs['move_no'] == int(kwargs['move_no'])

    def test_writes_passed_valid_move_to_db(self):
        assert Move.query.all() == []
        self.test_client.get('/game?move_no=0&row=16&column=15')
        moves = Move.query.all()
        assert len(moves) == 1
        move = moves[0]
        assert move.move_no == 0
        assert move.row == 16
        assert move.column == 15
        assert move.color == Move.Color.black


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
