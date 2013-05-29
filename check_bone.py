#!/usr/bin/env python2.4

from EGSPhant import *

if len(sys.argv) == 1:
    print 'Need name of egsphant file'
    sys.exit(1)

p = EGSPhant(sys.argv[1])

# set the density for tissue and bone voxels 
for k in range(p.dimensions[2]):
    for j in range(p.dimensions[1]):
        for i in range(p.dimensions[0]):
            mat = p.material(p.materialscan[k,j,i])
            if mat == 'ICRPBONE700ICRU':
                print '%s, %f g/cc' % (mat, p.densityscan[k,j,i])

