from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from contextlib import contextmanager
from itertools import chain
from mock import ANY, Mock, patch
import json
import re
import unittest
import time

from flask import flash, render_template, session, url_for
import flask.ext.testing
import requests
from werkzeug.datastructures import MultiDict

from .. import go_rules
from .. import main
from .. import sgftools
from ..main import DeadStone, Game, Move, Pass, SetupStone, db


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

    @contextmanager
    def assert_flashes(self, snippet, message=None):
        """Assert that the following code creates a Flask flash message.

        The message must contain the given snippet to pass."""
        if message is None:
            message = "'{}' not found in any flash message".format(snippet)
        mock_flash = Mock(spec=flash)
        with patch('app.main.flash', mock_flash):
            yield mock_flash
        for call_args in mock_flash.call_args_list:
            args, _ = call_args
            if snippet.lower() in args[0].lower():
                return
        self.fail(message)


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

    def add_game(self, stones=None):
        game = main.create_game_internal(
                'black@black.com', 'white@white.com', stones)
        return game


class TestFrontPageIntegrated(TestWithTestingApp):

    def test_without_login_shows_persona_login_link(self):
        response = self.test_client.get('/')
        assert re.search(
                r"""<a [^>]*id=['"]persona_login['"]""",
                str(response.get_data())) is not None

    def test_with_login_redirects_to_status(self):
        with self.set_email('test@mockmyid.com') as test_client:
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

    def post_simple_assertion(self, test_client=None, mock_post=None):
        if test_client is None:
            test_client = self.test_client
        if mock_post is None:
            mock_post = self.make_mock_post()
        with patch('app.main.requests.post', mock_post):
            response = test_client.post('/persona/login',
                                        data={'assertion': 'test'})
        return (response, mock_post)


    def test_aborts_on_no_assertion(self):
        response = self.test_client.post('/persona/login',
                                         data={})
        self.assertEqual(response.status_code, 400)

    def test_posts_assertion_to_mozilla(self):
        _, mock_post = self.post_simple_assertion()
        mock_post.assert_called_once_with(
                'https://verifier.login.persona.org/verify',
                data={
                    'assertion': 'test',
                    'audience': ANY
                },
                verify=True
        )

    def test_good_response_sets_session_email_and_persona_email(self):
        with main.app.test_client() as test_client:

            self.post_simple_assertion(test_client)

            self.assertEqual(session['email'], self.TEST_EMAIL)
            self.assertEqual(session['persona_email'], self.TEST_EMAIL)

    def test_bad_response_status_aborts(self):
        mock_post = self.make_mock_post(status='no no NO')
        with main.app.test_client() as test_client:

            response, _ = self.post_simple_assertion(test_client, mock_post)

            self.assertNotIn('email', session)
            self.assertNotEqual(response.status_code, 200)

    def test_bad_response_ok_aborts(self):
        mock_post = self.make_mock_post(ok=False)
        with main.app.test_client() as test_client:

            response, _ = self.post_simple_assertion(test_client, mock_post)

            self.assertNotIn('email', session)
            self.assertNotEqual(response.status_code, 200)


class TestLogoutIntegrated(TestWithTestingApp):

    def test_removes_email_and_persona_email_from_session(self):
        with main.app.test_client() as test_client:
            with test_client.session_transaction() as session:
                session['email'] = 'olduser@remove.me'
                session['persona_email'] = 'olduser@remove.me'

            test_client.post('/logout')

            with test_client.session_transaction() as session:
                self.assertNotIn('email', session)
                self.assertNotIn('persona_email', session)

    def test_no_error_when_email_not_set(self):
        with main.app.test_client() as test_client:
            try:
                test_client.post('/logout')
            except Exception as e:
                self.fail("exception {} raised for logout "
                          "with no email set".format(repr(e)))


