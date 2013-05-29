#!/usr/bin/env python2.4
# encoding: utf-8

# $Id: calc_cylinder_dose.py 86 2007-11-12 22:11:40Z dwchin $

import sys
import os
import math
import re

from optparse import OptionParser

import egsnrc.EGSPhant
import egsnrc.MCDose

from CylinderPhantom import *

from numarray import *

# we assume the layout is the same as for CylinderPhantom

# see notebook entry of 2006-05-15

# we want to average the dose in a chunk which has a square 
# x-y face, 2mm a side (modulo the jaggies), and of some
# extent in z. also, since we are right up against the 
# edge of the phantom, need to make sure we are only looking
# at voxels inside the phantom. i think this is easily
# taken care of by looking at the dose because we zero the
# dose in air. to be more accurate, we would need to check
# the material of the voxel in the phantom.

debug_p = True

globals_inited_p = False

# voxel dimensions
dx = 0.
dy = 0.

# radius of the cylinder
rcyl = 0.


class CylinderDose:
    def __init__(self, dosefilename):
        global dx, dy, rcyl, phant, globals_inited_p
        
        debug_print("dosefilename: %s" % dosefilename)
        
        self.dosefilename = dosefilename
        self.phantfilename = self.dosefilename.split('.')[0] + '.egsphant'
        
        # square of interest has sides of length 2 * d2
        self.d2 = 0.1   # cm
        
        debug_print("ALOHA")
        self.dose_dist = egsnrc.MCDose.MCDose(self.dosefilename)
        debug_print("FOOBAR")
        self.phant = CylinderPhantom()
        debug_print("GADZOOKS")
        self.phant.read(self.phantfilename)
        debug_print("CUBAAN")
        
        
        # globals
        dx = self.phant.dx
        dy = self.phant.dy
        rcyl = self.phant.radius
        
    
    
    def get_dose(self, angle):
        debug_print("angle: %f" % angle)
        angle *= math.pi / 180.
        
        # compute the x-y coordinates of the voxels (some extent in z)
        r0 = rcyl - self.d2  # radial distance to wanted voxel
        x0 = r0 * math.cos(angle)
        y0 = -r0 * math.sin(angle)
        
        # compute the x-y index of the voxel
        (i0, j0) = indices(x0, y0)
        
        debug_print('angle = %f rad = %f deg' % (angle, angle / math.pi * 180.))
        debug_print('r0 = %f' % r0)
        debug_print('x0 = %f' % x0)
        debug_print('y0 = %f' % y0)
        debug_print('i0 = %d' % i0)
        debug_print('j0 = %d' % j0)
        
        # q and r are as in the notes
        q = math.fabs(self.d2 * (math.cos(angle) + math.sin(angle)))
        r = math.fabs(self.d2 * (math.cos(angle) - math.sin(angle)))
        
        # the four corners of the square
        x1 = x0 + q
        y1 = y0 + r
        
        x2 = x0 - r
        y2 = y0 + q
        
        x3 = x0 - q
        y3 = y0 - r
        
        x4 = x0 + r
        y4 = y0 - q
        
        (i1, j1) = indices(x1, y1)
        (i2, j2) = indices(x2, y2)
        (i3, j3) = indices(x3, y3)
        (i4, j4) = indices(x4, y4)
        
        # centers of the 4 edges
        (xA, yA, xB, yB, xC, yC, xD, yD) = square_edge_centers(x0, y0, self.d2, angle)
        
        debug_print("In main(): (xA, yA), (xB, yB), (xC, yC), (xD, yD) = (%f, %f), (%f, %f), (%f, %f), (%f, %f)" % (xA, yA, xB, yB, xC, yC, xD, yD))
        
        # find the z-indices
        kstart = int((self.phant.phantom.zedges[-1] - self.phant.phantom.zedges[0]) / (2 * self.phant.dz)) - 2
        
        debug_print('len(zedge) = %d' % len(self.phant.phantom.zedges))
        debug_print('zedge[0] = %f' % self.phant.phantom.zedges[0])
        debug_print('zedge[-1] = %f' % self.phant.phantom.zedges[-1])
        debug_print('kstart = %d' % kstart)
        
        voxel_count = 0
        avg_dose = 0.
        mean_sigma = 0.
        for k in range(kstart, kstart + 4):
            for j in range(len(self.dose_dist.yedges) - 1):
                for i in range(len(self.dose_dist.xedges) - 1):
                    #debug_print("(k,j,i) = (%d,%d,%d)" % (k,j,i))
                    if voxel_in_phantom_and_square_p(i,j,k, self.phant, self.d2,xA, yA, xB, yB, xC, yC, xD, yD):
                        debug_print("aha! dose = %.6e; error = %2.2f%%" % (self.dose_dist.dose[k,j,i], self.dose_dist.error[k,j,i] * 100.))
                        voxel_count += 1
                        avg_dose += self.dose_dist.dose[k,j,i]
                        mean_sigma += self.dose_dist.error[k,j,i]
                        
        if voxel_count == 0:
            print >> sys.stderr, "Error: No matching voxels!"
            sys.exit(3)
            
        avg_dose /= voxel_count
        mean_sigma /= voxel_count
        
        debug_print("voxel_count = %d" % voxel_count)
        print self.dosefilename.split('.')[0] 
        print "    angle = %.2f; avg_dose = %.6e; mean_sigma = %.2f%%" % (angle*180./math.pi, avg_dose, mean_sigma * 100.)



