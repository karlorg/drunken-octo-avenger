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

def coverage_command(command_args, coverage, accumulate):
    """The `accumulate` argument specifies whether we should add to the existing
    coverage data or wipe that and start afresh. Generally you wish to
    accumulate if you need to run multiple commands and you want the coverage
    analysis relevant to all those commands. So, for the commands we specify
    below this is usually off by default, since if you are running coverage on
    a particular test command then presumably you only wish to know about that
    command. However, for the main 'test' command, we want to accumulte the
    coverage results for both the casper and unit tests, hence in our 'test'
    command below we supply 'accumulate=True' for the sub-commands test_casper
    and run_unittests.
    """

    # No need to specify the sources, this is done in the .coveragerc file.
    if coverage:
        command = ["coverage", "run"]
        if accumulate:
            command.append("-a")
        return command + command_args
    else:
        return ['python'] + command_args

def run_with_test_server(test_command, coverage, accumulate):
    """Run the test server and the given test command in parallel. If 'coverage'
    is True, then we run the server under coverage analysis and produce a
    coverge report.
    """
    # Note, if we start running Selenium tests again, then we should have,
    # rather than a single 'test_command' a series of 'test_commands'. Then
    # we start the server and *then* run each of the test commands, that way
    # we will get the combined coverage of all the test commands, for example
    # selenium + capserJS tests.
    server_command_args = ["manage.py", "run_test_server"]
    server_command = coverage_command(server_command_args, coverage, accumulate)
    server = subprocess.Popen(server_command, stderr=subprocess.PIPE)
    # TODO: If we don't get this line we should  be able to detect that
    # and avoid the starting test process.
    for line in server.stderr:
        if b' * Running on' in line:
            break
    test_process = subprocess.Popen(test_command)
    test_return_code = test_process.wait(timeout=90)
    # Once the test process has completed we can shutdown the server. To do so
    # we have to make a request so that the server process can shut down
    # cleanly, and in particular finalise coverage analysis.
    # We could check the return from this is success.
    requests.post('http://localhost:5000/shutdown')
    server_return_code = server.wait(timeout=90)
    if coverage:
        os.system("coverage report -m")
        os.system("coverage html")
    return test_return_code + server_return_code

@manager.command
def test_casper(name=None, coverage=False, accumulate=False):
    """Run the casper test suite with or without coverage analysis."""
    if coffeebuild():
        print("Coffee script failed to compile, exiting test!")
        return 1
    js_test_file = "app/static/compiled-js/tests/browser.js"
    casper_command = ["./node_modules/.bin/casperjs", "test", js_test_file]
    casper_command.append('--fail-fast')
    casper_command.append('--port={}'.format(app.config['TESTSERVER_PORT']))
    if name is not None:
        casper_command.append('--single={}'.format(name))
    return run_with_test_server(casper_command, coverage, accumulate)


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
    port = app.config['TESTSERVER_PORT']
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
    main.use_log_file_handler()

    app.run(port=port, use_reloader=False, threaded=True)

    db.session.remove()
    db.drop_all()

def run_unittests(unittest_args, coverage, accumulate=False):
    command_args = ['-m', 'unittest'] + unittest_args
    command = coverage_command(command_args, coverage, accumulate)
    result = run_command(" ".join(command))
    if coverage:
        os.system("coverage report -m")
        os.system("coverage html")
    return result

# I've assumed that if you are limiting your tests to just a particular module,
# or a particular package then it's likely because you're implementing a feature
# and not particularly interested in coverage analysis so the default for that
# is not to run coverage analysis. But the defaults for running all your tests
# is to run coverage analysis.

@manager.command
def test_module(module, coverage=False, accumulate=False):
    """ For example you might do `python manage.py test_module app.tests.test'
    """
    return run_unittests([module], coverage)

@manager.command
def test_package(directory, coverage=False, accumulate=True):
    """ For example `python manage.py test_package app.tests`"""
    arguments = ['discover', directory]
    return run_unittests(arguments, coverage, accumulate=accumulate)

@manager.command
def test_units(coverage=False, accumulate=False):
    """ Runs all the unittests but none of the casperJS tests """
    return run_unittests(['discover'], coverage, accumulate=accumulate)

@manager.command
def test_pytest(name=None, coverage=False, accumulate=True, output_capture='fd'):
    """Unlike in casper we run coverage on this command as well, however we need
    to accumulate if we want this to work at all, because we need to
    accumulate the coverage results of the server process as well as the
    pytest process itself. We do this because we want to make sure that the
    tests themselves don't contain dead code. So it almost never makes sense
    to run `test_pytest` with `coverage=True` but `accumulate=False`.
    The 'output_capture' argument is just passed through to pytest, it should be
    one of fd|sys|no, default is 'fd', this will show you the print statements
    only from the tests that fail, but if you need to see some debugging print
    statement set it to 'no'. In general I would like a way for this command to
    simply pass any unknown arguments through to pytest.
    """
    test_file = 'app/tests/browser_tests.py'
    command = ['-m', 'pytest', '--capture={}'.format(output_capture), test_file]
    pytest_command = coverage_command(command, coverage, accumulate)
    if name is not None:
        pytest_command.append('--k={}'.format(name))
    return run_with_test_server(pytest_command, coverage, accumulate)


@manager.option('--nopytest', dest='nopytest',
                default=False, action='store_true')
def test(nopytest, nocoverage=False, coverage_erase=True):
    """ Run both the casperJS and all the unittests. We do not bother to run
    the capser tests if the unittests fail. By default this will erase any
    coverage-data accrued so far, you can avoid this, and thus get the results
    for multiple runs by passing `--coverage_erase=False`"""
    if coverage_erase:
        os.system('coverage erase')
    coverage = not nocoverage
    test_categories = [ ('Unit', test_units),
                        ('Pytest', test_pytest),
                        ('Casper', test_casper)
                      ]
    for name, test_fun in test_categories:
        if name == 'Pytest' and nopytest:
            continue
        test_result = test_fun(coverage=coverage, accumulate=True)
        if test_result:
            print("{} test failure!".format(name))
            return test_result
    print('All tests passed!')
    return 0


@manager.command
def cloud9(nocoffeebuild=False):
    """When you run this command you should be able to view the running web app
    either by "Preview->Preview Running Application", or by visiting:
    `<worksapce>-<username>.c9users.io/` which you can get to by doing the above
    preview and then clicking to pop-out to a new window."""
    if not nocoffeebuild and coffeebuild():
        print("Coffee script failed to compile, exiting test!")
        return 1
    print('You should be able to view the running app by visiting:')
    print('http://drunken-octo-avenger-<username>.c9users.io/')
    return run_command('python manage.py runserver -h 0.0.0.0 -p 8080')



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
