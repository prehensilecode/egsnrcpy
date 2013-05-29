#!/usr/bin/env python2.4

# $Id: pickle_these.py 86 2007-11-12 22:11:40Z dwchin $

import os
import pickle

from EGSPhant import *
from MCDose import *

# loop over all egsphant and 3ddose file, and pickle them

for o in sys.argv:
    if o.endswith('3ddose'):
        d = MCDose(o)
        picklename = o.split('.3ddose')[0] + '_3ddose.pickle'
        f = open(picklename, 'wo')
        pickle.dump(d, f)
        f.close()
    elif o.endswith('egsphant'):
        p = EGSPhant(o)
        picklename = o.split('.egsphant')[0] + '_egsphant.pickle'
        f = open(picklename, 'wo')
        pickle.dump(p, f)
        f.close()
    else:
        pass

