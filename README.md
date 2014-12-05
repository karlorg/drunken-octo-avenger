## setup

Create a virtualenv outside the repo, install packages from `requirements.txt`
into it.  I haven't picked a Python version (yet); if I haven't messed up, 2.7
and 3.4 should both work.  Trying to stay compatible with both.

## running

(from virtualenv)

    python app/main.py

## testing

    python -m unittest discover [<package path>]
