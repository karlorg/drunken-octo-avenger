#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (
        absolute_import, division, print_function, unicode_literals)
from builtins import (ascii, bytes, chr, dict, filter, hex, input,  # noqa
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import os
import sys
from pip.req import parse_requirements



try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()
elif sys.argv[-1] == 'lint':
    # For this to work you need to install pylint
    # pip install pylint
    os.system('pylint app')
    sys.exit()
elif sys.argv[-1] == 'flake':
    # For this to work you will need to install flake8
    # pip install flake8
    os.system('flake8 app')
    sys.exit()
elif sys.argv[-1] == 'coverage':
    # For this to work you will need to install coverage
    # pip install coverage
    os.system('coverage run --source app setup.py test')
    os.system('coverage report -m')
    os.system('coverage html')
    sys.exit()


# It is kind of annoying that github reads in a 'README.md' whilst pypi
# requires rich structured text. Otherwise for this we could simple do a
# `open(README.md').read()`
# This is not a big problem here as we are unlikely to publish this to pypi
# anyway.
readme = """
A rather immature project aimed at creating a usable online Go server for
turn-based games.
"""

if sys.version_info < (3, 0):
    # parse_requirements() returns generator of
    # pip.req.InstallRequirement objects
    install_reqs = parse_requirements("requirements.txt")
else:
    install_reqs = parse_requirements("p3req.txt")

setup(
    name='drunken-octo-avenger',
    version='0.1.0',
    description="""A simple web application for an online Go server for
                   turn based games.
                """,
    long_description=readme + '\n\n',
    author='Karl Naylor',
    author_email='karlorg@users.noreply.github.com',
    url='https://github.com/karlorg/drunken-octo-avenger',
    include_package_data=True,
    install_requires=[str(ir.req) for ir in install_reqs],
    license="CC0",
    zip_safe=False,
    keywords='Go web game',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: CC0 License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='app.tests',
)
