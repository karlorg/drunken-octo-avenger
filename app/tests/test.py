from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from contextlib import contextmanager
from mock import ANY, Mock, patch
import re
import unittest

from flask import render_template, session, url_for
import flask.ext.testing
import requests
from werkzeug.datastructures import MultiDict

from .. import main
from ..main import Game, Move, db


class TestWithTestingApp(flask.ext.testing.TestCase):

    def create_app(self):
        main.app.config['TESTING'] = True
        main.app.config['WTF_CSRF_ENABLED'] = False
        return main.app

    def setUp(self):
        self.test_client = main.app.test_client()

    @contextmanager
    def set_email(self, email=None):
        """Set the logged in email value in the session object."""
        if email is None:
            email = self.LOGGED_IN_EMAIL
        with main.app.test_client() as test_client:
            with test_client.session_transaction() as session:
                session['email'] = email
            yield test_client

    @contextmanager
    def patch_render_template(self):
        """Patch out render_template with a mock.

        Use when the return value of the view is not important to the test;
        rendering templates uses a ton of runtime."""
        mock_render = Mock(spec=render_template)
        mock_render.return_value = ''
        with patch('app.main.render_template', mock_render):
            yield mock_render


class TestWithDb(TestWithTestingApp):

    def create_app(self):
        main.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        return super().create_app()

    def setUp(self):
        super().setUp()
        main.db.session.remove()
        main.db.drop_all()
        main.db.create_all()

    def tearDown(self):
        main.db.session.remove()
        main.db.drop_all()
        super().tearDown()


class TestFrontPageIntegrated(TestWithTestingApp):

    def test_without_login_shows_persona_login_link(self):
        response = self.test_client.get('/')
        assert re.search(
                r"""<a [^>]*id=['"]persona_login['"]""",
                str(response.get_data())) is not None

    def test_with_login_redirects_to_status(self):
        with main.app.test_client() as test_client:
            with test_client.session_transaction() as session:
                session['email'] = 'test@mockmyid.com'
            response = test_client.get('/')
        self.assert_redirects(response, url_for('status'))


class TestPersonaLoginIntegrated(TestWithTestingApp):

    TEST_EMAIL = 'test@example.com'

    def make_mock_post(self, ok=True, status='okay', email=TEST_EMAIL):
        mock_post = Mock(spec=requests.post)
        mock_post.return_value = Mock()
        mock_post.return_value.ok = ok
        mock_post.return_value.json.return_value = {
                'status': status,
                'email': email,
        }
        return mock_post

    def test_aborts_on_no_assertion(self):
        response = self.test_client.post(
                '/persona/login',
                data={}
        )
        assert response.status_code == 400

    def test_posts_assertion_to_mozilla(self):
        mock_post = self.make_mock_post()
        with patch('app.main.requests.post', mock_post):
            self.test_client.post(
                    '/persona/login',
                    data={'assertion': 'test'}
            )
        mock_post.assert_called_once_with(
                'https://verifier.login.persona.org/verify',
                data={
                    'assertion': 'test',
                    'audience': ANY
                },
                verify=True
        )

    def test_good_response_sets_session_email_and_persona_email(self):
        mock_post = self.make_mock_post()
        with main.app.test_client() as test_client:
            with patch('app.main.requests.post', mock_post):
                test_client.post(
                        '/persona/login',
                        data={'assertion': 'test'}
                )
            assert session['email'] == self.TEST_EMAIL
            assert session['persona_email'] == self.TEST_EMAIL

    def test_bad_response_aborts(self):
        mock_post = self.make_mock_post(status='no no NO')
        with main.app.test_client() as test_client:
            with patch('app.main.requests.post', mock_post):
                response = test_client.post(
                        '/persona/login',
                        data={'assertion': 'test'}
                )
            assert 'email' not in session
            assert response.status_code != 200


class TestLogoutIntegrated(TestWithTestingApp):

    def test_removes_email_and_persona_email_from_session(self):
        with main.app.test_client() as test_client:
            with test_client.session_transaction() as transaction:
                transaction['email'] = 'olduser@remove.me'
                transaction['persona_email'] = 'olduser@remove.me'
            test_client.post('/logout')
            assert 'email' not in session
            assert 'persona_email' not in session

    def test_no_error_when_email_not_set(self):
        with main.app.test_client() as test_client:
            test_client.post('/logout')


