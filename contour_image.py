#!/usr/bin/env python2.4

# $Id: contour_image.py 86 2007-11-12 22:11:40Z dwchin $

from __future__ import division

import sys
import pickle

from pylab import *
from EGSPhant import *
from MCDose import *


# Convenience functions to unpickle 3ddose and egsphant files,
# and to make isodose contour plots

def unpickle_dose(dosefilename):
    df = open(dosefilename, 'ro')
    d = pickle.load(df)
    df.close()
    return d


def unpickle_phant(phantfilename):
    pf = open(phantfilename, 'ro')
    p = pickle.load(pf)
    pf.close()
    return p


# These plotting routines take a normalization object so
# that the greyscale plot of the phantoms will have the 
# same range if one plots different phantoms.
# Let's say there are 2 3ddose files each with a corresponding
# phantom. The phantoms may have a different set of materials.
# The normalization object is created by, for example:
#
#    phanta = EGSPhant('foo.egsphant')
#    phantb = EGSPhant('bar.egsphant')
#    dosea = MCDose('foo.3ddose')
#    doseb = MCDose('bar.3ddose')
#    # set the lower end of the scale to be 0
#    norm_scale = pylab.normalize(0, max(phanta.densityscan.max(), phantb.densityscan.max()))
#    xy_plot(phanta, dosea, 13, 'foo', norm_scale)
#    xy_plot(phantb, doseb, 13, 'bar', norm_scale)



def xy_plot(phant,dose,slice,titlestr,norm):
    figure()

    extent = phant.extent()[0:4]
    im = imshow(phant.densityscan[slice,:,:], 
                interpolation='nearest', extent=extent,
                cmap=cm.bone, origin='lower', norm=norm)

    v = axis()
    x, y = meshgrid(phant.x, phant.y)
    
    levels = arange(0, dose.dose.max(), dose.dose.max()/15.)
    cset = contour(x,y,dose.dose[slice,:,:], levels, cmap=cm.jet, 
                   extent=extent, hold='on', origin='image')

    for c in cset.collections:
        c.set_linestyle('solid')

    #clabel(cset, fontsize=12, inline=1)

    colorbar(cset)

    axis(v)

    newtitlestr = '%s (z = %.2f cm)' % (titlestr, phant.z[slice])
    title(newtitlestr)

    xlabel('x (cm)')
    ylabel('y (cm)')

    ylim = get(gca(), 'ylim')
    setp(gca(), ylim=ylim[::-1])

    savefig(titlestr + '_xy')

    show()


def xz_plot(phant,dose,slice,titlestr,norm):
    figure()

    maxz = 3.5
    for i_maxz in range(len(phant.z)):
        if phant.z[i_maxz] < maxz:
            pass
        else:
            break

    extent = (phant.x[0], phant.x[-1], phant.z[0], phant.z[i_maxz])
    im = imshow(phant.densityscan[:i_maxz,slice,:], 
                interpolation='nearest', extent=extent,
                cmap=cm.bone, origin='lower', norm=norm)

    v = axis()

    x, z = meshgrid(phant.x, phant.z[:i_maxz])
    
    levels = arange(0., dose.dose.max(), dose.dose.max()/15.)
    cset = contour(x,z,dose.dose[:i_maxz,slice,:], levels, cmap=cm.jet, 
                   extent=extent, hold='on', origin='image')

    for c in cset.collections:
        c.set_linestyle('solid')

    #clabel(cset, fontsize=12, inline=1)

    colorbar(cset)

    axis(v)

    ylim = get(gca(), 'ylim')
    setp(gca(), ylim=ylim[::-1])

    newtitlestr = '%s (y = %.2f cm)' % (titlestr, phant.y[slice])

    title(newtitlestr)
    xlabel('x (cm)')
    ylabel('z (cm)')
    savefig(titlestr + '_xz')
    show()



def yz_plot(phant,dose,slice,titlestr,norm):
    figure()

    maxz = 3.5
    for i_maxz in range(len(phant.z)):
        if phant.z[i_maxz] < maxz:
            pass
        else:
            break

    extent = (phant.y[0], phant.y[-1], phant.z[0], phant.z[i_maxz])
    im = imshow(phant.densityscan[:i_maxz,:,slice], 
                interpolation='nearest', extent=extent,
                cmap=cm.bone, origin='lower', norm=norm)

    v = axis()
    y, z = meshgrid(phant.y, phant.z[:i_maxz])
    
    levels = arange(0, dose.dose.max(), dose.dose.max()/15.)
    cset = contour(y,z,dose.dose[:i_maxz,:,slice], levels, cmap=cm.jet, 
                   extent=extent, hold='on', origin='image')

    for c in cset.collections:
        c.set_linestyle('solid')

    #clabel(cset, fontsize=8)

    colorbar(cset)

    axis(v)
    ylim = get(gca(), 'ylim')
    setp(gca(), ylim=ylim[::-1])

    newtitlestr = '%s (x = %.2f cm)' % (titlestr, phant.x[slice])

    title(newtitlestr)

    xlabel('y (cm)')
    ylabel('z (cm)')

    savefig(titlestr + '_yz')
    show()

