from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from contextlib import contextmanager
from itertools import chain
from mock import ANY, Mock, patch
import re
import unittest
import time

from flask import flash, render_template, session, url_for
import flask.ext.testing
import requests

from .. import main
from ..main import Game, User, db


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

    def add_game(self, sgf_or_stones=None, stones=None, sgf=None,
                 black='black@black.com', white='white@white.com',
                 finished=False):
        game = main.create_game_internal(
            black=black, white=white,
            sgf_or_stones=sgf_or_stones, stones=stones, sgf=sgf)
        if finished:
            game.finished = True
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


class TestNativeLoginIntegrated(TestWithDb):

    def test_unknown_username(self):
        self.assertEqual(db.session.query(User).count(), 0)
        db.session.add(User(username='bill'))
        db.session.commit()
        with main.app.test_client() as test_client:
            self.assertNotIn('email', flask.session)
            with self.assert_flashes('not found'):

                response = test_client.post(url_for('login'),
                                            data=dict(username='ted',
                                                      password='theolog'))

            self.assertNotIn('email', flask.session)
        self.assert_redirects(response, '/')

    def test_good_login(self):
        db.session.add(User(username='rufus'))
        db.session.commit()
        with main.app.test_client() as test_client:
            self.assertNotIn('email', flask.session)

            response = test_client.post(url_for('login'),
                                        data=dict(username='rufus',
                                                  password='dudes'))

            self.assertIn('email', flask.session)
            self.assertEqual(flask.session['email'], 'rufus')
        self.assert_redirects(response, '/')


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

    def test_no_content_on_post(self):
        response = self.test_client.post(url_for('logout'))
        self.assertEqual(len(response.data), 0)

    def test_returns_to_front_on_get(self):
        response = self.test_client.get(url_for('logout'))
        self.assert_redirects(response, '/')

    def test_removes_email_and_persona_email_from_session(self):
        with main.app.test_client() as test_client:
            with test_client.session_transaction() as session:
                session['email'] = 'olduser@remove.me'
                session['persona_email'] = 'olduser@remove.me'
            with self.patch_render_template():

                test_client.post('/logout')

            with test_client.session_transaction() as session:
                self.assertNotIn('email', session)
                self.assertNotIn('persona_email', session)

    def test_no_error_when_email_not_set(self):
        with main.app.test_client() as test_client:
            try:
                with self.patch_render_template():
                    test_client.post('/logout')
            except Exception as e:
                self.fail("exception {} raised for logout "
                          "with no email set".format(repr(e)))


class TestChallengeIntegrated(TestWithDb):

    def test_good_post_creates_game(self):
        assert Game.query.all() == []
        with self.set_email('white@white.com') as test_client:
            test_client.post('/challenge', data=dict(
                opponent_email='black@black.com'))
        game = db.session.query(Game).one()
        self.assertEqual(game.white, 'white@white.com')
        self.assertEqual(game.black, 'black@black.com')
        self.assertIn("(;", game.sgf)
        self.assertFalse(game.finished)


class TestCreateAccountIntegrated(TestWithDb):

    def test_get_request_shows_form(self):
        with self.patch_render_template() as mock_render:
            self.test_client.get(url_for('create_account'))
            args, kwargs = mock_render.call_args
            self.assertEqual('create_account.html', args[0])

    def test_good_post_creates_account_and_logs_in(self):
        self.assertEqual(db.session.query(User).count(), 0)
        with main.app.test_client() as test_client:
            self.assertNotIn('email', flask.session)
            with self.patch_render_template():
                test_client.post(url_for('create_account'),
                                 data=dict(username='freddy',
                                           password1='letmein',
                                           password2='letmein'))
            self.assertIn('email', flask.session)
            self.assertEqual(flask.session['email'], 'freddy')
        user = db.session.query(User).one()
        self.assertEqual(user.username, 'freddy')

    def test_non_matching_passwords(self):
        with main.app.test_client() as test_client:
            with self.assert_flashes("don't match"):
                with self.patch_render_template() as mock_render:
                    test_client.post(url_for('create_account'),
                                     data=dict(username='freddy',
                                               password1='letmein',
                                               password2='letmien'))
                    args, kwargs = mock_render.call_args
                    self.assertEqual('create_account.html', args[0])
            self.assertNotIn('email', flask.session)