class TestProcessPersonaResponse(unittest.TestCase):

    def test_checks_response_ok(self):
        response = Mock()
        response.ok = False
        assert main.process_persona_response(response).do is False

    def test_checks_status_okay(self):
        response = Mock()
        response.ok = True
        response.json.return_value = {'status': 'very very bad'}
        assert main.process_persona_response(response).do is False

    def test_returns_good_for_good_response(self):
        response = Mock()
        response.ok = True
        response.json.return_value = {
                'status': 'okay',
                'email': 'bob@testcase.python',
        }
        result = main.process_persona_response(response)
        assert result.do is True
        assert result.email == 'bob@testcase.python'


class TestChallengeIntegrated(TestWithDb):

    def test_good_post_creates_game(self):
        assert Game.query.all() == []
        with main.app.test_client() as test_client:
            with test_client.session_transaction() as session:
                session['email'] = 'player1@gofan.com'
            test_client.post('/challenge', data=dict(
                opponent_email='player2@gofan.com'
            ))
        games = Game.query.all()
        assert len(games) == 1
        game = games[0]
        assert game.white == 'player1@gofan.com'
        assert game.black == 'player2@gofan.com'


class TestStatusIntegrated(TestWithDb):

    def count_pattern_in(self, pattern, string):
        return len(re.split(pattern, string)) - 1

    def setup_test_games(self):
        self.LOGGED_IN_EMAIL = 'testplayer@gotgames.mk'
        OTHER_EMAIL_1 = 'rando@opponent.net'
        OTHER_EMAIL_2 = 'wotsit@thingy.com'
        game1 = Game(black=self.LOGGED_IN_EMAIL, white=OTHER_EMAIL_1)
        game2 = Game(black=OTHER_EMAIL_1, white=OTHER_EMAIL_2)
        game3 = Game(black=OTHER_EMAIL_1, white=self.LOGGED_IN_EMAIL)
        game4 = Game(black=OTHER_EMAIL_1, white=self.LOGGED_IN_EMAIL)
        main.db.session.add(game1)
        main.db.session.add(game2)
        main.db.session.add(game3)
        main.db.session.add(game4)
        main.db.session.commit()
        main.db.session.add(Move(
            game_no=game4.id, move_no=0,
            row=9, column=9, color=Move.Color.black))
        return (game1, game2, game3, game4,)

    def test_anonymous_users_redirected_to_front(self):
        response = self.test_client.get(url_for('status'))
        self.assert_redirects(response, '/')

    def test_shows_links_to_existing_games(self):
        self.setup_test_games()
        with self.set_email() as test_client:
            response = test_client.get(url_for('status'))
        self.assertEqual(
                self.count_pattern_in(r"Game \d", str(response.get_data())),
                3)

    def test_sends_games_to_correct_template_params(self):
        game1, game2, game3, game4 = self.setup_test_games()
        with self.set_email() as test_client:
            with self.patch_render_template() as mock_render:
                test_client.get(url_for('status'))
                args, kwargs = mock_render.call_args
        assert args[0] == "status.html"
        your_turn_games = kwargs['your_turn_games']
        not_your_turn_games = kwargs['not_your_turn_games']
        assert game1 in your_turn_games
        assert game4 in your_turn_games
        assert game3 not in your_turn_games
        assert game3 in not_your_turn_games

    def test_games_come_out_sorted(self):
        """Regression test: going via dictionaries can break sorting"""
        for i in range(5):
            db.session.add(Game(black='some@one.com', white='some@two.com'))
            db.session.add(Game(black='some@two.com', white='some@one.com'))
        with self.set_email('some@one.com') as test_client:
            with self.patch_render_template() as mock_render:
                test_client.get(url_for('status'))
                args, kwargs = mock_render.call_args
        your_turn_games = kwargs['your_turn_games']
        not_your_turn_games = kwargs['not_your_turn_games']

        def game_key(game):
            return game.id
        self.assertEqual(
                your_turn_games,
                sorted(your_turn_games, key=game_key))
        self.assertEqual(
                not_your_turn_games,
                sorted(not_your_turn_games, key=game_key))


