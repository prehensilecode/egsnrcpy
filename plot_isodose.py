#!/usr/bin/env python

from EGSPhant import *
from MCDose import *
from pylab import *

d = MCDose('block_amalgam.3ddose')
d.make_absolute('6MV', 100)

p = EGSPhant('block_amalgam.egsphant')

X, Y = meshgrid(d.x, d.y)

Z = d.dose[11, :, :]

CS = contourf(X, Y, p.densityscan[11, :, :], cmap=cm.bone, origin='lower')
#CS2 = contourf(X, Y, Z, 10, cmap=cm.jet, origin='lower', alpha='0.5')
CS2 = imshow(X, Y, Z, 10, cmap=cm.jet, origin='lower', alpha='0.5')
title('Example isodose plot')
xlabel('X (cm)')
ylabel('Y (cm)')

#CS2 = contour(X, Y, Z, CS.levels, colors='white', origin='lower', hold='on')


ax_cbar = colorbar(CS, tickfmt='%1.2f')
ax_cbar.set_ylabel('dose (foo units)')

show()
