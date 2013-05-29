#!/usr/bin/env python2.4

# $Id: fix_phantom_tissue.py 86 2007-11-12 22:11:40Z dwchin $

from egsnrc.EGSPhant import *

if len(sys.argv) == 1:
    print 'Need name of egsphant file'
    sys.exit(1)

p = EGSPhant(sys.argv[1])

# set the density for tissue and bone voxels 
for k in range(p.dimensions[2]):
    for j in range(p.dimensions[1]):
        for i in range(p.dimensions[0]):
            mat = p.material(p.materialscan[k,j,i])
            if mat == 'ICRUTISSUE700ICRU':
                proper_dens = 1.0
                p.densityscan[k,j,i] = proper_dens
            elif mat == 'ICRPBONE700ICRU': # set to mid-range value
                proper_dens = 0.5 * (p.density[mat][0] + p.density[mat][1])
                p.densityscan[k,j,i] = proper_dens

new_filename = p.phantfilename.split('.egsphant')[0] + '_fixed.egsphant'
p.save(new_filename)

