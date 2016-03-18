from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import os
import subprocess

import flask
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
import requests

from app import main
from app.main import app, db
import config

manager = Manager(app)

Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.command
def remake_db(really=False):
    if not really:
        print("You should probably use 'python manage.py db upgrade' instead.")
        print("If you really want to use remake_db, provide option --really.")
        print("")
        print("(See https://flask-migrate.readthedocs.org/en/latest/ for"
              " details.)")
        return 0
    else:
        db.drop_all()
        db.create_all()

def run_command(command):
    """ We frequently inspect the return result of a command so this is just
        a utility function to do this. Generally we call this as:
        return run_command ('command_name args')
    """
    result = os.system(command)
    return 0 if result == 0 else 1

def spawn_command(command):
    """Start a shell command in a new process, return immediately."""
    import shlex
    cmd_args = shlex.split(command)
    return subprocess.Popen(cmd_args)

def spawn_commands_and_wait_forever(*cmds, **kwargs):
    """Spawn each of `cmds` as a subprocess, wait until any of them stops.

    This is intended for commands that you expect to run forever, so
    any command stopping is considered an error and all of them will
    then be aborted.

    If `error_msg` is given as a keyword arg, display that message if any
    subprocess stops.

    If a keyboard interrupt is received, end all processes and return 0.
    """
    import time
    error_msg = kwargs.get('error_msg', '')

    processes = []
    for cmd in cmds:
        processes.append(spawn_command(cmd))

    def poll_processes():
        for process in processes:
            if process.poll() is not None:
                print(error_msg)
                return process.returncode
        return None

    try:
        failure_code = None
        while failure_code is None:
            failure_code = poll_processes()
            time.sleep(0.1)
        return failure_code
    except KeyboardInterrupt:
        return 0
    finally:
        for process in processes:
            process.terminate()

@manager.command
def coffeelint():
    return run_command('coffeelint app/coffee')

coffee_dirs = [
    'app/coffee', 'app/coffee/tests'
]

@manager.command
def coffeebuild():
    return run_command(
        'coffee -c -o app/static/compiled-js app/coffee &&'
        'coffee -c -o app/static/compiled-js/tests app/coffee/tests'
    )

@manager.command
def coffeewatch():
    """Continuously compile any changed coffeescript files."""
    import glob
    cmds = []
    for src_dir in coffee_dirs:
        target_dir = src_dir.replace('app/coffee', 'app/static/compiled-js')
        # produce a list of .coffee files so as not to pick up temp
        # backup files like `#file.coffee#` and `file.coffee~`
        src_files = ' '.join(
            glob.glob("{src_dir}/*.coffee".format(**locals()))
        )
        cmd = "coffee -cwo {target_dir} {src_files}".format(**locals())
        cmds.append(cmd)
    return spawn_commands_and_wait_forever(*cmds,
                                           error_msg="A coffee process died!")

def run_with_test_server(test_command, coverage):
    """Run the test server and the given test command in parallel. If 'coverage'
    is True, then we run the server under coverage analysis and produce a
    coverge report."""
    coverage_prefix = ["coverage", "run", "--source", "app.main"]
    server_command_prefx = coverage_prefix if coverage else ['python']
    server_command = server_command_prefx + ["manage.py", "run_test_server"]
    server = subprocess.Popen(server_command, stderr=subprocess.PIPE)
    # TODO: If we don't get this line we should  be able to detect that
    # and avoid the starting test process.
    for line in server.stderr:
        if b' * Running on' in line:
            break
    test_process = subprocess.Popen(test_command)
    test_process.wait(timeout=60)
    # Once the test process has completed we can shutdown the server. To do so
    # we have to make a request so that the server process can shut down
    # cleanly, and in particular finalise coverage analysis.
    # We could check the return from this is success.
    requests.post('http://localhost:5000/shutdown')
    server_return_code = server.wait(timeout=60)
    if coverage:
        os.system("coverage report -m")
        os.system("coverage html")
    return server_return_code

@manager.command
def test_casper(nocoverage=False):
    """Run the casper test suite with or without coverage analysis."""
    if coffeebuild():
        print("Coffee script failed to compile, exiting test!")
        return 1
    js_test_file = "app/static/compiled-js/tests/browser.js"
    casper_command = ["./node_modules/.bin/casperjs", "test", js_test_file]
    return run_with_test_server(casper_command, not nocoverage)


@manager.command
def test_main(nocoverage=False):
    """Run the python only tests within py.test app/main.py we still run
    the test server in parallel and produce a coverage report."""
    test_command = ['py.test', 'app/main.py']
    return run_with_test_server(test_command, not nocoverage)


@manager.command
def test():
    casper_result = test_casper()
    main_result = test_main()
    return max([casper_result, main_result])


def shutdown():
    """Shutdown the Werkzeug dev server, if we're using it.
    From http://flask.pocoo.org/snippets/67/"""
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:  # pragma: no cover
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@manager.command
def run_test_server():
    """Used by the phantomjs tests to run a live testing server"""
    # running the server in debug mode during testing fails for some reason
    app.config['DEBUG'] = False
    app.config['TESTING'] = True
    port = app.config['LIVESERVER_PORT']
    # Don't use the production database but a temporary test database.
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///test.db"
    db.drop_all()
    db.create_all()
    db.session.commit()

    # Add a route that allows the test code to shutdown the server, this allows
    # us to quit the server without killing the process thus enabling coverage
    # to work.
    app.add_url_rule('/shutdown', 'shutdown', shutdown,
                             methods=['POST', 'GET'])

    app.run(port=port, use_reloader=False, threaded=True)

    db.session.remove()
    db.drop_all()



@manager.command
def test_browser(name):
    """Run a single browser test, given its name (excluding `test_`)"""
    command = "python -m unittest app.browser_tests.test_{}".format(name)
    return run_command(command)


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

# @manager.command
# def test(browser=None, casper=None, module=None, package=None):
#     """For convenience, you can use `test -x` as a shorthand for other tests"""
#     if browser is not None:
#         return test_browser(browser)
#     elif casper is not None:
#         return test_casper(casper)
#     elif module is not None:
#         return test_module(module)
#     elif package is not None:
#         return test_package(package)
#     else:
#         return test_all()

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

# @manager.command
# def run_test_server():
#     """Used by the phantomjs tests to run a live testing server"""
#     # running the server in debug mode during testing fails for some reason
#     app.config['DEBUG'] = False
#     app.config['TESTING'] = True
#     port = config.LIVESERVER_PORT
#     app.run(port=port, use_reloader=False)

@manager.command
def setup_finished_game(black, white):
    """Create a game in the marking dead stones phase, for manual testing. """
    load_sgf(os.path.join(config.basedir, 'sgfs', 'test-game.sgf'),
             black, white)

@manager.command
def load_sgf(filename, black, white):
    """Create a game from an SGF file.

    Dangerous; if the SGF doesn't parse you'll get errors when running
    the server and will have to manually delete the game from the
    database.
    """
    with open(filename) as file:
        sgf = file.read()
    main.create_game_internal(black, white, sgf=sgf)

if __name__ == "__main__":
    manager.run()