def debug_print(arg):
    if debug_p:
        print arg


def init_globals():
    global dx, dy, rcyl, phant, globals_inited_p
    
    if not globals_inited_p:
        phant = CylinderPhantom()
        # FIXME
        phant.read('cylinder_skin_10MV_140deg.egsphant')
        dx = phant.dx
        dy = phant.dy
        rcyl = phant.radius
    
        globals_inited_p = True



def main(dosefilename, angle):
    # extracts the dose from a cylinder phantom, from a dose file 
    # 'dosefilename' at an angle 'angle'
    global dx, dy, rcyl, phant, globals_inited_p
    
    #init_globals()
    
    phantfilename = dosefilename.split('.')[0] + '.egsphant'
    
    # square of interest has sides of length 2 * d2
    d2 = 0.1
    
    # convert to radians
    angle = angle * math.pi / 180.
    
    dose_dist = egsnrc.MCDose.MCDose(dosefilename)
    phant = CylinderPhantom()
    phant.read(phantfilename)    
    dx = phant.dx
    dy = phant.dy
    rcyl = phant.radius
    
    debug_print('main: rcyl = %f\n' % rcyl)
    
    
    # compute the x-y coordinates of the voxels (some extent in z)
    r0 = rcyl - d2  # radial distance to wanted voxel
    x0 = r0 * math.cos(angle)
    y0 = -r0 * math.sin(angle)
    
    # compute the x-y index of the voxel
    (i0, j0) = indices(x0, y0)
    
    debug_print('angle = %f rad = %f deg' % (angle, angle / math.pi * 180.))
    debug_print('r0 = %f' % r0)
    debug_print('x0 = %f' % x0)
    debug_print('y0 = %f' % y0)
    debug_print('i0 = %d' % i0)
    debug_print('j0 = %d' % j0)
    
    # q and r are as in the notes
    q = math.fabs(d2 * (math.cos(angle) + math.sin(angle)))
    r = math.fabs(d2 * (math.cos(angle) - math.sin(angle)))
    
    # the four corners of the square
    x1 = x0 + q
    y1 = y0 + r
    
    x2 = x0 - r
    y2 = y0 + q
    
    x3 = x0 - q
    y3 = y0 - r
    
    x4 = x0 + r
    y4 = y0 - q
    
    (i1, j1) = indices(x1, y1)
    (i2, j2) = indices(x2, y2)
    (i3, j3) = indices(x3, y3)
    (i4, j4) = indices(x4, y4)
    
    # centers of the 4 edges
    (xA, yA, xB, yB, xC, yC, xD, yD) = square_edge_centers(x0, y0, d2, angle)
    
    debug_print("In main(): (xA, yA), (xB, yB), (xC, yC), (xD, yD) = (%f, %f), (%f, %f), (%f, %f), (%f, %f)" % (xA, yA, xB, yB, xC, yC, xD, yD))
    
    # find the z-indices
    kstart = int((phant.phantom.zedges[-1] - phant.phantom.zedges[0]) / (2 * phant.dz)) - 2
    
    debug_print('len(zedge) = %d' % len(phant.phantom.zedges))
    debug_print('zedge[0] = %f' % phant.phantom.zedges[0])
    debug_print('zedge[-1] = %f' % phant.phantom.zedges[-1])
    debug_print('kstart = %d' % kstart)
    
    voxel_count = 0
    avg_dose = 0.
    rms_error = 0.
    for k in range(kstart, kstart + 4):
        for j in range(len(dose_dist.yedges) - 1):
            for i in range(len(dose_dist.xedges) - 1):
                #debug_print("(k,j,i) = (%d,%d,%d)" % (k,j,i))
                if voxel_in_phantom_and_square_p(i,j,k,phant,d2,xA, yA, xB, yB, xC, yC, xD, yD):
                    debug_print("aha! dose = %.6e; error = %2.2f%%" % (dose_dist.dose[k,j,i], dose_dist.error[k,j,i] * 100.))
                    voxel_count += 1
                    avg_dose += dose_dist.dose[k,j,i]
                    rms_error += dose_dist.error[k,j,i]*dose_dist.error[k,j,i]
    
    if voxel_count == 0:
        print >> sys.stderr, "Error: No matching voxels!"
        sys.exit(3)
    
    avg_dose = avg_dose/voxel_count
    rms_error = math.sqrt(rms_error/voxel_count)
    
    debug_print("voxel_count = %d" % voxel_count)
    print "avg_dose = %.6e; rms error = %.2f%%" % (avg_dose, rms_error * 100.)


