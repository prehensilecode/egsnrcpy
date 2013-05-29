#!/usr/bin/env python2.4

# $Id: makeblankphant.py 86 2007-11-12 22:11:40Z dwchin $



from EGSPhant import *

debug_p = True

def debug_print(arg):
    if debug_p:
        print arg



class BlankPhant:
    def __init__(self, filename, xdim, ydim, zdim, voxel_width):
        '''Assumes cubic voxels'''
        self.phantom = EGSPhant(None, xdim, ydim, zdim)
        
        # TODO: don't overwrite pre-existing file
        
        self.phantom.phantfilename = filename
        
        self.phantom.nmaterials = 6
        
        self.phantom.materials = []
        self.phantom.materials.append('AIR700ICRU')
        #self.phantom.materials.append('H2O700ICRU')
        self.phantom.materials.append('LUNG700ICRU')
        self.phantom.materials.append('ICRUTISSUE700ICRU')
        self.phantom.materials.append('ICRPBONE700ICRU')
        self.phantom.materials.append('ECLIPSE')
        self.phantom.materials.append('CERAMCOC3')
        
        self.phantom.estepe = ones(self.phantom.nmaterials, type=Float32)
        
        self.phantom.xedges = zeros(self.phantom.dimensions[0]+1, type=Float32)
        self.phantom.yedges = zeros(self.phantom.dimensions[1]+1, type=Float32)
        self.phantom.zedges = zeros(self.phantom.dimensions[2]+1, type=Float32)
        
        # make the x-y slices center on (x=0, y=0)
        x_start = self.phantom.dimensions[0] * voxel_width / 2.
        y_start = self.phantom.dimensions[1] * voxel_width / 2.
        
        for i in range(self.phantom.dimensions[0]+1):
            self.phantom.xedges[i] = -x_start + i * voxel_width
        
        for i in range(self.phantom.dimensions[1]+1):
            self.phantom.yedges[i] = -y_start + i * voxel_width
        
        for i in range(self.phantom.dimensions[2]+1):
            self.phantom.zedges[i] = i * voxel_width
        
        self.phantom.materialscan = zeros([self.phantom.dimensions[2],self.phantom.dimensions[1],
                                   self.phantom.dimensions[0]], type=Int32)
        # set all slices to be tissue
        self.phantom.materialscan[:,:,:] = self.phantom.materialscan[:,:,:] + 3 * ones((self.phantom.dimensions[2], self.phantom.dimensions[1], self.phantom.dimensions[0]), type=Int32)
        
        self.phantom.densityscan = zeros([self.phantom.dimensions[2],self.phantom.dimensions[1],
                                  self.phantom.dimensions[0]], type=Float32)
        
        # fix only the artificial materials
        self.phantom.fix_density()
    
    
    def fix_all_density(self):
        '''Fixes up the density scan'''
        
        # if tissue, want density to be 1.0
        # otherwise, set to the mean density for that material
        # (to be accurate, only "mean" in the sense of middle of the
        # range of possible densities.)
        for k in range(self.phantom.dimensions[2]):
            for j in range(self.phantom.dimensions[1]):
                for i in range(self.phantom.dimensions[0]):
                    mat = self.phantom.material(self.phantom.materialscan[k,j,i])
                    if not self.phantom.density_correct_p(k,j,i):
                        mat = self.phantom.material(self.phantom.materialscan[k,j,i])
                        self.phantom.debug_print(mat)
                        if mat == 'ICRUTISSUE700ICRU':
                            proper_dens = 1.0
                        else:
                            proper_dens = 0.5 (self.phantom.density[mat][0] + self.phantom.density[mat][1])
                        self.phantom.densityscan[k,j,i] = proper_dens
    
    
    def save(self):
        self.phantom.save(self.phantom.phantfilename)
    



def usage():
    print "Usage: makeblankphant.py filename [nx ny nz dx]"
    print "  where filename is the name of the phantom file to be created"
    print "  nx, ny, nz are the number of voxels in each dimension"
    print "  and dx = dy = dz is the voxel size"


if __name__ == "__main__":
    debug_print(sys.argv)
    
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)
    elif len(sys.argv) == 2:
        p = BlankPhant(sys.argv[1], 56, 28, 40, 0.1)    
    elif len(sys.argv) == 6:
        p = BlankPhant(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]))
    else:
        usage()
        sys.exit()
        
    
    print "dimensions = ", p.phantom.dimensions
    print "shape(p.phantom.xedges) = ", shape(p.phantom.xedges)
    
    p.save()

