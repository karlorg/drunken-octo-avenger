from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from os import path
import subprocess

THIS_FOLDER = path.dirname(path.abspath(__file__))
FOLDER_OUTSIDE_REPO = path.dirname(path.dirname(path.dirname(THIS_FOLDER)))
USERNAMES_PATH = path.join(FOLDER_OUTSIDE_REPO, "server-usernames")

class UsernameNotFoundForHostError(Exception):
    pass

def _get_username_on_server(host):
    """Return appropriate username to run fab commands on server.

    Uses a file outside the repo to look up the name, see constants in this
    file.  Usernames file should contain one line per server, with the hostname
    first, followed by whitespace, then the user name.
    """
    file = open(USERNAMES_PATH, 'r')
    for line in file:
        if line.startswith(host):
            return line.split()[1]
    raise UsernameNotFoundForHostError(host)

def _run_fab_command(host, command, *args):
    username = _get_username_on_server(host)
    response = subprocess.check_output(
            [
                'fab',
                command,
                '--host={}'.format(host),
                '--user={}'.format(username),
                '--hide=everything,status',
            ] + list(args),
            cwd=THIS_FOLDER
    ).decode().strip()
    return response

def clear_games_for_player_on_server(host, email):
    """Use fabric to clear a player's games on the remote server."""
    _run_fab_command(
            host,
            'clear_games_for_player_on_server:email={}'.format(email))

def create_game_on_server(host, black_email, white_email):
    """Use fabric to create a custom game on the remote server."""
    _run_fab_command(
            host,
            'create_game_on_server:black_email={0},white_email={1}'
            .format(black_email, white_email))

def create_session_on_server(host, email):
    """Use fabric to create a login session on the remote server.

    Return a dictionary of cookie name, value, and path to set.
    """
    response = _run_fab_command(
            host, 'create_session_on_server:email={}'.format(email))
    name, value, path = response.splitlines()
    return dict(name=name, value=value, path=path)