class TestChallengeIntegrated(TestWithDb):

    def test_good_post_creates_game(self):
        assert Game.query.all() == []
        with main.app.test_client() as test_client:
            with test_client.session_transaction() as session:
                session['email'] = 'player1@gofan.com'

            test_client.post('/challenge', data=dict(
                opponent_email='player2@gofan.com'))

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
        game5 = Game(black=OTHER_EMAIL_1, white=self.LOGGED_IN_EMAIL)
        game6 = Game(black=self.LOGGED_IN_EMAIL, white=OTHER_EMAIL_1)
        game6.winner = self.LOGGED_IN_EMAIL  # this game is over
        main.db.session.add(game1)
        main.db.session.add(game2)
        main.db.session.add(game3)
        main.db.session.add(game4)
        main.db.session.add(game5)
        main.db.session.add(game6)
        main.db.session.commit()
        main.db.session.add(Move(
            game_no=game4.id, move_no=0,
            row=9, column=9, color=Move.Color.black))
        main.db.session.add(Pass(
            game_no=game5.id, move_no=0, color=Move.Color.black))
        return (game1, game2, game3, game4, game5, game6,)

    def test_anonymous_users_redirected_to_front(self):
        response = self.test_client.get(url_for('status'))
        self.assert_redirects(response, '/')

    def test_shows_links_to_existing_games(self):
        self.setup_test_games()
        with self.set_email() as test_client:
            response = test_client.get(url_for('status'))
        self.assertEqual(
                self.count_pattern_in(r"Game \d", str(response.get_data())),
                4)

    def test_sends_games_to_correct_template_params(self):
        game1, game2, game3, game4, game5, game6 = self.setup_test_games()
        with self.set_email() as test_client:
            with self.patch_render_template() as mock_render:

                test_client.get(url_for('status'))

                args, kwargs = mock_render.call_args
        self.assertEqual(args[0], "status.html")
        your_turn_games = kwargs['your_turn_games']
        not_your_turn_games = kwargs['not_your_turn_games']

        self.assertIn(game1, your_turn_games)
        self.assertNotIn(game2, your_turn_games)
        self.assertNotIn(game3, your_turn_games)
        self.assertIn(game4, your_turn_games)
        self.assertIn(game5, your_turn_games)
        self.assertNotIn(game6, your_turn_games)

        self.assertNotIn(game1, not_your_turn_games)
        self.assertNotIn(game2, not_your_turn_games)
        self.assertIn(game3, not_your_turn_games)
        self.assertNotIn(game4, not_your_turn_games)
        self.assertNotIn(game5, not_your_turn_games)
        self.assertNotIn(game6, not_your_turn_games)

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


class TestGameIntegrated(TestWithDb):

    def pass_twice(self, game):
        db.session.add(Pass(
            game_no=game.id, move_no=0, color=Move.Color.black))
        db.session.add(Pass(
            game_no=game.id, move_no=1, color=Move.Color.white))
        db.session.commit()

    def test_404_if_no_game_specified(self):
        response = self.test_client.get('/game')
        self.assert404(response)

    def test_redirects_to_home_if_game_not_found(self):
        out_of_range = max(chain([0], Game.query.filter(Game.id))) + 1
        response = self.test_client.get(url_for('game', game_no=out_of_range))
        self.assert_redirects(response, '/')

    def do_mocked_get(self, game):
        with self.set_email('black@black.com') as test_client:
            with self.patch_render_template() as mock_render:
                test_client.get(url_for('game', game_no=game.id))
                return mock_render.call_args

    def test_passes_sgf_in_form(self):
        game = self.add_game(['.b'])
        args, kwargs = self.do_mocked_get(game)
        self.assertIn("B[ba]", kwargs['form'].data.data)

    def test_after_two_passes_activates_scoring_interface(self):
        game = self.add_game(['.b', 'bb'])
        self.pass_twice(game)

        args, kwargs = self.do_mocked_get(game)

        self.assertEqual(kwargs['with_scoring'], True)


