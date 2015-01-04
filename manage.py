from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from flask.ext.script import Manager

from app.main import app

manager = Manager(app)

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