def position(i, j):
    """Given the indices (i, j), return the coordinates (x, y)"""
    global dx, dy, rcyl, globals_inited_p
    
    x = float(i) * dx - rcyl
    y = float(j) * dy - rcyl
    
    return (x, y)


def check_position():
    print "Check position()"
    print "----------------"
    
    print "Expect: (-10.0, -10.0)"
    print "Got:   ", position(0, 0)
    print "Expect: (0.0, 0.0)"
    print "Got:   ", position(200, 200)


def indices(x, y):
    """Given the coordinates (x, y), return the indices (i, j)"""
    global dx, dy, rcyl, globals_inited_p
    
    debug_print('x = %f; rcyl = %f; dx = %f\n' % (x, rcyl, dx))
    i = int((x + rcyl) / dx)
    j = int((y + rcyl) / dy)
    
    return (i, j)


def check_indices():
    print "Check indices()"
    print "---------------"
    
    print "Expect: (0, 0)"
    print "Got:   ", indices(-10., -10.)
    
    print "Expect: (100, 0)"
    print "Got:   ", indices(-5., -10.)
    
    print "Expect: (0, 100)"
    print "Got:   ", indices(-10., -5.)


def determinant_2d(x1, y1, x2, y2):
    """Gives the determinant"""
    return math.fabs(x1 * y2 - x2 * y1)


def distance_2d(x1, y1, x2, y2):
    """Distance between 2 points"""
    return math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))

 
def point_line_distance_2d(x0, y0, x1, y1, x2, y2):
    """Gives the distance from the point (x0, y0) to the line defined
    by the two points (x1, y1) and (x2, y2)"""
    num = determinant_2d((x2-x1), (y2-y1), (x1-x0), (y1-y0))
    den = distance_2d(x1, y1, x2, y2)
    # debug_print "point_line_distance_2d: %.12e" % (num/den)
    return num/den