class TestResumeGameIntegrated(TestWithDb):

    def setUp(self):
        super().setUp()
        self.game = self.add_game()
        db.session.add(Pass(
            game_no=self.game.id, move_no=0, color=Move.Color.black))
        db.session.add(Pass(
            game_no=self.game.id, move_no=1, color=Move.Color.white))
        db.session.commit()

    # at the moment, the correct player to resume play is defined as the
    # opponent of the last player to pass.

    def test_correct_turn_simple(self):
        """Sets turn to correct player in the most simple case."""
        with self.set_email('black@black.com') as test_client:
            test_client.post(url_for('resumegame'), data={
                'game_no': self.game.id, 'move_no': 2})
        self.assertEqual(self.game.to_move(), 'black@black.com')

    def test_correct_turn_with_mark_stones(self):
        """Sets turn to correct player when stones have been marked once.

        That is, the opponent of the last player to pass has marked dead stones
        and submitted that proposal, and the last player to pass wishes to
        resume."""
        # we use the actual mark stones view function for this, because its
        # behaviour needs to match up with ours.
        with self.set_email('black@black.com') as test_client:
            test_client.post(url_for('markdead'), data={
                'game_no': self.game.id, 'move_no': 2, 'response': '(;)'})
        with self.set_email('white@white.com') as test_client:
            test_client.post(url_for('resumegame'), data={
                'game_no': self.game.id, 'move_no': 3})
        self.assertEqual(self.game.to_move(), 'black@black.com')

    def test_removes_dead_stone_marks(self):
        db.session.add(DeadStone(self.game.id, 1, 1))
        with self.set_email('black@black.com') as test_client:
            test_client.post(url_for('resumegame'), data={
                'game_no': self.game.id, 'move_no': 2})
        self.assertEqual(len(self.game.dead_stones), 0)


class TestResignIntegrated(TestWithDb):

    def test_sets_winner(self):
        game = self.add_game()
        self.assertEqual(game.winner, None, "winner should be initially unset")
        with self.set_email(game.black) as test_client:
            test_client.post(url_for('resign'), data=dict(
                game_no=game.id, move_no=0, color=Move.Color.black))
        self.assertEqual(game.winner, game.white)


class TestGetSgfFromGame(unittest.TestCase):

    def test_simple_example_game(self):
        game = Game()
        game.setup_stones = [SetupStone(game_no=game.id, before_move=0,
                                        column=1, row=0,
                                        color=Move.Color.black)]
        game.moves = [Move(game_no=1, move_no=0,
                           row=2, column=3, color=Move.Color.black),
                      Move(game_no=1, move_no=1,
                           row=14, column=15, color=Move.Color.white)]
        sgf = main.get_sgf_from_game(game)
        self.assertRegex(sgf, r";AB\[ba\];B\[dc\];W\[po\]\)")

    def test_dead_stones(self):
        game = Game()
        game.moves = [Move(game_no=1, move_no=0,
                           row=0, column=1, color=Move.Color.black)]
        game.passes = [Pass(game_no=1, move_no=1,
                            color=Move.Color.white),
                       Pass(game_no=1, move_no=2,
                            color=Move.Color.black)]
        game.dead_stones = [DeadStone(game_no=1, row=0, column=1)]

        sgf = main.get_sgf_from_game(game)

        regexp = re.compile(";[^;]*TW[^A-Z]*\[ba][^;]*\)")
        self.assertRegex(sgf, regexp, "territory not found in SGF")


class TestGetRulesBoardFromDbGame(unittest.TestCase):

    def test_combination(self):
        game = Game()
        game.moves = [Move(game.id, 0, 2, 3, Move.Color.black)]
        game.setup_stones = main.get_stones_from_text_map(['.bw'], game)
        board = main.get_rules_board_from_db_game(game)
        self.assertEqual(board[go_rules.Coord(x=0, y=0)], go_rules.Color.empty)
        self.assertEqual(board[go_rules.Coord(x=1, y=0)], go_rules.Color.black)
        self.assertEqual(board[go_rules.Coord(x=2, y=0)], go_rules.Color.white)
        self.assertEqual(board[go_rules.Coord(x=3, y=2)], go_rules.Color.black)

    def test_setup_stones(self):
        """Regression test: need to process setup stones after last move.

        eg. setup stones for 'before move 0' when there are no moves yet.
        """
        game = Game()
        game.moves = []
        game.setup_stones = main.get_stones_from_text_map(['.bw'], game)
        board = main.get_rules_board_from_db_game(game)
        self.assertEqual(board[go_rules.Coord(x=1, y=0)], go_rules.Color.black)

    def test_copes_with_pass_then_move(self):
        """Regression test: process setup stones on first move pass.

        This would fail in tests which use a first turn setup stones &
        pass, with further moves after the pass."""
        game = Game()
        game.moves = [Move(game.id, move_no=1, row=2, column=3,
                           color=Move.Color.white)]
        game.setup_stones = main.get_stones_from_text_map(['.bw'], game)
        board = main.get_rules_board_from_db_game(game)
        self.assertEqual(board[go_rules.Coord(x=1, y=0)], go_rules.Color.black)


