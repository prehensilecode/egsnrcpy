#!/usr/bin/env python
# encoding: utf-8
"""
CylinderDose.py

Created by David Chin on 2006-09-18.
Copyright (c) 2006 Brigham & Women's Hospital. All rights reserved.
"""

import sys
import os


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