class TestStatusIntegrated(TestWithDb):

    def count_pattern_in(self, pattern, string):
        return len(re.split(pattern, string)) - 1

    def setup_test_games(self):
        self.LOGGED_IN_EMAIL = 'testplayer@gotgames.mk'
        OTHER_EMAIL_1 = 'rando@opponent.net'
        OTHER_EMAIL_2 = 'wotsit@thingy.com'
        game1 = self.add_game(black=self.LOGGED_IN_EMAIL, white=OTHER_EMAIL_1)
        game2 = self.add_game(black=OTHER_EMAIL_1, white=OTHER_EMAIL_2)
        game3 = self.add_game(black=OTHER_EMAIL_1, white=self.LOGGED_IN_EMAIL)
        game4 = self.add_game(black=OTHER_EMAIL_1, white=self.LOGGED_IN_EMAIL,
                              sgf="(;B[jj])")
        game5 = self.add_game(black=OTHER_EMAIL_1, white=self.LOGGED_IN_EMAIL,
                              sgf="(;B[])")
        game6 = self.add_game(black=self.LOGGED_IN_EMAIL, white=OTHER_EMAIL_1,
                              finished=True)
        return (game1, game2, game3, game4, game5, game6,)

    def test_sends_games_to_correct_template_params(self):
        game1, game2, game3, game4, game5, game6 = self.setup_test_games()
        with self.set_email() as test_client:
            with self.patch_render_template() as mock_render:

                test_client.get(url_for('status'))

                args, kwargs = mock_render.call_args
        self.assertEqual(args[0], "status.html")
        your_turn_games = kwargs['your_turn_games']
        not_your_turn_games = kwargs['not_your_turn_games']

        self.assertEqual(set(your_turn_games), set([game1, game4, game5]))
        self.assertEqual(set(not_your_turn_games), set([game3]))

    def test_shows_links_to_existing_games(self):
        self.setup_test_games()
        with self.set_email() as test_client:
            response = test_client.get(url_for('status'))
        self.assertEqual(
                self.count_pattern_in(r"Game \d", str(response.get_data())),
                4)

    def test_anonymous_users_redirected_to_front(self):
        with main.app.test_client() as test_client:
            response = test_client.get(url_for('status'))
        self.assert_redirects(response, '/')

    def test_games_come_out_sorted(self):
        """Regression test: going via dictionaries can break sorting"""
        for i in range(5):
            self.add_game(black='some@one.com', white='some@two.com')
            self.add_game(black='some@two.com', white='some@one.com')
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


class TestFinishedIntegrated(TestWithDb):

    def test_anonymous_users_redirected_to_front(self):
        with main.app.test_client() as test_client:
            response = test_client.get(url_for('finished'))
        self.assert_redirects(response, '/')

    def test_shows_only_finished_games(self):
        black_game = self.add_game(black='us@we.com', finished=True)
        white_game = self.add_game(white='us@we.com', finished=True)
        self.add_game(black='us@we.com', finished=False)
        self.add_game(finished=True)
        with self.set_email('us@we.com') as test_client:
            with self.patch_render_template() as mock_render:

                test_client.get(url_for('finished'))

                args, kwargs = mock_render.call_args
        self.assertEqual(args[0], "finished.html")
        finished_games = kwargs['finished_games']
        self.assertEqual(set(finished_games), set([black_game, white_game]))


class TestGameIntegrated(TestWithDb):

    def test_404_if_no_game_specified(self):
        response = self.test_client.get('/game')
        self.assert404(response)

    def test_redirects_to_home_if_game_not_found(self):
        out_of_range = max(chain([0], Game.query.filter(Game.id))) + 1
        with main.app.test_client() as test_client:
            response = test_client.get(url_for('game', game_no=out_of_range))
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
        game = self.add_game("(;B[];W[])")
        args, kwargs = self.do_mocked_get(game)
        self.assertEqual(kwargs['with_scoring'], True)


class TestResignIntegrated(TestWithDb):

    def test_sets_finished(self):
        game = self.add_game()
        self.assertFalse(game.finished,
                         "game should not initially be finished")
        with self.set_email(game.black) as test_client:
            test_client.post(url_for('play', game_no=game.id),
                             data=dict(resign_button='resign'))
        self.assertTrue(game.finished,
                        "game should be finished after resign posted")

    def test_nothing_happens_off_turn(self):
        game = self.add_game()
        self.assertFalse(game.finished,
                         "game should not initially be finished")
        with self.set_email(game.white) as test_client:
            test_client.post(url_for('play', game_no=game.id),
                             data=dict(resign_button='resign'))
        self.assertFalse(game.finished,
                         "game should not be finished")