class TestPlayStoneIntegrated(TestWithDb):

    def test_can_add_stones_and_passes_to_two_games(self):
        game1 = self.add_game()
        game2 = self.add_game()
        with self.patch_render_template():
            with self.set_email('black@black.com') as test_client:
                test_client.post('/playstone', data=dict(
                    game_no=game1.id, move_no=0, response="(;B[pd])"
                ))
            with self.set_email('black@black.com') as test_client:
                test_client.post('/playstone', data=dict(
                    game_no=game2.id, move_no=0, response="(;B[jj])"
                ))
            with self.set_email('white@white.com') as test_client:
                test_client.post('/playstone', data=dict(
                    game_no=game1.id, move_no=1, response="(;B[pd];W[pp])"
                ))
            with self.set_email('black@black.com') as test_client:
                test_client.post('/playpass', data=dict(
                    game_no=game1.id, move_no=2
                ))
        self.assertEqual(len(game1.moves), 2)
        self.assertEqual(len(game1.passes), 1)
        self.assertEqual(len(game2.moves), 1)
        # also check the data in one of the moves
        moves = Move.query.all()
        move = moves[0]
        self.assertEqual(move.game_no, game1.id)
        self.assertEqual(move.move_no, 0)
        self.assertEqual(move.row, 3)
        self.assertEqual(move.column, 15)
        self.assertEqual(move.color, Move.Color.black)

    def test_redirects_to_home_if_not_logged_in(self):
        game = self.add_game()
        response = self.test_client.post(url_for('playpass'), data=dict(
            game_no=game.id, move_no=0))
        self.assert_redirects(response, '/')

    def test_rejects_new_move_off_turn(self):
        game = self.add_game()
        assert Move.query.all() == []
        with self.set_email('white@white.com') as test_client:
            with self.assert_flashes('not your turn'):
                test_client.post('/playstone', data=dict(
                    game_no=game.id, move_no=0, response="(;W[pq])"
                ))
        moves = Move.query.all()
        assert len(moves) == 0

    def test_rejects_missing_args(self):
        game = self.add_game()
        assert Move.query.all() == []
        with self.set_email('black@black.com') as test_client:
            with self.assert_flashes('invalid'):
                test_client.post('/playstone', data=dict(
                    game_no=game.id
                ), follow_redirects=True)
        moves = Move.query.all()
        assert len(moves) == 0

    def test_handles_missing_game_no(self):
        with self.set_email('white@white.com') as test_client:
            with self.patch_render_template():
                test_client.post('/playstone', data=dict(
                    move_no=0, response="(;W[pq])"
                ))
        # should not raise

    def test_handles_missing_move(self):
        game = self.add_game()
        with self.set_email('black@black.com') as test_client:
            with self.patch_render_template():
                test_client.post('/playstone', data=dict(
                    game_no=game.id, move_no=0, response="(;)"))
        # should not raise

    def test_passes_ordinary_dict_to_helper(self):
        """Regression test: request.form is a werkzeug MultiDict that doesn't
        always raise KeyError for missing arguments; need to check we're
        converting it to an ordinary dict for the helper function."""
        game = self.add_game()
        with self.set_email('black@black.com') as test_client:
            with self.patch_render_template():
                mock_play_move = Mock(spec=main.validate_turn_and_record)
                mock_play_move.return_value = None
                with patch(
                        'app.main.validate_turn_and_record', mock_play_move
                ):
                    test_client.post('/playstone', data=dict(
                        game_no=game.id, move_no=0, response="(;B[jj])"
                    ))
                self.assertIsNotNone(mock_play_move.call_args)
                passed_dict = mock_play_move.call_args[0][3]
                self.assertIsInstance(passed_dict, dict)
                self.assertNotIsInstance(passed_dict, MultiDict)

    def test_returns_to_game_on_illegal_move(self):
        game = self.add_game(['.b'])
        with self.patch_render_template():
            with self.set_email('black@black.com') as test_client:
                response = test_client.post('/playstone', data=dict(
                    game_no=game.id, move_no=0, response="(;B[ba])"
                ))
        self.assert_redirects(response, url_for('game', game_no=game.id))

    def test_counts_passes_toward_turn_count(self):
        game = self.add_game()
        with self.set_email('black@black.com') as test_client:
            test_client.post('/playpass', data=dict(
                game_no=game.id, move_no=0
            ))
        with self.set_email('white@white.com') as test_client:
            test_client.post('/playstone', data=dict(
                game_no=game.id, move_no=1, response="(;B[];W[pp])"
            ))
        self.assertEqual(len(game.moves), 1)

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


