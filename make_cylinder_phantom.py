#!/usr/bin/env python2.4

import sys
import math

from CylinderPhantom import *

if __name__ == '__main__':
    phant = CylinderPhantom(sys.argv[1])
    phant.build()