def check_point_line_distance_2d():
    print "Check distance of point to line"
    print "-------------------------------"
    # distances from x-axis
    (x1, y1) = (0., 0.)
    (x2, y2) = (4., 0.)
    (x, y) = (2., 2.)
    print "distance = %.4f ; expected = %.4f" % (point_line_distance_2d(x, y, x1, y1, x2, y2), 2.)
    (x1, y1) = (-2, 0.)
    (x2, y2) = (-8., 0.)
    (x, y) = (2., 3.)
    print "distance = %.4f ; expected = %.4f" % (point_line_distance_2d(x, y, x1, y1, x2, y2), 3.)
    
    # distances from y-axis
    (x1, y1) = (0., 0.)
    (x2, y2) = (0., 4.)
    (x, y) = (2., 2.)
    print "distance = %.4f ; expected = %.4f" % (point_line_distance_2d(x, y, x1, y1, x2, y2), 2.)
    (x1, y1) = (0., -2.)
    (x2, y2) = (0., -8.)
    (x, y) = (3., 2.)
    print "distance = %.4f ; expected = %.4f" % (point_line_distance_2d(x, y, x1, y1, x2, y2), 3.)
    
    (x1, y1) = (0., 0.)
    (x2, y2) = (4., 3.)
    (x, y) = (-3., 4.)
    print "distance = %.4f ; expected = %.4f" % (point_line_distance_2d(x, y, x1, y1, x2, y2), 5.)


def square_edge_centers(x0, y0, d2, angle):
    """Given the center of the square (x0, y0), the half-width of
    the square (d2), and the rotation angle in radians, return the coordinates of 
    the four edge-centers (in counterclockwise direction)"""
    # centers of the 4 edges. 
    dc = d2 * math.cos(angle)
    ds = d2 * math.sin(angle)
    
    xA = x0 + ds
    yA = y0 + dc
    
    xB = x0 - dc
    yB = y0 + ds
    
    xC = x0 - ds
    yC = y0 - dc
    
    xD = x0 + dc
    yD = y0 - ds
    
    return (xA, yA, xB, yB, xC, yC, xD, yD)


def check_square_edge_centers():
    print "Check for finding the centers of the edges"
    print "------------------------------------------"
    
    # center of square
    (x0, y0) = (2., 2.)
    
    # half the side of square
    d2 = 1.
    
    # angle about center of square by which it is rotated
    angle = 0.
     
    # centers of the 4 edges. 
    dc = d2 * math.cos(angle)
    ds = d2 * math.sin(angle)
    
    xA = x0 + ds
    yA = y0 + dc
    
    xB = x0 - dc
    yB = y0 + ds
    
    xC = x0 - ds
    yC = y0 - dc
    
    xD = x0 + dc
    yD = y0 - ds
    
    print "Center, d2, angle: (%.4f, %.4f), %.1f, %.5f" % (x0, y0, d2, angle)
    print "  Expect:"
    print "    ", (2., 3.), (1., 2.), (2., 1.), (3., 2.)
    print ""
    
    print "  Manual calc:"
    print "    ", (xA, yA), (xB, yB), (xC, yC), (xD, yD)
    print ""
    
    (xA, yA, xB, yB, xC, yC, xD, yD) = square_edge_centers(x0, y0, d2, angle)
    print "  Using square_edge_centers:"
    print "    ", (xA, yA), (xB, yB), (xC, yC), (xD, yD)
    
    print ""
    angle = 45. * math.pi / 180.
    d2 = 1. / math.sqrt(2.)
    print "Center, d2, angle: (%.4f, %.4f), %.1f, %.5f" % (x0, y0, d2, angle/math.pi * 180.)
    (xA, yA, xB, yB, xC, yC, xD, yD) = square_edge_centers(x0, y0, d2, angle)
    print "  Expect:"
    print "    ", (2.5, 2.5), (1.5, 2.5), (1.5, 1.5), (2.5, 1.5)
    print ""
    print "  Using square_edge_centers:"
    print "    ", (xA, yA), (xB, yB), (xC, yC), (xD, yD)
    
    print ""
    angle = 30. * math.pi / 180.
    d2 = 1.
    print "Center, d2, angle: (%.4f, %.4f), %.1f, %.5f" % (x0, y0, d2, angle/math.pi * 180.)
    (xA, yA, xB, yB, xC, yC, xD, yD) = square_edge_centers(x0, y0, d2, angle)
    print "  Expect:"
    print "    ", (x0 + math.sin(angle), y0 + math.cos(angle)), (x0 - math.cos(angle), y0 + math.sin(angle)), (x0 - math.sin(angle), y0 - math.cos(angle)), (x0 + math.cos(angle), y0 - math.sin(angle))
    print ""
    print "  Using square_edge_centers:"
    print "    ", (xA, yA), (xB, yB), (xC, yC), (xD, yD)
    


