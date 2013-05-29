#!/usr/bin/env python

# $Id: MCDose.py 186 2008-04-23 17:09:27Z dwchin $

from __future__ import division

import sys
import scanf
import pickle

import _mcdose

### TODO: convert to numpy
# from numarray import *
#from numpy import *
import numpy as np

from Scientific import Statistics
#import mayavi
#from mayavi.tools import imv
#import pyvtk

# A note on coordinate systems.  FIXME
#
# The 3ddose file format is defined in:
#    http://www.irs.inms.nrc.ca/BEAM/user_manuals/statdose/node12.html
#
# Say the patient is lying supine (face up). Look at the top (crown)
# of the patient's head, sighting along the length of the body.
# Or are we looking at the feet?
# So, the axes are: blablabla


class MCDose:
    """A class encapsulating dose output of DOSXYZnrc"""
    
    # debug flag
    debug_p = False

    __version = "$Revision: 186 $"
    
    def __init__(self, dosefilename=None):
        if dosefilename:
            self.dosefilename = dosefilename
            self.read(self.dosefilename)
    
    
    def __dict_to_mcdose(self, d):
        self.dimensions = d['dimensions']
        
        print "dimensions: ", self.dimensions
        
        print "len(d['xedges']): ", len(d['xedges'])
        print "len(d['dose']): ", len(d['dose'])
        
        
        self.xedges = np.array(d['xedges'], order='c', dtype=float)
        self.yedges = np.array(d['yedges'], order='c', dtype=float)
        self.zedges = np.array(d['zedges'], order='c', dtype=float)
        
        # the data is sorted in "reverse", i.e. the indices are 
        # [z,y,x]
        self.dose = np.array(d['dose'], order='c', dtype=float)
        self.dose = self.dose.reshape(self.dimensions[2], self.dimensions[1],
                                      self.dimensions[0], order='c')
        
        self.error = np.array(d['error'], order='c', dtype=float)
        self.error = self.error.reshape(self.dimensions[2], self.dimensions[1],
                                        self.dimensions[0], order='c')
    
    
    def read(self, dosefilename):
        d = _mcdose.read(dosefilename)
        self.__dict_to_mcdose(d)
    
    
    # def read(self, dosefilename):
    #     self.dosefilename = dosefilename
    #     
    #     try:
    #         f = open(self.dosefilename, "ro")
    #         
    #         try:
    #             # read in dimensions
    #             self.dimensions = scanf.fscanf(f, "%d %d %d")
    #             self.xedges = zeros(self.dimensions[0]+1, type=Float32)
    #             self.yedges = zeros(self.dimensions[1]+1, type=Float32)
    #             self.zedges = zeros(self.dimensions[2]+1, type=Float32)
    #             
    #             # read in x-edges
    #             formatstr = ""
    #             for i in range(self.dimensions[0]+1):
    #                 formatstr = formatstr + "%f "
    #             self.xedges = array(scanf.fscanf(f, formatstr))
    #             
    #             self.__debug_print(self.xedges)
    #             
    #             # read in y-edges
    #             formatstr = ""
    #             for i in range(self.dimensions[1]+1):
    #                 formatstr = formatstr + "%f "
    #             self.yedges = array(scanf.fscanf(f, formatstr))
    #             
    #             self.__debug_print(self.yedges)
    #             
    #             # read in z-edges
    #             formatstr = ""
    #             for i in range(self.dimensions[2]+1):
    #                 formatstr = formatstr + "%f "
    #             self.zedges = array(scanf.fscanf(f, formatstr))
    #             
    #             self.__debug_print(self.zedges)
    #             
    #             self.__debug_print(self.dimensions)
    #             
    #             # convert voxel edges to voxel centers and store
    #             self.__edges_to_centers()
    #     
    #             
    #             # NB: a 3D array is made up of a stack of slices, each
    #             #     slice being a matrix
    #             #     the index order is z,y,x where x is column index,
    #             #     y is row index, and z is slice index
    #     
    #             
    #             # read in doses
    #             self.dose = zeros([self.dimensions[2],self.dimensions[1],
    #                               self.dimensions[0]], type=Float32)
    #             formatstr = ""
    #             for i in range(self.dimensions[0]):
    #                 formatstr = formatstr + "%f "
    #             
    #             for k in range(self.dimensions[2]):
    #                 for j in range(self.dimensions[1]):
    #                     self.dose[k,j,:] = array(scanf.fscanf(f, formatstr))
    #             
    #             # read in errors, if any
    #             # FIXME -- how to deal with files with no error?
    #             self.error = zeros([self.dimensions[2],self.dimensions[1],
    #                                self.dimensions[0]], type=Float32)
    #             formatstr = ""
    #             for i in range(self.dimensions[0]):
    #                 formatstr = formatstr + "%f "
    #             
    #             for k in range(self.dimensions[2]):
    #                 for j in range(self.dimensions[1]):
    #                     self.error[k,j,:] = array(scanf.fscanf(f, formatstr))
    #         
    #         finally:
    #             f.close()
    #     
    #     except IOError:
    #         print "%s: error opening file %s" % (sys.argv[0], dosefile)
    #         raise IOError
    
    
    def save(self, filename):
        """Write to a 3ddose file"""
        try:
            f = open(filename, 'w')
            
            try:
                # dimensions
                for d in self.dimensions:
                    f.write('% 12d' %d)
                f.write('\n')
                
                # lists of edges are written out in
                # chunks 5 numbers wide
                float_width = 5
                
                # x-edges
                for i in range(len(self.xedges)):
                    f.write('  % .6f    ' % self.xedges[i])
                    if not (i+1) % float_width:
                        f.write('\n')
                f.write('\n')
                
                # y-edges
                for i in range(len(self.yedges)):
                    f.write('  % .6f    ' % self.yedges[i])
                    if not (i+1) % float_width:
                        f.write('\n')
                f.write('\n')
                
                # z-edges
                for i in range(len(self.zedges)):
                    f.write('  % .6f    ' % self.zedges[i])
                    if not (i+1) % float_width:
                        f.write('\n')
                f.write('\n')
                
                # doses and dose errors are written out
                # in chunks of 3 numbers wide
                float_width = 3
                
                # doses
                for k in range(self.dimensions[2]):
                    for j in range(self.dimensions[1]):
                        for i in range(self.dimensions[0]):
                            f.write('  % .16f    ' % self.dose[k,j,i])
                            if not (i+1) % float_width:
                                f.write('\n')
                        f.write('\n')
                    f.write('\n')
                
                # errors
                for k in range(self.dimensions[2]):
                    for j in range(self.dimensions[1]):
                        for i in range(self.dimensions[0]):
                            f.write('  % .16f    ' % self.error[k,j,i])
                            if not (i+1) % float_width:
                                f.write('\n')
                        f.write('\n')
                    f.write('\n')
            
            finally:
                f.close()
        
        except IOError:
            print "%s: error opening file %s" % (sys.argv[0], filename)
            raise IOError
    
    def pickle(self, pickle_filename=None):
        """Pickles to a file"""
        
        if not pickle_filename:
            self.picklefilename = self.dosefilename.split(".3ddose")[0] + "_3ddose.pickle"
        else:
            self.picklefilename = pickle_filename
        
        try:
            pf = open(self.picklefilename, "wo")
            pickle.dump(self, pf)
        finally:
            pf.close()
    
    def unpickle(self, pickle_filename):
        """Unpickles from file pickle_filename"""
        try:
            pf = open(pickle_filename, "ro")
            self = pickle.load(pf)
        finally:
            pf.close()
    
    def make_absolute(self, energy, mu):
        """Converts the per particle dose to absolute dose.
           Takes two arguments:
             - a string which can be one of two values, '6MV' or '10MV'
             - the number of MUs"""
        
        # Scaling factors for deriving absolute dose.
        # Multiply the 3ddose values (which are per primary
        # history) with this value. Result is dose in Gy.
        # NB: these factors are dependent on the specific
        #     phase space file that is used to calculate dose
        scalefactor = { '6MV' : 8.1027e+13,
                        '10MV' : 2.4125e+13 }
        if (energy == '6MV' or energy == '10MV') and mu > 0:
            self.dose *= scalefactor[energy] * mu
    
    def make_relative(self, ref=0):
        """Converts the dose to relative dose (percentage), normalized against
           the given ref value. Takes one argument:
             - reference dose value to normalize against"""
        if ref == 0:
            ref = self.dose.max()
        
        # for k in range(self.dimensions[2]):
        #     for j in range(self.dimensions[1]):
        #         for i in range(self.dimensions[0]):
        #             self.dose[k,j,i] /= ref / 100.
                    
        self.dose /= ref / 100.
    
    def scale(self, factor):
        """Multiplies dose values by given factor. (Replaces the 'scale' executable by jssong.)"""
        self.dose *= factor
    
    def max_dose(self):
        """Returns the maximum dose"""
        return self.dose.max()
    
    def __edges_to_centers(self):
        """Convert the list of voxel edges to voxel centers"""
        self.x = np.zeros(self.dimensions[0], order='c', dtype=float)
        self.y = np.zeros(self.dimensions[1], order='c', dtype=float)
        self.z = np.zeros(self.dimensions[2], order='c', dtype=float)
        
        # x
        for i in range(len(self.xedges)-1):
            self.x[i] = (self.xedges[i] + self.xedges[i+1])/2.
        
        # y
        for i in range(len(self.yedges)-1):
            self.y[i] = (self.yedges[i] + self.yedges[i+1])/2.
        
        # z
        for i in range(len(self.zedges)-1):
            self.z[i] = (self.zedges[i] + self.zedges[i+1])/2.
    
    def __debug_print(self, o):
        """Print given object if debug flag is non-zero"""
        if self.debug_p:
            print o
    

if __name__ == "__main__":
    dose = MCDose(sys.argv[1])
    print dose.dimensions
    print dose.xedges
    print dose.xedges.getshape()
    print dose.yedges
    print dose.yedges.getshape()
    print dose.zedges
    print shape(dose.zedges)
    print dose.dose[0][1][2]
    print dose.dose.getshape()
    
    #v1 = imv.view(dose.dose[20,:,:])
