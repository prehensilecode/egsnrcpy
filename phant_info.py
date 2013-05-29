#!/usr/bin/env python
# encoding: utf-8
"""
phant_info.py

Created by David Chin on 2006-07-11.
Copyright (c) 2006 Brigham & Women's Hospital. All rights reserved.
"""

import sys
from egsnrc.EGSPhant import *

if len(sys.argv) == 1:
    print "Need one argument, name of phantom file to fix"
else:
    try:
        phant = EGSPhant(sys.argv[1])
    except IOError:
        raise
    
    phant.print_info()
    