def in_square_p(x, y, d2, xA, yA, xB, yB, xC, yC, xD, yD):
    """The (x, y) inside the square which has edge centers (xA, yA)
       (xB, yB), (xC, yC), ond (xD, yD). Points 1 and 3 are opposite
       each other, and points 2 and 4 are opposite each other."""
       
    # (x, y) is inside the square if its distances from the line 13
    # and from the line 24 are less than d/2
      
    return ((point_line_distance_2d(x, y, xA, yA, xC, yC) < d2) and \
        (point_line_distance_2d(x, y, xB, yB, xD, yD) < d2))


def check_in_square():
    print "Check for in-square"
    print "-------------------"
    
    # center of square
    (x0, y0) = (2., 2.)
    
    # half the side of square
    d2 = 1.
    
    # angle about center of square by which it is rotated
    angle = 0.
        
    # centers of the 4 edges. 
    (xA, yA, xB, yB, xC, yC, xD, yD) = square_edge_centers(x0, y0, d2, angle)
    # so, expect (2, 1), (1,2), (2,3), (3,2)
    print "Edge centers:", (xA, yA), (xB, yB), (xC, yC), (xD, yD)
    
    print "(2., 2.) Expect: True; Got:", in_square_p(2., 2., d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print "(1., 2.) Expect: False; Got:", in_square_p(1., 2., d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print "(2.5, 2.5) Expect: True; Got:", in_square_p(2.5, 2.5, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    
    # angle about center of square by which it is rotated
    angle = 45. * math.pi / 180.
    d2 = 1. / math.sqrt(2.)
    # centers of the 4 edges. 
    (xA, yA, xB, yB, xC, yC, xD, yD) = square_edge_centers(x0, y0, d2, angle)
    # so, expect (2.5, 2.5), (1.5, 2.5), (1.5, 1.5), (2.5, 1.5)
    print "Edge centers: (%.3f, %.3f), (%.3f, %.3f), (%.3f, %.3f), (%.3f, %.3f)" % (xA, yA, xB, yB, xC, yC, xD, yD)
    
    print "(2., 1.1) Expect: True; Got:", in_square_p(2., 1.1, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print "(2., 3.1) Expect: False; Got:", in_square_p(2., 3.1, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print "(3., 2.) Expect: False; Got:", in_square_p(3., 2., d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print "(2.9, 2.) Expect: True; Got:", in_square_p(2.9, 2., d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print "(2.5, 2.5) Expect: False; Got:", in_square_p(2.5, 2.5, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print "(2.4, 2.5) Expect: True; Got:", in_square_p(2.4, 2.5, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    


def voxel_in_square_p(i, j, d2, xA, yA, xB, yB, xC, yC, xD, yD):
    """Predicate: voxel with indices (i, j) is in desired square"""
    (x, y) = position(i, j)
    return in_square_p(x, y, d2, xA, yA, xB, yB, xC, yC, xD, yD)


def check_voxel_in_square():
    print "Check voxel_in_square_p()"
    print "-------------------------"
    
    # center of square
    (x0, y0) = (0., 0.)
    
    # half the side of square: 2 voxels
    d2 = 0.1
    
    # angle about center of square by which it is rotated
    angle = 0.
    
    (xA, yA, xB, yB, xC, yC, xD, yD) = square_edge_centers(x0, y0, d2, angle)
    
    print "Square corners: (%.12e, %.12e), (%.12e, %.12e), (%.12e, %.12e), (%.12e, %.12e)" % (xA, yA, xB, yB, xC, yC, xD, yD)
    print "d2 = %.12e" % (d2)
    print " "
    
    (xx, yy) = (200, 200)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: True"    
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    
    (xx, yy) = (201, 199)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: True"
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    
    (xx, yy) = (199, 201)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: True"
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    
    (xx, yy) = (202, 200)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: False"
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    
    (xx, yy) = (200, 202)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: False"
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    
    (xx, yy) = (200, 198)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: False"
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    
    (xx, yy) = (198, 200)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: False"
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    
    (xx, yy) = (200, 197)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: False"
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    
    (xx, yy) = (197, 200)
    print "Given: (%.12e, %.12e)" % position(xx, yy)
    print "Expect: False"
    print "Got:   ", voxel_in_square_p(xx, yy, d2, xA, yA, xB, yB, xC, yC, xD, yD)
    print " "
    



def voxel_in_phantom_p(i, j, k, phantom):
    """Predicate: voxel is in the phantom"""
    
    # merely checks that the material of the voxel is water
    return (phantom.phantom.material(phantom.phantom.materialscan[k, j, i]) == 'H2O700ICRU')


def check_voxel_in_phantom():
    global phant, globals_inited_p
    print "Check voxel_in_phantom_p()"
    print "--------------------------"
    
    print "(0,0,0) is in phantom?", voxel_in_phantom_p(0, 0, 0, phant)
    print "               Expect: False"
    
    print "(200,160,0) is in phantom?", voxel_in_phantom_p(200, 160, 0, phant)
    print "               Expect: True"


def voxel_in_phantom_and_square_p(i, j, k, phantom, d2, xA, yA, xB, yB, xC, yC, xD, yD):
    """Predicate: voxel is in the phantom and in the desired square"""
    return (voxel_in_square_p(i, j, d2, xA, yA, xB, yB, xC, yC, xD, yD) and voxel_in_phantom_p(i, j, k, phantom))



def usage():
    print "calc_cylinder_dose.py dosefile angle"



if __name__ == '__main__':
    #if len(sys.argv) == 1:
        dosefile = sys.argv[1]
        if not dosefile.split('.')[-1] == '3ddose':
            dosefile = dosefile + '.3ddose'
        
        debug_print("Testing %s" % sys.argv[0].split('/')[-1])
        debug_print("dosefile = %s" % dosefile)
        # main(sys.argv[1], 20.)
        
        cyldose = CylinderDose(dosefile)
                
        cyldose.get_dose(0.)
        cyldose.get_dose(10.)
        cyldose.get_dose(20.)
        cyldose.get_dose(30.)
        cyldose.get_dose(40.)
        cyldose.get_dose(50.)
        cyldose.get_dose(60.)
        cyldose.get_dose(70.)
        cyldose.get_dose(80.)
        
    # elif len(sys.argv) == 1:
    #     dosefile = sys.argv[1]
    #     print "Testing %s" % sys.argv[0].split('/')[-1]
    #     print "dosefile = %s" % dosefile
    #     # main('foobar.3ddose', 0.)
    #     # print "-----"
    #     # main('foobar.3ddose', 30.)
    #     # print "-----"
    #     # main('foobar.3ddose', 45.)
    #     # print "-----"
    #     # main('foobar.3ddose', 60.)
    #     # print "-----"
    #     # main('foobar.3ddose', 90.)
    #     # print "-----"
    #     # main('foobar.3ddose', 180.)
    #     # print "\n"
    #     #main('cylinder_skin_10MV_140deg', 0.)
    #     # sys.exit(0)
    #     # main()
    #     # init_globals()
    #     # check_position()
    #     # print "\n"
    #     # check_indices()
    #     # print "\n"
    #     # check_point_line_distance_2d()
    #     # print "\n"
    #     # check_square_edge_centers()
    #     # print "\n"
    #     # check_in_square()
    #     # print "\n"
    #     # check_voxel_in_square()
    #     # print "\n"
    #     # check_voxel_in_phantom()
    # else:
    #     usage()
    #     sys.exit(1)