class TestMarkDeadIntegrated(TestWithDb):

    def setUp(self):
        super().setUp()
        game = self.add_game(['.b.w',
                              '.b.w',
                              'bb.w',
                              'wwww'])
        db.session.add(Pass(game_no=game.id, move_no=0,
                            color=Move.Color.black))
        db.session.add(Pass(game_no=game.id, move_no=1,
                            color=Move.Color.white))
        db.session.commit()
        self.game = game
        self.sgf_prefix = ("(;AB[ba][bb][bc][ac]" +
                           "AW[da][db][dc][dd][cd][bd][ad]" +
                           ";B[];W[];")
        self.sgf_suffix = ")"

    def coord_set(self):
        db_objs = DeadStone.query.filter(
                DeadStone.game_no == self.game.id).all()
        return set(map(lambda dead: (dead.column, dead.row,), db_objs))

    def do_post(self, territory_sgf, move_no=None):
        game = self.game
        if move_no is None:
            move_no = game.move_no
        response = self.sgf_prefix + territory_sgf + self.sgf_suffix
        with self.set_email(game.to_move()) as test_client:
            with self.patch_render_template():
                test_client.post(url_for('markdead'),
                                 data={'game_no': game.id,
                                       'move_no': move_no,
                                       'response': response})

    def test_advances_turn(self):
        original_turn = self.game.to_move()
        self.do_post('')
        self.assertNotEqual(original_turn, self.game.to_move())

    def test_records_dead_stones_in_db(self):
        territory = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cc]"

        self.do_post(territory)

        coords = self.coord_set()
        self.assertIn((1, 0), coords)
        self.assertIn((1, 1), coords)
        self.assertIn((1, 2), coords)
        self.assertIn((0, 2), coords)

    def test_new_proposal_erases_old(self):
        first_territory = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cc]"
        second_live_stones_coords = [[1, 0], [1, 1], [1, 2], [0, 2]]
        second_territory = "TB"
        for y in range(19):
            for x in range(19):
                if [x, y] not in second_live_stones_coords:
                    second_territory += "[" + sgftools.encode_coord(x, y) + "]"

        self.do_post(first_territory)
        self.do_post(second_territory)

        coords = self.coord_set()
        self.assertNotIn((1, 0), coords)
        self.assertIn((3, 3), coords)

    def test_two_identical_proposals_end_game(self):
        territory = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cc]"
        self.do_post(territory)
        self.assertIsNone(self.game.winner,
                          "game is not over after one submission")

        self.do_post(territory)

        self.assertIsNotNone(self.game.winner,
                             "game is over after second identical submission")

    def test_two_different_proposals_do_not_end_game(self):
        first_territory = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cc]"
        second_territory = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cd]"

        self.do_post(first_territory)
        self.do_post(second_territory)

        self.assertIsNone(self.game.winner,
                          "game is not over after second different submission")

    def test_bad_move_no_does_nothing(self):
        territory = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cc]"
        self.do_post(territory, move_no=42)
        self.assertNotIn((1, 0), self.coord_set())

    def test_malformed_sgf_does_nothing(self):
        territory = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cc]"
        bad_territory = "TW[;]"
        self.do_post(territory)
        original_turn = self.game.to_move()

        self.do_post(bad_territory)

        self.assertEqual(original_turn, self.game.to_move())
        self.assertIn((1, 0), self.coord_set())


