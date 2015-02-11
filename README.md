## setup

I recommend cloning this repository inside an existing directory that's just
for this project.  The sqlite database will be created one directory up from
the repo, and that's also where I recommend you put your virtualenv and the
setup script below will do the that.

## setup script

Run the setup script, give the python version you wish to use as the only
argument.

    source setup.sh 3.4

This will create a virtual environment, activate it, and install all of the
dependencies.

## Test Python Versions

The `test_python_versions` script will test different versions of python. It
will call the setup script with different arguments, currently just the 2.7 and
3.4 versions are called but more can easily be added. Worth looking in the
script to see the arguments, but none will cause it to call the entire test
suite, `quick` will just run a single test module and `coverage` will run the
coverage analysis in both versions.

## Database

Run `db_remake.py` to create the database (by default it will appear one
directory level higher than your repository root).

## compilation

So far the only code that needs compiling is the coffeescript in `app/coffee`
(and at time of writing, the resulting Javascript is still included in the
repo, so unless you're editing it, you shouldn't need to compile even that).
In the repository root directory, run

    cake build

## running

(from virtualenv)

    python run.py

## testing

### Python code

    python -m unittest discover [<package path>]

Omit the package path to run all Python tests.  (Please run this before each
commit.  Committing with expected failures is OK, but do check there are no
unexpected failures.)

Or for an individual module/class/method:

    python -m unittest [<component path>]

For notes on running browser automation tests against remote servers, see the
markdown file in `app/browser_tests`.

### Javascript code

Open `app/static/tests/tests.html` in your browser.

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
