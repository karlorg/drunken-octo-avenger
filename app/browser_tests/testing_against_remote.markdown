Testing against a remote server has some internal complications which are
described here.

# Quickstart (getting remote testing working)

You'll need to do the following to be able to run browser tests against a
remote server:

* The directory structure on the server needs to be the default provided by the
  deployment scripts (at time of writing these don't exist, but see
  `deployment-notes.markdown` for a description).

* The user account that owns the files on the remote server should have ssh
  authorized keys set up so that you can ssh to it without a password.  This is
  because Fabric operates by ssh'ing into that account to execute commands.

* Install fabric (`pip2 install fabric`) on the local machine.  It can be
  installed globally, so it's not in the requirements files.

* On the local machine, add a line to `server-usernames` in the directory
  *above* the repository (create the file if necessary) containing the host
  name, then whitespace, then the username to use for ssh access.

* Run the tests with the environment variable `LIVESERVER` set to the hostname
  of the remote server (without the `http://`)

# Implementation notes

First, flask-testing's `LiveServerTestCase` needs to be prevented from spawning
a local server.  This is done by overriding its `__call__` method.

Then, there are several convenience methods on our `SeleniumTest` base class
that modify the database and/or retrieve app-specific information without using
the web, to avoid having to go through lengthy logins, game creation etc. every
time a test needs a login session or game as a prerequisite for what is
actually being tested.  To get this to work remotely, we use Fabric to execute
commands on the remote server.

So each of these methods has two paths:

* For local testing, call `manage.py`'s `[methodname]_internal` to do the work
  directly

* For remotes:

  - call `server_tools.[methodname]_on_server`, which runs fabric in a
    subprocess (since it's not Python 3 compatible at time of writing);
  - fabric executes a function in `app/browser_tests/fabfile.py`,
  - which runs `python manage.py [method]` on the remote server,
  - which finally calls `[methodname]_internal` as in the local testing path.

If that's confusing, there's a longer description of this process in Harry
Percival's book online (which is where I got the idea), with an ASCII-art
diagram,
[here](http://chimera.labs.oreilly.com/books/1234000000754/ch17.html#_managing_the_test_database_on_staging).
It's for Django, but the principles are the same.

Currently this creates a lot of long delays in remote test running, presumably
due to Fabric needing to open a new ssh session for every call.  Maybe we could
speed this up by using a Python 3-compatible fork of Fabric (or waiting for
official Python 3 compatibility) and using its API to avoid running it as a
subprocess.