# I'm skipping this test because I have removed the method that it tests.
# Still I think the idea of testing that nothing happens should I make an
# invalid request is a good one. But we should test it more functionally, by
# actually making a request, then perhaps checking that the database has not
# moved on and/or the returned page has an error on it. So I'm leaving this
# test here until I check that.
@unittest.skip("Skipping test of removed method")
class TestGetMoveOrPassIfArgsGood(unittest.TestCase):

    def assert_get_move_and_pass(self,
                                 expect_color_or_none=None,
                                 moves=None, passes=None,
                                 game_no=1, move_no=0, row=1, column=2,
                                 omit_args=None):
        if moves is None:
            moves = []
        if passes is None:
            passes = []
        if omit_args is None:
            omit_args = []
        args = {'game_no': game_no, 'move_no': move_no,
                'row': row, 'column': column}
        for omit in omit_args:
            del args[omit]
        move = main.get_move_or_pass_if_args_good(
                which="move", args=args, moves=moves, passes=passes)
        pass_ = main.get_move_or_pass_if_args_good(
                which="move", args=args, moves=moves, passes=passes)
        if expect_color_or_none is None:
            self.assertIsNone(move)
            # don't assert pass is None if the only excluded arguments were
            # ones that don't exist in Pass anyway
            if omit_args and not(set(omit_args).issubset(['row', 'column'])):
                self.assertIsNone(pass_)
        else:
            self.assertEqual(move.row, row)
            self.assertEqual(move.column, column)
            self.assertEqual(move.color, expect_color_or_none)
            self.assertEqual(pass_.color, expect_color_or_none)

    def test_returns_none_for_missing_args(self):
        self.assert_get_move_and_pass(None, omit_args=['game_no'])
        self.assert_get_move_and_pass(None, omit_args=['move_no'])
        self.assert_get_move_and_pass(None, omit_args=['row'])

    def test_returns_none_if_move_no_bad(self):
        self.assert_get_move_and_pass(
                None,
                moves=[{'row': 9, 'column': 9}], passes=[],
                move_no=0)
        self.assert_get_move_and_pass(
                None,
                moves=[{'row': 9, 'column': 9}], passes=[],
                move_no=2)
        self.assert_get_move_and_pass(
                None,
                moves=[{'move_no': 0, 'row': 9, 'column': 9}],
                passes=[{'move_no': 1}],
                move_no=1)
        self.assert_get_move_and_pass(
                None,
                moves=[{'move_no': 0, 'row': 9, 'column': 9}],
                passes=[{'move_no': 1}],
                move_no=3)

    def test_returns_black_as_first_move(self):
        self.assert_get_move_and_pass(
                Move.Color.black,
                moves=[], passes=[])

    def test_returns_white_as_second_move(self):
        self.assert_get_move_and_pass(
                Move.Color.white,
                moves=[{'move_no': 0, 'row': 9, 'column': 9}], passes=[],
                move_no=1)
        self.assert_get_move_and_pass(
                Move.Color.white,
                moves=[], passes=[{'move_no': 0}],
                move_no=1)


class TestServerPlayer(TestWithDb):

    def assert_status_list_lengths(self, email, your_turns, not_your_turns):
        your_turn_games, not_your_turn_games = main.get_status_lists(email)
        self.assertEqual(len(your_turn_games), your_turns)
        self.assertEqual(len(not_your_turn_games), not_your_turns)

    def test_server_player(self):
        server_player_email = "serverplayer@localhost"
        server_player = main.ServerPlayer(server_player_email)
        test_opponent_email = "serverplayermock@localhost"
        main.create_game_internal(server_player_email, test_opponent_email)
        self.assert_status_list_lengths(server_player_email, 1, 0)
        server_player.act()
        self.assert_status_list_lengths(server_player_email, 0, 1)

    # This test is skipped for now, basically a little misunderstanding how the
    # ORM is working. When we attempt this test, what happens is, that all of
    # the database operations that are done in the daemon thread, are rolled
    # back when the thread exits. I'm not sure why. I think it may well have
    # something to do with connection pooling, but the ORM hides that well.
    #
    # Why not use `@unittest.expectedFailure`? This means that the test will
    # not be run at all, whereas using a `assertRaises` context manager we
    # ensure that the test gets run and does not error out on some other
    # exception.  So in particular we are making sure that the code is at least
    # exercised and does not fail with, for example, a type error.
    def test_server_player_daemon(self):
        with self.assertRaises(AssertionError):
            rest_interval = 0.1
            server_player_email = "serverplayer@localhost"
            server_player = main.ServerPlayer(
                    server_player_email, rest_interval=rest_interval)
            test_opponent_email = "serverplayermock@localhost"

            # We start the daemon, create a game, then wait the three times the
            # rest period, during which the daemon should have acted.
            main.create_game_internal(server_player_email, test_opponent_email)
            server_player.start_daemon()
            time.sleep(3 * rest_interval)
            server_player.terminate_daemon()
            self.assert_status_list_lengths(server_player_email, 0, 1)
