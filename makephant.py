#!/usr/bin/env python2.4

# $Id: makephant.py 86 2007-11-12 22:11:40Z dwchin $

from __future__ import division

import sys
import scanf

from numarray import *
#from Scientific import Statistics
#import mayavi
#from mayavi.tools import imv
#import pyvtk


# The egsphant file format is documented here:
#   http://www.irs.inms.nrc.ca/BEAM/user_manuals/pirs794/node95.html

class EGSPhant:
    """A class encapsulating an EGS phantom file"""
    
    # Debug flag
    debug_p = 0
    
    # Name of the egsphant file
    phantfilename = ''
    
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
    # FIXME: GOLDALLOY and DENTALPORCELAIN are totally fake
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
                'CERAMCOC3' : (2.4, 2.8) }

    
    def __init__(self, phantfilename=None, xdim=0, ydim=0, zdim=0):
        """Basic init method, with optional file name argument"""
        
        if phantfilename:
            self.read(phantfilename)
        else:
            self.nmaterials = 0
            self.materials = []
            self.estepe = []

            if xdim != 0 and ydim !=0 and zdim !=0:
                self.dimensions = (xdim, ydim, zdim)
                self.xedges = zeros(self.dimensions[0], type=Float32)
                self.yedges = zeros(self.dimensions[1], type=Float32)
                self.zedges = zeros(self.dimensions[2], type=Float32)
                self.materialscan = zeros([self.dimensions[2], self.dimensions[1],
                                          self.dimensions[0]], type=Float32)
                self.densityscan = zeros([self.dimensions[2], self.dimensions[1],
                                          self.dimensions[0]], type=Float32)

    

    def material(self, i):
        """Given integer, return material"""
        return self.materials[i-1]
    

    def density_correct_p(self, k, j, i):
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
        """Fix the density map: material type and density are
           inconsistent"""
        for k in range(self.dimensions[2]):
            for j in range(self.dimensions[1]):
                for i in range(self.dimensions[0]):
                    mat = self.material(self.materialscan[k,j,i])
                    if mat == 'AU700ICRU' or mat == 'DENTALAMALGAM' or mat == 'PEMA' or mat == 'VITALLIUMASTMF90':
                        if not self.density_correct_p(k,j,i):
                            mat = self.material(self.materialscan[k,j,i])
                            self.debug_print(mat)
                            proper_dens = self.density[mat][0]
                            self.densityscan[k,j,i] = proper_dens        
    
    def fix_all_density(self):
        """Fix the density map: material type and density are
           inconsistent"""
        for k in range(self.dimensions[2]):
            for j in range(self.dimensions[1]):
                for i in range(self.dimensions[0]):
                    mat = self.material(self.materialscan[k,j,i])
                    if not self.density_correct_p(k,j,i):
                        mat = self.material(self.materialscan[k,j,i])
                        self.debug_print(mat)
                        proper_dens = self.density[mat][0]
                        self.densityscan[k,j,i] = proper_dens        
    
    def read(self, phantfilename):
        """Reads in an EGSPhant from a .egsphant file"""
        self.phantfilename = phantfilename
        
        try:
            f = open(self.phantfilename, "ro")
            
            try:        
                self.read_materials(f)
                                                
                self.read_voxels(f)
                                
                self.read_materialscan(f)
                                                        
                self.read_densityscan(f)
            
            except scanf.FormatError:
                print "%s: format error in file %s" % (sys.argv[0], self.phantfilename)
            
            else:
                f.close()
                
        except IOError:
            print "%s: error opening file %s" % (sys.argv[0], self.phantfilename)

                
        else:
            f.close()

    
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
                self.read_materials(f)
                
                self.read_voxels(f)
                
                self.read_materialscan(f)
                            
                # scan of densities: allocate space, but don't read
                self.densityscan = zeros([self.dimensions[2],self.dimensions[1],
                                          self.dimensions[0]], type=Float32)
                            
            finally:
                f.close()
                
        except IOError:
            print "%s: error opening file %s" % (sys.argv[0], self.phantfilename)
            raise IOError
            
        except scanf.FormatError:
            print "%s: format error in file %s" % (sys.argv[0], self.phantfilename)
            raise scanf.FormatError
    
    
    def read_materials(self, phantfile):
        """Reads material name list from given file object"""
        try:
            # number of materials
            self.nmaterials = scanf.fscanf(phantfile, "%d")[0]
            self.debug_print(self.nmaterials)
            
            # list of materials
            self.materials = []
            for i in range(self.nmaterials):
                material = scanf.fscanf(phantfile, "%s")[0]
                self.materials.append(material)
            
            self.debug_print(self.materials)
            
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


    def read_voxels(self, phantfile):
        """Read voxel data from given file object"""
        try:
            # dimensions
            self.dimensions = scanf.fscanf(phantfile, "%d %d %d")

            self.debug_print(("dimensions = ", self.dimensions))
            
            self.xedges = zeros(self.dimensions[0]+1, type=Float32)
            self.yedges = zeros(self.dimensions[1]+1, type=Float32)
            self.zedges = zeros(self.dimensions[2]+1, type=Float32)
     
            # x-edges
            formatstr = ""       
            for i in range(self.dimensions[0]+1):
                formatstr = formatstr + "%f "
            self.xedges = array(scanf.fscanf(phantfile, formatstr))
     
            self.debug_print(self.xedges)
     
            # y-edges
            formatstr = ""
            for i in range(self.dimensions[1]+1):
                formatstr = formatstr + "%f "
            self.yedges = array(scanf.fscanf(phantfile, formatstr))
             
            self.debug_print(self.yedges)
     
            # z-edges
            formatstr = ""
            for i in range(self.dimensions[2]+1):
                formatstr = formatstr + "%f "
            self.zedges = array(scanf.fscanf(phantfile, formatstr))
     
            self.debug_print(self.zedges)
        
        except IOError:
            raise IOError
        
        except scanf.FormatError:
            raise scanf.FormatError
 
       
    def read_materialscan(self, phantfile):
        """Read in the material scan from given file object"""
        # NB: a 3D array is made up of a stack of slices, each
        #     slice being a matrix
        #     the index order is z,y,x where x is column index, 
        #     y is row index, and z is slice index

        try:
            # scan of materials
            self.materialscan = zeros([self.dimensions[2],self.dimensions[1],
                                      self.dimensions[0]], type=Int32)
    
            for k in range(self.dimensions[2]):
                for j in range(self.dimensions[1]):
                    print "k = ", k, ", ", "j = ", j
                    matrow = []
                    matrow.extend(scanf.fscanf(phantfile, "%s ")[0])
                    if len(matrow) != self.dimensions[0]:
                        print matrow, len(matrow)
                    for i in range(len(matrow)):
                        self.materialscan[k,j,i] = int(matrow[i])
                        
        except IOError:
            raise IOError
            
        except scanf.FormatError:
            raise scanf.FormatError



    def read_densityscan(self, phantfile):
        """Read in the density scan from given file object"""
        # NB: a 3D array is made up of a stack of slices, each
        #     slice being a matrix
        #     the index order is z,y,x where x is column index, 
        #     y is row index, and z is slice index

        try:
            # scan of densities
            self.densityscan = zeros([self.dimensions[2],self.dimensions[1],
                                      self.dimensions[0]], type=Float32)
            formatstr = ""
            for i in range(self.dimensions[0]):
                formatstr = formatstr + "%f "
    
            for k in range(self.dimensions[2]):
                for j in range(self.dimensions[1]):
                    self.densityscan[k,j,:] = array(scanf.fscanf(phantfile, formatstr))
        
        except IOError:
            raise IOError
            
        except scanf.FormatError:
            print "FOOBAR"
            raise scanf.FormatError


    def save(self, filename):
        """Write EGSPhant to an egsphant file."""
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


    def edges_to_centers(self):
        """Convert the list of voxel edges to voxel centers"""
        self.x = zeros(self.dimensions[0], type=Float32)
        self.y = zeros(self.dimensions[1], type=Float32)
        self.z = zeros(self.dimensions[2], type=Float32)

        # x
        for i in range(len(self.xedges)-1):
            self.x[i] = (self.xedges[i] + self.xedges[i+1])/2.

        # y
        for i in range(len(self.yedges)-1):
            self.y[i] = (self.yedges[i] + self.yedges[i+1])/2.

        # z
        for i in range(len(self.zedges)-1):
            self.z[i] = (self.zedges[i] + self.zedges[i+1])/2.


    def print_wrong_voxels(self):
        """Print out voxels with the wrong density"""
        for k in range(self.dimensions[2]):
            for j in range(self.dimensions[1]):
                for i in range(self.dimensions[0]):
                    if not self.density_correct_p(k,j,i):
                        print 'Voxel with wrong density: (%d, %d, %d)' % (k, j, i)
                        print '  Expected: %f' % self.density[self.material(self.materialscan[k,j,i])][0]
                        print '  Got:      %f' % self.densityscan[k,j,i]
            
           

    def debug_print(self, o):
        """Print given object if the debug_p class variable is non-zero"""
        if self.debug_p:
            print o