class TestPlayIntegrated(TestWithDb):

    def test_can_add_stones_and_passes_to_two_games(self):
        game1 = self.add_game()
        game2 = self.add_game()
        with self.patch_render_template():
            with self.set_email('black@black.com') as test_client:
                test_client.post(url_for('play', game_no=game1.id),
                                 data=dict(response="(;B[pd])"))
            with self.set_email('black@black.com') as test_client:
                test_client.post(url_for('play', game_no=game2.id),
                                 data=dict(response="(;B[jj])"))
            with self.set_email('white@white.com') as test_client:
                test_client.post(url_for('play', game_no=game1.id),
                                 data=dict(response="(;B[pd];W[pp])"))
            with self.set_email('black@black.com') as test_client:
                test_client.post(url_for('play', game_no=game1.id),
                                 data=dict(response="(;B[pd];W[pp];B[])"))
        self.assertEqual(game1.sgf, "(;B[pd];W[pp];B[])")
        self.assertEqual(game2.sgf, "(;B[jj])")

    def test_redirects_to_home_if_not_logged_in(self):
        game = self.add_game()
        with main.app.test_client() as test_client:
            response = test_client.post(
                url_for('play', game_no=game.id),
                data=dict(response="(;B[])"))
        self.assert_redirects(response, '/')

    def test_redirects_to_home_if_game_not_found(self):
        with self.set_email('black@black.com') as test_client:
            response = test_client.post(
                url_for('play', game_no=0),
                data=dict(response="(;B[])"))
        self.assert_redirects(response, '/')

    def test_rejects_new_move_off_turn(self):
        game = self.add_game()
        self.assertIn("(;", game.sgf)
        with self.set_email('white@white.com') as test_client:
            with self.assert_flashes('not your turn'):
                test_client.post(url_for('play', game_no=game.id),
                                 data=dict(response="(;W[pq])"))
        self.assertIn("(;", game.sgf)

    def test_rejects_missing_args(self):
        game = self.add_game()
        self.assertIn("(;", game.sgf)
        with self.set_email('black@black.com') as test_client:
            with self.assert_flashes('invalid'):
                test_client.post(url_for('play', game_no=game.id), data={},
                                 follow_redirects=True)
        self.assertIn("(;", game.sgf)

    def test_works_with_setup_stones(self):
        game = self.add_game("(;AW[ba])")
        with self.set_email('black@black.com') as test_client:
            test_client.post(url_for('play', game_no=game.id),
                             data=dict(response="(;AW[ba]B[bc])"))
        self.assertEqual(game.sgf, "(;AW[ba]B[bc])")

    def test_rejects_invalid_move(self):
        game = self.add_game("(;AW[ba])")
        with self.set_email('black@black.com') as test_client:
            with self.assert_flashes('invalid'):
                response = test_client.post(
                    url_for('play', game_no=game.id),
                    data=dict(response="(;AW[ba]B[ba])"))
        self.assertEqual(game.sgf, "(;AW[ba])")
        self.assert_redirects(response, url_for('game', game_no=game.id))

    def test_handles_missing_move(self):
        game = self.add_game()
        with self.set_email('black@black.com') as test_client:
            test_client.post(url_for('play', game_no=game.id),
                             data=dict(response="(;)"))  # should not raise

    def test_counts_passes_toward_turn_count(self):
        game = self.add_game("(;)")
        with self.set_email('black@black.com') as test_client:
            test_client.post(url_for('play', game_no=game.id),
                             data=dict(response="(;B[])"))
        with self.set_email('white@white.com') as test_client:
            test_client.post(url_for('play', game_no=game.id),
                             data=dict(response="(;B[];W[pp])"))
        self.assertEqual(game.sgf, "(;B[];W[pp])")

    def test_two_identical_deadstones_end_game(self):
        tw = 'TW[aa][ab][ac][ba][bb][bc][ca][cb][cc]'
        old_sgf = '(;SZ[3];B[];W[];{})'.format(tw)
        new_sgf = '(;SZ[3];B[];W[];{};{})'.format(tw, tw)
        game = self.add_game(old_sgf)
        self.assertFalse(game.finished,
                         "game is not initially finished")

        with self.set_email('white@white.com') as test_client:
            test_client.post(url_for('play', game_no=game.id),
                             data=dict(response=new_sgf))

        new_game = db.session.query(Game).filter_by(id=game.id).one()
        self.assertEqual(new_game.sgf, new_sgf)
        self.assertTrue(new_game.finished,
                        "game is over after second identical submission")

    def test_two_different_deadstones_do_not_end_game(self):
        tw0 = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cc]"
        tw1 = "TW[aa][ab][ac][ba][bb][bc][ca][cb][cd]"
        old_sgf = '(;SZ[3];B[];W[];{})'.format(tw0)
        new_sgf = '(;SZ[3];B[];W[];{};{})'.format(tw0, tw1)
        game = self.add_game(old_sgf)
        self.assertFalse(game.finished,
                         "game is not initially finished")

        with self.set_email('white@white.com') as test_client:
            test_client.post(url_for('play', game_no=game.id),
                             data=dict(response=new_sgf))

        new_game = db.session.query(Game).filter_by(id=game.id).one()
        self.assertEqual(new_game.sgf, new_sgf)
        self.assertFalse(new_game.finished,
                         "game is not over after different submission")

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


class TestStorage(TestWithDb):

    def test_handles_large_sgf(self):
        # this will hopefully fail if we switch from SQLite to a backend that
        # actually restricts the length of string fields; in which case, we
        # probably would have to save SGFs in files or something.
        with open('app/tests/adc-karlnaylor-948890-20150121.sgf') as test_file:
            test_sgf = test_file.read()
        saved = Game(black='black@black.com', white='white@white.com',
                     sgf=test_sgf)
        db.session.add(saved)
        db.session.commit()
        returned = db.session.query(Game).filter_by(id=saved.id).one()
        self.assertEqual(returned.sgf, saved.sgf)


class TestSgfFromTextMap(unittest.TestCase):

    def test_empty_map(self):
        self.assertEqual(main.sgf_from_text_map([]), "(;)")

    def test_black_and_white_stone(self):
        self.assertEqual(main.sgf_from_text_map(['.w', 'b.']),
                         "(;AB[ab]AW[ba])")


@unittest.skip("""Server player needs updated to new architecture.""")
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
