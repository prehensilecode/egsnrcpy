#!/usr/bin/env python

# $Id: setup.py 86 2007-11-12 22:11:40Z dwchin $

# Hacked from TableIO source

"""Build / install script for MCDose

See INSTALL for installation instructions.
"""

from distutils.core import setup, Extension
import sys, os

setup(name = 'egsnrc',
      version = '0.1',
      license = 'GPL',
      author = 'David Chin',
      author_email = 'david.w.h.chin@gmail.com',
      maintainer = 'David Chin',
      maintainer_email = 'david.w.h.chin@gmail.com',
      description = 'Encapsulates 3ddose and egsphant files.',
      url = 'http://www.hms.harvard.edu/',  # required to make rpm
      packages = ['egsnrc'],
      ext_package='egsnrc',
      ext_modules = [Extension('_mcdose', ['egsnrc/_mcdose.c']), \
                     Extension('_egsphant', ['egsnrc/_egsphant.c'])],
      )