class TestGetPlayerGames(unittest.TestCase):

    def test_filters_correctly(self):
        TEST_EMAIL = 'our_guy@our_guy.com'
        OTHER_EMAIL_1 = 'other@other.com'
        OTHER_EMAIL_2 = 'other2@other2.com'
        game_not_involved = Game(black=OTHER_EMAIL_1, white=OTHER_EMAIL_2)
        game_black = Game(black=TEST_EMAIL, white=OTHER_EMAIL_1)
        game_white = Game(black=OTHER_EMAIL_1, white=TEST_EMAIL)
        games = [game_not_involved, game_black, game_white]

        result = main.get_player_games(TEST_EMAIL, games)
        assert game_not_involved not in result
        assert game_black in result
        assert game_white in result


class TestIsPlayersTurnInGame(unittest.TestCase):

    def setUp(self):
        self.TEST_EMAIL = 'us@we.com'
        self.OTHER_EMAIL = 'other@other.com'
        self.black_game = Game(black=self.TEST_EMAIL, white=self.OTHER_EMAIL)
        self.white_game = Game(black=self.OTHER_EMAIL, white=self.TEST_EMAIL)

    def test_black_first_move(self):
        moves = []
        self.assertTrue(main.is_players_turn_in_game(
            self.black_game, moves, self.TEST_EMAIL))

    def test_white_first_move(self):
        moves = []
        self.assertFalse(main.is_players_turn_in_game(
            self.white_game, moves, self.TEST_EMAIL))

    def test_black_second_move(self):
        moves = [Move(
            game_no=self.black_game.id, move_no=0,
            row=9, column=9, color=Move.Color.black)]
        self.assertFalse(main.is_players_turn_in_game(
            self.black_game, moves, self.TEST_EMAIL))

    def test_white_second_move(self):
        moves = [Move(
            game_no=self.white_game.id, move_no=0,
            row=9, column=9, color=Move.Color.black)]
        self.assertTrue(main.is_players_turn_in_game(
            self.white_game, moves, self.TEST_EMAIL))


class TestGameIntegrated(TestWithDb):

    def add_game(self):
        game = Game()
        game.black = 'black@black.com'
        game.white = 'white@white.com'
        main.db.session.add(game)
        main.db.session.commit()
        return game

    def test_redirects_to_home_if_no_game_specified(self):
        response = self.test_client.get('/game')
        self.assert_redirects(response, '/')

    def test_passes_correct_goban_format_and_params_to_template(self):
        game = self.add_game()
        mock_render = Mock(spec=render_template)
        mock_render.return_value = ''
        with patch('app.main.render_template', mock_render):
            self.test_client.get('/game?game_no={game}'.format(game=game.id))
        args, kwargs = mock_render.call_args
        assert args[0] == "game.html"
        goban = kwargs['goban']
        assert goban[0][0] == str(goban[0][0])
        assert kwargs['move_no'] == int(kwargs['move_no'])
        assert int(kwargs['move_no']) == 0


