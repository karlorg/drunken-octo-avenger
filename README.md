## setup

I recommend cloning this repository inside an existing directory that's just
for this project.  The setup scripts (see below) will create the database file
and Python virtual environments one level up from the repository root.

### setup script

Run the setup script, give the python version you wish to use as the only
argument.

    source setup.sh 3.4

This will create a virtual environment, activate it, and install all of the
dependencies.

### database

Run `python manage.py remake_db` to create the database (by default it will
appear one directory level higher than your repository root).

## compilation

So far the only code that needs compiling is the coffeescript in `app/coffee`
(and at time of writing, the resulting Javascript is still included in the
repo, so unless you're editing it, you shouldn't need to compile even that).
In the repository root directory, run

    cake build

## running

(from virtualenv)

    python manage.py runserver

Access the local server at `http://localhost:5000` by default (other domains
will need to be set in `config.py` to avoid confusing the login system).

Note: When you run the server it may tell you that it is:

    Running on http://127.0.0.1:5000/

If you actually go there though you will not be able to login via persona
because there will be an audience and domain mismatch. So make sure you visit
`http://localhost:5000` instead.

## testing

### Python code

#### testing multiple Python versions

The `test_python_versions` script will run tests against several versions of
python. It will call the setup script with different arguments, currently just
the 2.7 and 3.4 versions are called but more can easily be added. Worth looking
in the script to see the arguments, but none will cause it to call the entire
test suite, `quick` will just run a single test module and `coverage` will run
the coverage analysis in both versions.

#### more specific testing

You can also use various `python manage.py` commands, eg.:

    python manage.py test_all
    python manage.py test_package app.tests
    python manage.py test_module app.browser_tests.test_frontpage
    python manage.py test_browser frontpage
    python manage.py test_casper ChallengeTest

As a shorthand, you can also use `python manage.py test -x` where `x` is `p`
for package, `m` for module, `b` for browser or `c` for casper, or leave out
the option to test all.

You can also use `python -m unittest [discover]` as normal.

#### coverage

`python manage.py coverage -q` will produce coverage stats for the non-browser
automation tests (`-b` runs the browser tests, but coverage isn't working for
those yet).  View the results in the `htmlcov` directory.

#### testing against a remote server

For notes on running browser automation tests against remote servers, see the
markdown file in `app/browser_tests`.

### Javascript code

To enable the coverage options for Javascript, run a local server as above and
open `http://localhost:5000/static/tests/tests.html`.  This may later become
the only way to run the tests if we start doing clever things that get the
server involved in JS testing.

If you don't care about coverage, you can also just open the local file
`app/static/tests/tests.html` in your browser.

## Compatibility (Python 2/3)

For the moment I'm using recommendations from
[python-future.org](http://python-future.org); if you see anything that looks
not quite idiomatic for either 2 or 3, may be worth checking there before
changing it.  The aim is to write in a Python 3 style with Python 2
compatibility; for example, use `range()` and import the 'future' `range` for
Python 2, as opposed to using `xrange()` and importing the 'past' `xrange` for
Python 3.

The file `compat_stub.py` contains a set of imports to put at the
top of each file, to guard against accidentally producing code that behaves
differently on Python 2 and 3.
