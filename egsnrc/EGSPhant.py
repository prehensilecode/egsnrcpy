#!/usr/bin/env python

# $Id: EGSPhant.py 186 2008-04-23 17:09:27Z dwchin $

from __future__ import division

import sys
import scanf
import pickle

import _egsphant

### TODO: convert to numpy
# from numarray import *
import numpy as np

#from Scientific import Statistics
#import mayavi
#from mayavi.tools import imv
#import pyvtk

# The egsphant file format is documented here:
#   http://www.irs.inms.nrc.ca/BEAM/user_manuals/pirs794/node95.html

class EGSPhant:
    """A class encapsulating an EGS phantom file"""
    
    # Debug flag
    debug_p = False

    # version string
    __version = "$Revision: 186 $"
    
    #
    # Dictionary of material densities which we will encounter
    # when dealing with EGS phantoms. Data comes from
    # ctcreate.mortran, and the pegs4inp files on
    # jvneumann in ~dwchin/egsnrc05/pegs4/inputs.
    # The artificial materials have a fixed
    # density, unlike the bone and tissue, and air.
    # Each material has a range of densities, and here we
    # list the extremes of their ranges. Units are g/cm^3
    #
    # See http://kalos.partners.org/RadOncWiki/index.php?title=Dental_implants#Material_Data for sources
    density = { 'AIR700ICRU' : (0.001, 0.044),
                'LUNG700ICRU' : (0.044, 0.302),
                'ICRUTISSUE700ICRU' : (0.302, 1.101),
                'ICRPBONE700ICRU' : (1.101, 2.088),
                'AU700ICRU' : (19.32, 19.32),
                'DENTALAMALGAM' : (8.0, 8.0),
                'PEMA' : (1.119, 1.119),
                'VITALLIUMASTMF90' : (8.3, 8.3) ,
                'MIRACAST' : (11.8, 11.8),
                'ECLIPSE' : (13.8, 13.8),
                'CERAMCOC3' : (2.4, 2.8),
                'H2O700ICRU' : (1.0, 1.0) }
    
    
    def __init__(self, phantfilename=None, xdim=0, ydim=0, zdim=0):
        """Basic init method, with optional file name argument"""
        
        if phantfilename:
            self.phantfilename = phantfilename
            
            self.__debug_print("CUBAAN: %s" % self.phantfilename)
            
            self.read(self.phantfilename)
            # self.edges_to_centers()
        else:
            if (xdim > 0) and (ydim > 0) and (zdim > 0):
                self.dimensions = (xdim, ydim, zdim)
    
    def __dict_to_egsphant(self, d):
        """Convert the dictionary returned by _egsphant.read to member attributes"""
        
        self.__debug_print("CUBAAN: converting _egsphant dictionary")
        
        self.nmaterials = d['nmaterials']
        self.materials = d['materials']
        self.estepe = d['estepe']
        self.dimensions = d['dimensions']
        
        self.xedges = np.array(d['xedges'], order='C', dtype=float)
        self.yedges = np.array(d['yedges'], order='C', dtype=float)
        self.zedges = np.array(d['zedges'], order='C', dtype=float)
        
        self.x = np.array(d['x'], order='C', dtype=float)
        self.y = np.array(d['y'], order='C', dtype=float)
        self.z = np.array(d['z'], order='C', dtype=float)
        
        self.materialscan = np.array(d['materialscan'], order='C', dtype=int)
        self.materialscan = self.materialscan.reshape(self.dimensions[2],
                                                      self.dimensions[1],
                                                      self.dimensions[0],
                                                      order='C')
        
        self.densityscan = np.array(d['densityscan'], order='C', dtype=float)
        self.densityscan = self.densityscan.reshape(self.dimensions[2],
                                                    self.dimensions[1],
                                                    self.dimensions[0],
                                                    order='C')
    
    
    def material(self, i):
        """Given integer, return material"""
        return self.materials[i-1]
    
        
    def __density_correct_p(self, k, j, i):
        """Is the density at voxel [k,j,i] within the appropriate range?"""
        
        # material name at given voxel
        mat = self.material(self.materialscan[k,j,i])
        
        # material density range
        denslow = self.density[mat][0]
        denshi  = self.density[mat][1]
        
        # density at given voxel listed in phantom
        dens = self.densityscan[k,j,i]
        
        return (dens >= denslow and dens <= denshi)   
    
    
    #
    # Fix the density map.
    # The egsphant file may have been manually edited to
    # "insert" things like dental fillings, etc. While it
    # is straightforward to see the position of the voxel
    # to be changed in the material map, the density map
    # is not laid out in a spatial grid like the material
    # map. This function scans each voxel, and if the
    # voxel's density does not lie within the range of the
    # material, the density is modified. Set the density to
    # the lower of the range. Correction is done only for
    # dental implant materials
    #
    def fix_density(self):
        """Fix the density map for dental restoration materials:
           material type and density are inconsistent"""
        for k in range(self.dimensions[2]):
            for j in range(self.dimensions[1]):
                for i in range(self.dimensions[0]):
                    mat = self.material(self.materialscan[k,j,i])
                    if mat == 'AU700ICRU' or mat == 'DENTALAMALGAM' or mat == 'PEMA' or mat == 'VITALLIUMASTMF90' or mat == 'MIRACAST' or mat == 'ECLIPSE' or mat == 'CERAMCOC3':
                        if not self.__density_correct_p(k,j,i):
                            mat = self.material(self.materialscan[k,j,i])
                            self.__debug_print(mat)
                            proper_dens = self.density[mat][0]
                            self.densityscan[k,j,i] = proper_dens
    
    
    def fix_all_density(self):
        """Fix the density map for all materials: material type
           and density are inconsistent"""
        for k in range(self.dimensions[2]):
            for j in range(self.dimensions[1]):
                for i in range(self.dimensions[0]):
                    mat = self.material(self.materialscan[k,j,i])
                    if not self.__density_correct_p(k,j,i):
                        mat = self.material(self.materialscan[k,j,i])
                        self.__debug_print(mat)
                        proper_dens = self.density[mat][0]
                        self.densityscan[k,j,i] = proper_dens
    
    
    def read(self, phantfilename):
        """Reads in an EGSPhant from a .egsphant file"""
        
        self.__debug_print("CUBAAN: about to call _egsphant.read")
        
        d = _egsphant.read(phantfilename)
        self.__dict_to_egsphant(d)
    
    
    # def read(self, phantfilename):
    #     """Reads in an EGSPhant from a .egsphant file"""
    #     self.phantfilename = phantfilename
    #     
    #     try:
    #         f = open(self.phantfilename, "ro")
    #         
    #         try:
    #             self.__read_materials(f)
    #             
    #             self.__read_voxels(f)
    #             
    #             self.__read_materialscan(f)
    #             
    #             self.__read_densityscan(f)
    #         
    #         finally:
    #             f.close()
    #     
    #     except IOError:
    #         print "%s: error opening file %s" % (sys.argv[0], self.phantfilename)
    #     
    
    
    # I want a read_partial() function because I'd like to manually
    # create an egsphant file by just specifying the material scan,
    # and have the density scan filled in automatically. Just call
    # read_partial() and then fix_density() to fill in the density scan.
    def read_partial(self, phantfilename):
        """Reads in a partial EGSPhant from a .egsphant file with no density data"""
        self.phantfilename = phantfilename
        
        try:
            f = open(self.phantfilename, "ro")
            
            try:
                self.__read_materials(f)
                
                self.__read_voxels(f)
                self.edges_to_centers()
                
                self.__read_materialscan(f)
                
                # scan of densities: allocate space, but don't read
                self.densityscan = np.zeros((self.dimensions[2],
                                             self.dimensions[1],
                                             self.dimensions[0]),
                                            order='C', dtype=float)
            
            finally:
                f.close()
        
        except IOError:
            print "%s: error opening file %s" % (sys.argv[0], self.phantfilename)
            raise IOError
        
        except scanf.FormatError:
            print "%s: format error in file %s" % (sys.argv[0], self.phantfilename)
            raise scanf.FormatError
    
       
    
    def __read_voxels(self, phantfile):
        """Read voxel data from given file object"""
        try:
            # dimensions
            self.dimensions = scanf.fscanf(phantfile, "%d %d %d")
            
            self.xedges = np.zeros(self.dimensions[0]+1, order='C', dtype=float)
            self.yedges = np.zeros(self.dimensions[1]+1, order='C', dtype=float)
            self.zedges = np.zeros(self.dimensions[2]+1, order='C', dtype=float)
            
            # x-edges
            formatstr = ""
            for i in range(self.dimensions[0]+1):
                formatstr = formatstr + "%f "
            self.xedges = np.array(scanf.fscanf(phantfile, formatstr),
                                   dtype=float)
            
            self.__debug_print(self.xedges)
            
            # y-edges
            formatstr = ""
            for i in range(self.dimensions[1]+1):
                formatstr = formatstr + "%f "
            self.yedges = np.array(scanf.fscanf(phantfile, formatstr),
                                   dtype=float) 
            
            self.__debug_print(self.yedges)
            
            # z-edges
            formatstr = ""
            for i in range(self.dimensions[2]+1):
                formatstr = formatstr + "%f "
            self.zedges = np.array(scanf.fscanf(phantfile, formatstr),
                                   dtype=float)
            
            self.__debug_print(self.zedges)
        
        except IOError:
            raise IOError
        
        except scanf.FormatError:
            raise scanf.FormatError
    
   
    def __read_materials(self, phantfile):
        """Reads material name list from given file object"""
        try:
            # number of materials
            self.nmaterials = scanf.fscanf(phantfile, "%d")[0]
            self.__debug_print(self.nmaterials)
        
            # list of materials
            self.materials = []
            for i in range(self.nmaterials):
                material = scanf.fscanf(phantfile, "%s")[0]
                self.materials.append(material)
            
            self.__debug_print(self.materials)

            # dummy estepe values, one per material
            # even though they're dummy, I've seen different
            # values (0.0, and 1.0), so might as well store them
            self.estepe = []
            for i in range(self.nmaterials):
                self.estepe.append(scanf.fscanf(phantfile, "%f"))

        except IOError:
            raise IOError

        except scanf.FormatError:
            raise scanf.FormatError

    
    
    def __read_materialscan(self, phantfile):
        """Read in the material scan from given file object"""
        # NB: a 3D array is made up of a stack of slices, each
        #     slice being a matrix
        #     the index order is z,y,x where x is column index,
        #     y is row index, and z is slice index
        #    Ordering in the file:
        #      x increases to the right
        #      y increases downward
        #      z increases downward
        
        try:
            # scan of materials
            self.materialscan = np.zeros((self.dimensions[2],
                                          self.dimensions[1],
                                          self.dimensions[0]),
                                         order='C', dtype=int)
            
            for k in range(self.dimensions[2]):
                for j in range(self.dimensions[1]):
                    matrow = []
                    matrow.extend(scanf.fscanf(phantfile, "%s ")[0])
                    for i in range(len(matrow)):
                        self.materialscan[k,j,i] = int(matrow[i])
        
        except IOError:
            raise IOError
        
        except scanf.FormatError:
            raise scanf.FormatError
    
    
    def __read_densityscan(self, phantfile):
        """Read in the density scan from given file object"""
        # NB: a 3D array is made up of a stack of slices, each
        #     slice being a matrix
        #     the index order is z,y,x where x is column index,
        #     y is row index, and z is slice index
        
        try:
            # scan of densities
            self.densityscan = np.zeros((self.dimensions[2],self.dimensions[1],
                                         self.dimensions[0]), order='C',
                                        dtype=float)
            formatstr = ""
            for i in range(self.dimensions[0]):
                formatstr = formatstr + "%f "
            
            for k in range(self.dimensions[2]):
                for j in range(self.dimensions[1]):
                    self.densityscan[k,j,:] = np.array(scanf.fscanf(phantfile, formatstr))
        
        except IOError:
            raise IOError
        
        except scanf.FormatError:
            print "FOOBAR"
            raise scanf.FormatError
    
    
    def save(self, filename=None):
        """Write EGSPhant to an egsphant file."""
        if not filename:
            filename = self.phantfilename
        
        try:
            f = open(filename, 'w')
            
            try:
                # number of materials
                f.write('%2d\n' % self.nmaterials)
                
                # list of material names
                # string must be right-padded with spaces to
                # a length of 24
                for mat in self.materials:
                    f.write('%s' % mat)
                    for i in range(24-len(mat)):
                        f.write(' ')
                    f.write('\n')
                
                # dummy ESTEPE values (one per material)
                for i in self.estepe:
                    f.write('  %.7E' % i)
                f.write('\n')
                
                # phantom dimensions
                for d in self.dimensions:
                    f.write('%5d' % d)
                f.write('\n')
                
                # lists of edges are written out in chunks
                # 5 numbers wide
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
                
                # convert voxel edges to centers
                self.edges_to_centers()
                
                # write the material scans. each slice is
                # separated by a blank line
                for k in range(self.dimensions[2]):
                    for j in range(self.dimensions[1]):
                        for i in range(self.dimensions[0]):
                            f.write('%d' % self.materialscan[k,j,i])
                        f.write('\n')
                    f.write('\n')
                
                # density scans
                for k in range(self.dimensions[2]):
                    for j in range(self.dimensions[1]):
                        for i in range(self.dimensions[0]):
                            f.write('  % .6f    ' % self.densityscan[k,j,i])
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
            self.picklefilename = self.phantfilename.split('.egsphant')[0] + "_egsphant.pickle"
        else:
            self.picklefilename = pickle_filename
        
        try:
            pf = open(self.picklefilename, "wo")
            pickle.dump(self, pf)
        finally:
            pf.close()
    
    
    def unpickle(self, pickle_filename=None):
        """Unpickles from file pickle_filename"""
        if pickle_filename:
           self.picklefilename = pickle_filename
        elif not self.picklefilename:
            raise AttributeError
        try:
            pf = open(self.picklefilename, "ro")
            self = pickle.load(pf)
        finally:
            pf.close()
    
    
    def edges_to_centers(self):
        """Convert the list of voxel edges to voxel centers"""
        self.x = np.zeros(self.dimensions[0], order='C', dtype=float)
        self.y = np.zeros(self.dimensions[1], order='C', dtype=float)
        self.z = np.zeros(self.dimensions[2], order='C', dtype=float)
        
        for i in range(len(self.xedges)-1):
            self.x[i] = (self.xedges[i] + self.xedges[i+1])/2.
        
        for i in range(len(self.yedges)-1):
            self.y[i] = (self.yedges[i] + self.yedges[i+1])/2.
        
        for i in range(len(self.zedges)-1):
            self.z[i] = (self.zedges[i] + self.zedges[i+1])/2.
    
    
    def extent(self):
        """Returns a tuple of the edges of the phantom
           (xmin, xmax, ymin, ymax, zmin, zmax)"""
        return (self.x[0], self.x[-1], self.y[0], self.y[-1],
                self.z[0], self.z[-1])
    
    
    def print_wrong_voxels(self):
        """Print out voxels with the wrong density"""
        for k in range(self.dimensions[2]):
            for j in range(self.dimensions[1]):
                for i in range(self.dimensions[0]):
                    if not self.__density_correct_p(k,j,i):
                        print 'Voxel with wrong density: (%d, %d, %d)' % (k, j, i)
                        print '  Expected: %f' % self.density[self.material(self.materialscan[k,j,i])][0]
                        print '  Got:      %f' % self.densityscan[k,j,i]
    
    
    def __debug_print(self, o):
        """Print given object if the debug_p class variable is non-zero"""
        if self.debug_p:
            print o
    



if __name__ == "__main__":
    try:
        phant = EGSPhant(sys.argv[1])
    except IOError:
        raise
    
    print phant.materials[0]
    print phant.materialscan.getshape()
    print phant.densityscan.getshape()
    print "%s has density %s" % (phant.materials[3],
                                 repr(phant.density[phant.materials[3]]))
    
    print "Check wrong voxels..."
    phant.print_wrong_voxels()
    print "Fixing voxels (hopefully)..."
    phant.fix_density()
    print "Check wrong voxels..."
    phant.print_wrong_voxels()
    
    phant.save('foobar.egsphant')
