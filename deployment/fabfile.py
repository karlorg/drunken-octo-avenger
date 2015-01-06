from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

from fabric.api import abort, cd, env, local, run, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import sed

REPO_URL = 'https://github.com/karlorg/drunken-octo-avenger.git'
REPO_FOLDER_NAME = 'repo'
VENV_FOLDER_NAME = 'virtualenv'

def deploy():
    if 'staging' not in env.host:
        if not confirm(
                "'staging' not found in host name. Deploy here anyway?"):
            abort("Aborting.")
    site_folder = '/home/{user}/sites/{host}'.format(
            user=env.user, host=env.host)
    repo_folder = site_folder + '/' + REPO_FOLDER_NAME
    _create_directory_structure_if_necessary(site_folder)
    _update_repo(repo_folder)
    _update_virtualenv(site_folder, repo_folder)
    config_file = repo_folder + '/config.py'
    _set_secret_key(config_file)
    _disable_debug(config_file)
    _set_domain_name(config_file)
    _reset_db(repo_folder)
    _reload_gunicorn()

def _create_directory_structure_if_necessary(site_folder):
    run('mkdir -p {}'.format(site_folder))

def _update_repo(repo_folder):
    with settings(warn_only=True):
        if (run('test -d {}'.format(repo_folder)).failed):
            run('git clone {remote} {local}'.format(
                remote=REPO_URL, local=repo_folder))
    with cd(repo_folder):
        run('git pull')
        revision = (
                local('git rev-parse --verify HEAD', capture=True)
                .decode().strip()
        )
        run('git reset --hard {}'.format(revision))

def _update_virtualenv(site_folder, repo_folder):
    venv_folder = site_folder + '/' + VENV_FOLDER_NAME
    with settings(warn_only=True):
        if (run('test -d {}'.format(venv_folder)).failed):
            run('virtualenv {} --python=python3'.format(venv_folder))
    with cd(repo_folder):
        run('../{}/bin/pip install -r p3req.txt'.format(VENV_FOLDER_NAME))

def _set_secret_key(config_file):
    import random
    charset = 'abcdefghijklmnopqrstuvwxyz'
    charset += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    charset += '0123456789 _-'
    new_key = repr(''.join(
            (random.SystemRandom().choice(charset) for i in range(32))
    )).replace("'", '"')
    # fabric's sed automatically attempts to 'escape' single quotes, but (if I
    # understand correctly) shell single quotes do not work that way?  You have
    # to close the single quote section, then enter the escaped quote, then
    # re-open the single quotes:  'texttext'\''moretext'
    sed(
            config_file,
            '^SECRET_KEY[^\w_].*$',
            'SECRET_KEY = {}  # noqa'.format(new_key))

def _disable_debug(config_file):
    sed(config_file, '^DEBUG[^\w_].*$', 'DEBUG = False')

def _set_domain_name(config_file):
    sed(config_file, '^DOMAIN[^\w_].*$', 'DOMAIN = {}'.format(
        repr(env.host).replace("'", '"')
    ))

def _reset_db(repo_folder):
    with cd(repo_folder):
        run('../virtualenv/bin/python db_remake.py')

def _reload_gunicorn():
    pid = run('cat /var/run/gunicorn-{}.pid'.format(env.host)).decode().strip()
    run('kill -HUP {}'.format(pid))
