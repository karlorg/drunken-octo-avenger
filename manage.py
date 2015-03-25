from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import os
import pickle

from flask.ext.script import Manager

from app.main import Game, Move, add_stones_from_text_map_to_game, app, db
import config

manager = Manager(app)

@manager.command
def remake_db():
    db.drop_all()
    db.create_all()

def run_command(command):
    """ We frequently inspect the return result of a command so this is just
        a utility function to do this. Generally we call this as:
        return run_command ('command_name args')
    """
    result = os.system(command)
    return 0 if result == 0 else 1

@manager.command
def coffeelint():
    return run_command('coffeelint app/coffee')

@manager.command
def coffeebuild():
    return run_command('coffee -c -o app/static app/coffee')

@manager.command
def test_browser(name):
    """Run a single browser test, given its name (excluding `test_`)"""
    command = "python -m unittest app.browser_tests.test_{}".format(name)
    return run_command(command)

@manager.command
def test_casper(name=None):
    """Run the specified single CasperJS test, or all if not given"""
    from app.browser_tests.test_phantom import PhantomTest
    phantom_test = PhantomTest('test_run')
    phantom_test.set_single(name)
    result = phantom_test.test_run()
    return (0 if result == 0 else 1)

@manager.command
def test_module(module):
    """ For example you might do `python manage.py test_module app.tests.test'
    """
    return run_command("python -m unittest " + module)

@manager.command
def test_package(directory):
    return run_command("python -m unittest discover " + directory)

@manager.command
def test_all():
    return run_command("python -m unittest discover")

@manager.command
def test(browser=None, casper=None, module=None, package=None):
    """For convenience, you can use `test -x` as a shorthand for other tests"""
    if browser is not None:
        return test_browser(browser)
    elif casper is not None:
        return test_casper(casper)
    elif module is not None:
        return test_module(module)
    elif package is not None:
        return test_package(package)
    else:
        return test_all()

@manager.command
def coverage(quick=False, browser=False, phantom=False):
    rcpath = os.path.abspath('.coveragerc')

    quick_command = 'test_package app.tests'
    # once all browser tests are converted to phantom, we can remove the
    # phantom option
    browser_command = 'test_package app.browser_tests'
    phantom_command = 'test_module app.browser_tests.phantom'
    full_command = 'test_all'

    if quick:
        manage_command = quick_command
    elif browser:
        manage_command = browser_command
    elif phantom:
        manage_command = phantom_command
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
def run_test_server():
    """Used by the phantomjs tests to run a live testing server"""
    # running the server in debug mode during testing fails for some reason
    app.config['DEBUG'] = False
    app.config['TESTING'] = True
    port = config.LIVESERVER_PORT
    app.run(port=port, use_reloader=False)

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
