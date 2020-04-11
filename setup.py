#!/usr/bin/env python3
"""
Tabletop Games GUI Support
"""
# SPDX-License-Identifier: GPL-3.0
import sys
if sys.version_info < (3,6):
    raise Exception("Python 3.6 required -- this is only " + sys.version)

import re
import setuptools
import unittest

__version__ = re.search(r'(?m)^__version__\s*=\s*"([\d.]+(?:[\-\+~.]\w+)*)"', open('amethyst/ttkvlib/__init__.py').read()).group(1)

def my_test_suite():
    return unittest.TestLoader().discover('tests', pattern='test_*.py')

setuptools.setup(
    name         = 'amethyst-ttkvlib',
    version      = __version__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        ],
    url          = 'https://github.com/duelafn/python-amethyst-ttkvlib',
    author       = 'Dean Serenevy',
    author_email = 'dean@serenevy.net',
    description  = 'Tabletop Games GUI Support',
    packages     = setuptools.find_packages(),
    requires     = [
        'amethyst.core (>=0.8.6)',
        'amethyst.games',
        'kivy (>=1.10)',
    ],
    python_requires = '>=3.6',
    namespace_packages = [ 'amethyst' ],
    test_suite   = 'setup.my_test_suite',
)
