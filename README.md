## setup

Create a virtualenv outside the repo, install packages from `requirements.txt`
for Python 2, or `p3req.txt` for Python 3, into it.  I haven't picked a Python
version (yet); if I haven't messed up, 2.7 and 3.4 should both work.  Trying to
stay compatible with both.  See 'compatibility' section below.

## running

(from virtualenv)

    python run.py

## testing

### Python code

    python -m unittest discover [<package path>]

Omit the package path to run all Python tests.  (Please run this before each
commit.  Committing with expected failures is OK, but do check there are no
unexpected failures.)

### Javascript code

Open `app/static/tests/tests.html` in your browser.

## Compatibility (Python 2/3)

For the moment I'm using recommendations from
[python-future.org](http://python-future.org).  The
file `compat_stub.py` contains a set of imports to put at the top of each file,
to guard against accidentally producing code that behaves differently on Python
2 and 3.
