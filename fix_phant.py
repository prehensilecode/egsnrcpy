#!/usr/bin/env python2.4

import sys

from EGSPhant import *


if len(sys.argv) == 1:
    print "Need one argument, name of phantom file to fix"
else:
    try:
        phant = EGSPhant(sys.argv[1])
    except IOError:
        raise
    
    suffix = '.egsphant'
    phant.fix_density()
    basename = sys.argv[1].split(suffix)[0]
    newname = basename + '_fixed' + suffix
    phant.save(newname)

