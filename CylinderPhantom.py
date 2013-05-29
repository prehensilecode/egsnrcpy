# encoding: utf-8

import egsnrc.EGSPhant as EGSPhant

from numarray import *


# want to make a phantom used in skindose
# the lower section is oblongoid:
#      height 5cm
#      width  20cm
#      depth  30cm
# the upper section is a half-cylinder (semicircular prism)
#      radius 10cm
#      depth 30cm
#
# so, 3 parameters define its size: height, radius, depth
#   (width = 2 x radius)
# also need to define voxel size dx, dy, dz

# NB x-coord is read from left to right,
#    y-coord from top to bottom
#    z-coord from top to bottom

class CylinderPhantom:
    def __init__(self, filename=None):
        self.debug_p = False
        
        self.phantfilename = filename
        
        # all measurements are in cm
        self.height = 5.
        self.radius = 10.
        self.width = 2. * self.radius
        self.depth = 30.
        
        # voxel size
        self.dx = 0.05
        self.dy = 0.05
        self.dz = 0.25
        
        # compute dimensions of phantom, i.e. number of
        # voxels in each direction
        self.dimensions = (int(self.width / self.dx), \
            int((self.height + self.radius) / self.dy), \
            int(self.depth / self.dz))
        
        # print self.dimensions
        
        # make a blank phantom
        self.phantom = EGSPhant.EGSPhant(None, self.dimensions[0], self.dimensions[1], self.dimensions[2])
        
        self.phantom.phantfilename = self.phantfilename
        
        # phantom is just air and water
        self.phantom.nmaterials = 2
        self.phantom.materials = ('AIR700ICRU', 'H2O700ICRU')
        
        self.phantom.estepe = ones(self.phantom.nmaterials, type=Float32)
        
        # set the voxel edges
        self.phantom.xedges = zeros(self.phantom.dimensions[0]+1, type=Float32)
        self.phantom.yedges = zeros(self.phantom.dimensions[1]+1, type=Float32)
        self.phantom.zedges = zeros(self.phantom.dimensions[2]+1, type=Float32)
        
        for i in range(self.phantom.dimensions[0]+1):
            self.phantom.xedges[i] = -10. + i * self.dx
            
        for i in range(self.phantom.dimensions[1]+1):
            self.phantom.yedges[i] = -10. + i * self.dy
        
        for i in range(self.phantom.dimensions[2]+1):
            self.phantom.zedges[i] = -15. + i * self.dz
            
        self.phantom.edges_to_centers()
    
    
    def build(self):    
        # all slices are air
        self.phantom.materialscan = ones([self.phantom.dimensions[2],
            self.phantom.dimensions[1], self.phantom.dimensions[0]], 
            type=Int32)
        
        # we'll fix the density scan after the phantom is built up
        self.phantom.densityscan = zeros([self.phantom.dimensions[2],
            self.phantom.dimensions[1], self.phantom.dimensions[0]], 
            type=Float32)
        
        #
        # now, make the cylinder shape
        #
        
        # first, the easy bit: the oblong part at the bottom
        #   it covers all x, all z, and part of y
        j_start = int(self.radius / self.dy)
        self.phantom.materialscan[:,j_start:,:] = 2 * ones([self.phantom.dimensions[2],
            int(self.height / self.dy), self.phantom.dimensions[0]], type=Int32)
        
        # take the constant-z slices 
        # in the first slice,
        #    if the distance from the voxel to (0,0,z) is less than self.radius, 
        #        set that voxel to have material 2 (water)
        # copy that first slice to all other slices
        j_max = int(self.radius / self.dy)
        for j in range(j_max):
            for i in range(self.phantom.dimensions[0]):
                if self.distance(self.phantom.x[i], self.phantom.y[j], 0., 0.) < self.radius:
                    self.phantom.materialscan[0,j,i] = 2
        # all the slices are the same
        for k in range(1, self.phantom.dimensions[2]):
            self.phantom.materialscan[k,:,:] = self.phantom.materialscan[0,:,:]
        
        # fix up the density scan
        self.phantom.fix_all_density()
                    
        self.phantom.save()
    
    
    def read(self, filename=None):
        self.debug_print("HERE WE ARE")
        if (filename):
            self.phantfilename = filename
        self.phantom.read(self.phantfilename)
        self.debug_print("CYL.PHANTOM: Done reading")
    
    
    def distance(self, x1, y1, x2, y2):
        dx = x1 - x2
        dy = y1 - y2
        return math.sqrt(dx*dx + dy*dy)
        
    
    def debug_print(self, arg):
        if self.debug_p:
            print arg