if __name__ == "__main__":
    #p.nmaterials = 6
    #p.materials.append('AIR700ICRU')
    #p.materials.append('LUNG700ICRU')
    #p.materials.append('ICRUTISSUE700ICRU')
    #p.materials.append('ICRPBONE700ICRU')
    #p.materials.append('GOLDALLOY')
    #p.materials.append('DENTALPORCELAIN')

    #p.estepe = ones(p.nmaterials, type=Float32)

    #print p.dimensions
    #print shape(p.xedges)
    #print p.xedges

    # set all slices to be tissue density
    #p.materialscan[:,:,:] = p.materialscan[:,:,:] + 3 * ones((p.dimensions[2], p.dimensions[1], p.dimensions[0]), type=Int32)

    #p.save('mockup.egsphant')
    p = EGSPhant()
    p.read_partial('fixed_partial_denture_nodens.egsphant')

    print "dimensions = ", p.dimensions
    
    for i in range(p.dimensions[0]+1):
        p.xedges[i] = -2.8 + i * 0.1

    for i in range(p.dimensions[1]+1):
        p.yedges[i] = -1.4 + i * 0.1

    for i in range(p.dimensions[2]+1):
        p.zedges[i] = i * 0.1

    p.edges_to_centers()
    p.fix_all_density()

    p.save('mockup.egsphant')