class TestPlayStoneIntegrated(TestWithDb):

    def add_game(self):
        game = Game()
        game.black = 'black@black.com'
        game.white = 'white@white.com'
        main.db.session.add(game)
        main.db.session.commit()
        return game

    def test_can_add_stones_to_two_games(self):
        game1 = self.add_game()
        game2 = self.add_game()
        with self.patch_render_template():
            with self.set_email('black@black.com') as test_client:
                test_client.post('/playstone', data=dict(
                    game_no=game1.id, move_no=0, row=3, column=15
                ))
            with self.set_email('black@black.com') as test_client:
                test_client.post('/playstone', data=dict(
                    game_no=game2.id, move_no=0, row=9, column=9
                ))
            with self.set_email('white@white.com') as test_client:
                test_client.post('/playstone', data=dict(
                    game_no=game1.id, move_no=1, row=15, column=15
                ))
        game1moves = Move.query.filter(Move.game_no == game1.id).all()
        game2moves = Move.query.filter(Move.game_no == game2.id).all()
        self.assertEqual(len(game1moves), 2)
        self.assertEqual(len(game2moves), 1)
        # also check the data in one of the moves
        moves = Move.query.all()
        move = moves[0]
        self.assertEqual(move.game_no, game1.id)
        self.assertEqual(move.move_no, 0)
        self.assertEqual(move.row, 3)
        self.assertEqual(move.column, 15)
        self.assertEqual(move.color, Move.Color.black)

    def test_rejects_new_move_off_turn(self):
        game = self.add_game()
        assert Move.query.all() == []
        with self.set_email('white@white.com') as test_client:
            response = test_client.post('/playstone', data=dict(
                game_no=game.id, move_no=0, row=16, column=15
            ), follow_redirects=True)
        moves = Move.query.all()
        assert len(moves) == 0
        assert 'not your turn' in str(response.get_data())

    def test_rejects_missing_args(self):
        game = self.add_game()
        assert Move.query.all() == []
        with self.set_email('black@black.com') as test_client:
            response = test_client.post('/playstone', data=dict(
                game_no=game.id
            ), follow_redirects=True)
        moves = Move.query.all()
        assert len(moves) == 0
        assert 'Invalid' in str(response.get_data())

    def test_handles_missing_game_no(self):
        with self.set_email('white@white.com') as test_client:
            with self.patch_render_template():
                test_client.post('/playstone', data=dict(
                    move_no=0, row=16, column=15
                ))
        # should not raise

    def test_passes_ordinary_dict_to_helper(self):
        """Regression test: request.form is a werkzeug MultiDict that doesn't
        always raise KeyError for missing arguments; need to check we're
        converting it to an ordinary dict for the helper function."""
        game = self.add_game()
        with self.set_email('black@black.com') as test_client:
            with self.patch_render_template():
                mock_get_stone = Mock(spec=main.get_stone_if_args_good)
                mock_get_stone.return_value = None
                with patch(
                        'app.main.get_stone_if_args_good', mock_get_stone
                ):
                    test_client.post('/playstone', data=dict(
                        game_no=game.id, move_no=0, row=9, column=9
                    ))
                assert mock_get_stone.call_args is not None
                passed_dict = mock_get_stone.call_args[1]['args']
                assert not isinstance(passed_dict, MultiDict)

    @unittest.skip(
            """haven't decided yet what should be returned after a move is
            played""")
    def test_no_links_after_playing_a_move(self):
        # regression: testing specifically the response to playing a move due
        # to old bug whereby 'is our turn' testing happened before updating the
        # move list with the new stone
        game = self.add_game()
        with self.set_email('black@black.com') as test_client:
            response = test_client.get(
                    '/game?game_no={game}&move_no=0&row=16&column=15'
                    .format(game=game.id))
        assert 'move_no=' not in str(response.get_data())


class TestGetStoneIfArgsGood(unittest.TestCase):

    def test_returns_none_for_missing_args(self):
        assert main.get_stone_if_args_good(args={}, moves=[]) is None
        assert main.get_stone_if_args_good(
                args={'game_no': 1, 'move_no': 0, 'row': 0}, moves=[]) is None
        assert main.get_stone_if_args_good(
                args={'game_no': 1, 'move_no': 0, 'column': 0}, moves=[]
        ) is None
        assert main.get_stone_if_args_good(
                args={'column': 0, 'row': 0}, moves=[]) is None

    def test_returns_none_if_move_no_bad(self):
        stone = main.get_stone_if_args_good(
                moves=[{'row': 9, 'column': 9}],
                args={'game_no': 1, 'move_no': 0, 'row': 3, 'column': 3})
        assert stone is None
        stone = main.get_stone_if_args_good(
                moves=[{'row': 9, 'column': 9}],
                args={'game_no': 1, 'move_no': 2, 'row': 3, 'column': 3})
        assert stone is None

    def test_returns_black_stone_as_first_move(self):
        stone = main.get_stone_if_args_good(
                moves=[],
                args={'game_no': 1, 'move_no': 0, 'row': 9, 'column': 9})
        assert stone.row == 9
        assert stone.column == 9
        assert stone.color == Move.Color.black

    def test_returns_white_stone_as_second_move(self):
        stone = main.get_stone_if_args_good(
                moves=[{'row': 9, 'column': 9}],
                args={'game_no': 1, 'move_no': 1, 'row': 3, 'column': 3})
        assert stone.row == 3
        assert stone.column == 3
        assert stone.color == Move.Color.white


class TestGetImgArrayFromMoves(unittest.TestCase):

    def test_imgs_appear_on_expected_points(self):
        goban = main.get_img_array_from_moves([
            Move(
                game_no=1, move_no=0,
                row=3, column=4, color=Move.Color.black),
            Move(
                game_no=1, move_no=1,
                row=15, column=16, color=Move.Color.white)
        ])
        assert 'e.gif' in goban[3][3]
        assert 'w.gif' in goban[15][16]
        assert 'b.gif' in goban[3][4]
        ## regression: shared list pointers cause stones to appear on all rows
        assert 'e.gif' in goban[4][4]
