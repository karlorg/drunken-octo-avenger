## setup

I recommend cloning this repository inside an existing directory that's just
for this project.  The sqlite database will be created one directory up from
the repo, and that's also where I recommend you put your virtualenv.

So, create a virtualenv outside the repo, install packages from
`requirements.txt` for Python 2, or `p3req.txt` for Python 3, into it.  I
haven't picked a Python version (yet); if I haven't messed up, 2.7 and 3.4
should both work.  Trying to stay compatible with both.  See 'compatibility'
section below.

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
