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

### manage.py

Once you have done that, a good place to start is to look in `manage.py` and
run `python manage.py --help`, you can also get help for a specific command,
for example `python manage.py test --help`.

### database

Run `python manage.py remake_db` to create the database (by default it will
appear one directory level higher than your repository root).

Generally you can run `python manage.py db upgrade` to upgrade the database to
the most recent version, for example you may have to do this following a
`git pull`. You can see the current version of the database with
`python manage.py db current`.

## compilation

So far the only code that needs compiling is the coffeescript in `app/coffee`
(and at time of writing, the resulting Javascript is still included in the
repo, so unless you're editing it, you shouldn't need to compile even that).
In the repository root directory, run

    python manage.py coffeebuild

## running

(from virtualenv)

    python manage.py runserver

Access the local server at `http://localhost:5000` by default (other domains
will need to be set in `config.py` to avoid confusing the login system).


## testing

Just run `python manage.py test` to run all of our tests with coverage analysis.
You can run more specific tests, for example whilst developing, rather than
repeat everything here, just checkout the `manage.py` file.


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