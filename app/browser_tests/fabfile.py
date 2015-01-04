from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from fabric.api import env, run


def _get_base_folder(host):
    return '~/sites/' + host

def _get_manage_dot_py(host):
    return '{path}/virtualenv/bin/python {path}/repo/manage.py'.format(
            path=_get_base_folder(host)
    )


def clear_games_for_player_on_server(email):
    run('{manage_py} clear_games_for_player {email}'.format(
        manage_py=_get_manage_dot_py(env.host),
        email=email,
    ))
    return

def create_game_on_server(black_email, white_email):
    run('{manage_py} create_game {black_email} {white_email}'.format(
        manage_py=_get_manage_dot_py(env.host),
        black_email=black_email, white_email=white_email,
    ))
    return

def create_session_on_server(email):
    response = run('{manage_py} create_login_session {email}'.format(
        manage_py=_get_manage_dot_py(env.host),
        email=email,
    ))
    print(response)
