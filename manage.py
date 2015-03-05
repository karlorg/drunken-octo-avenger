from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import os
import pickle

from flask.ext.script import Manager

from app.main import Game, Move, add_stones_from_text_map_to_game, app, db

manager = Manager(app)

@manager.command
def remake_db():
    db.drop_all()
    db.create_all()

@manager.command
def test_browser(name):
    """Run a single browser test, given its name (excluding `test_`)"""
    result = os.system(
            "python -m unittest app.browser_tests.test_{}".format(name))
    return (0 if result == 0 else 1)

@manager.command
def test_module(module):
    """ For example you might do `python manage.py test_module app.tests.test'
    """
    result = os.system("python -m unittest " + module)
    return (0 if result == 0 else 1)

@manager.command
def test_package(directory):
    result = os.system("python -m unittest discover " + directory)
    return (0 if result == 0 else 1)

@manager.command
def test_all():
    result = os.system("python -m unittest discover")
    return (0 if result == 0 else 1)

@manager.command
def test(browser=None, module=None, package=None):
    """For convenience, you can use `test -x` as a shorthand for other tests"""
    if browser is not None:
        return test_browser(browser)
    elif module is not None:
        return test_module(module)
    elif package is not None:
        return test_package(package)
    else:
        return test_all()

@manager.command
def coverage(quick=False, browser=False):
    rcpath = os.path.abspath('.coveragerc')

    quick_command = 'test_package app.tests'
    browser_command = 'test_module app.browser_tests.phantom'
    full_command = 'test_all'

    if quick:
        manage_command = quick_command
    elif browser:
        manage_command = browser_command
    else:
        manage_command = full_command

    if os.path.exists('.coverage'):
        os.remove('.coverage')
    os.system((
            "COVERAGE_PROCESS_START='{0}' "
            "coverage run manage.py {1}"
            ).format(rcpath, manage_command))
    os.system("coverage combine")
    os.system("coverage report -m")
    os.system("coverage html")


@manager.command
def clear_games_for_player(email):
    """Clear all of `email`'s games from the database."""
    clear_games_for_player_internal(email)

def clear_games_for_player_internal(email):
    """Clear all of `email`'s games from the database."""
    games_as_black = Game.query.filter(Game.black == email).all()
    games_as_white = Game.query.filter(Game.white == email).all()
    games = games_as_black + games_as_white
    moves = Move.query.filter(Move.game in games).all()
    for move in moves:
        db.session.delete(move)
    for game in games:
        db.session.delete(game)
        db.session.commit()

@manager.command
def create_game(black_email, white_email, pickled_stones=None):
    """Create a custom game in the database without using the web."""
    if pickled_stones is None:
        stones = None
    else:
        stones = pickle.loads(stones)
    create_game_internal(black_email, white_email, stones)

def create_game_internal(black_email, white_email, stones=None):
    game = Game()
    game.black = black_email
    game.white = white_email
    db.session.add(game)
    db.session.commit()
    if stones is not None:
        add_stones_from_text_map_to_game(stones, game)

@manager.command
def create_login_session(email):
    """Set up a pre-authenticated login session.

    Prints the cookie name, value, and path that should be set in the browser
    in order to use this session.
    """
    cookie = create_login_session_internal(email)
    print(cookie['name'])
    print(cookie['value'])
    print(cookie['path'])

def create_login_session_internal(email):
    """Set up a pre-authenticated login session.

    In contrast to the manage.py command, this function only creates the
    session and returns the cookie name, value, and path without printing.
    """
    interface = app.session_interface
    session = interface.session_class()
    session['email'] = email
    # the following process for creating the cookie value is copied from
    # the Flask source; if the cookies created by this method stop
    # working, see if a Flask update has changed the cookie creation
    # procedure in flask/sessions.py -> SecureCookieSessionInterface
    # (currently the default) -> save_session
    cookie_value = (
            interface.get_signing_serializer(app).dumps(dict(session))
    )
    return dict(
            name=app.session_cookie_name,
            value=cookie_value,
            path=interface.get_cookie_path(app),
    )

if __name__ == "__main__":
    manager.run()
