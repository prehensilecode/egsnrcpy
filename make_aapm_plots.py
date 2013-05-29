#!/usr/bin/env python2.4

from contour_image import *


metalp = unpickle_phant('fixed_partial_metal_pontic_egsphant.pickle')
metald = unpickle_dose('fixed_partial_metal_pontic_3ddose.pickle')
rowp = unpickle_phant('row_teeth_egsphant.pickle')
rowd = unpickle_dose('row_teeth_3ddose.pickle')
dentp = unpickle_phant('fixed_partial_denture_egsphant.pickle')
dentd = unpickle_dose('fixed_partial_denture_3ddose.pickle')

metald.make_absolute('6MV',1000)
rowd.make_absolute('6MV',1000)
dentd.make_absolute('6MV',1000)

xz_plot(metalp,metald,14,"Fixed partial denture, all metal", normalization_factor)
yz_plot(metalp,metald,28,"Fixed partial denture, all metal", normalization_factor)
xy_plot(dentp,dentd,12,"Fixed partial denture", normalization_factor)
xz_plot(dentp,dentd,14,"Fixed partial denture", normalization_factor)
yz_plot(dentp,dentd,28,"Fixed partial denture", normalization_factor)
xy_plot(rowp,rowd,11,"Teeth without dental work", normalization_factor)
xz_plot(rowp,rowd,14,"Teeth without dental work", normalization_factor)
yz_plot(rowp,rowd,28,"Teeth without dental work", normalization_factor)

xc=20
yc=15
zc=35

plot(rowd.x, rowd.dose[zc,yc,:], dentd.x, dentd.dose[zc,yc,:], metald.x, metald.dose[zc,yc,:]) 
titlestr = 'Lateral dose profile (z = %.2f cm, y = %.2f cm)' % (rowd.z[zc], rowd.y[yc])
title(titlestr)
xlabel('x (cm)')
ylabel('Abs. dose (cGy)')
savefig('Dental_work_lateral_dose_shadow')
show()

plot(rowd.x, rowd.dose[zc,yc,:], dentd.x, dentd.dose[zc,yc,:], metald.x, metald.dose[zc,yc,:]) 
title(titlestr)
xlabel('x (cm)')
ylabel('Abs. dose (cGy)')
legend(('No dental work','Mixed metal & ceramic','All metal'),'upper right')
show()

zc = 9
plot(rowd.x, rowd.dose[zc,yc,:], dentd.x, dentd.dose[zc,yc,:], metald.x, metald.dose[zc,yc,:]) 
titlestr = 'Lateral dose profile (z = %.2f cm, y = %.2f cm)' % (rowd.z[zc], rowd.y[yc])
title(titlestr)
xlabel('x (cm)')
ylabel('Abs. dose (cGy)')
legend(('No dental work','Mixed metal & ceramic','All metal'),'lower right')
savefig('Dental_work_lateral_dose')
show()

zc=7
titlestr='Depth dose profile (x = %.2f, y = %.2f)' % (rowd.x[xc], rowd.y[yc])
titlestr = 'Lateral dose profile (z = %.2f cm, y = %.2f cm)' % (rowd.z[zc], rowd.y[yc])
plot(rowd.x, rowd.dose[zc,yc,:], dentd.x, dentd.dose[zc,yc,:], metald.x, metald.dose[zc,yc,:]) 
title(titlestr)
xlabel('x (cm)')
ylabel('Abs. dose (cGy)')
legend(('No dental work','Mixed metal & ceramic','All metal'),'lower right')
savefig('Dental_work_lateral_dose_z_0_75')
show()

zc=35
plot(rowd.z[0:zc],rowd.dose[0:zc,yc,xc], dentd.z[0:zc], dentd.dose[0:zc,yc,xc], metald.z[0:zc], metald.dose[0:zc,yc,xc])
titlestr = 'Depth dose profile (x = %.2f cm, y = %.2f cm)' % (rowd.x[xc], rowd.y[yc])
title(titlestr)
legend(('No dental work','Mixed metal & ceramic','All metal'),'lower right')
xlabel('z (cm)')
ylabel('Abs. dose (cGy)')
savefig('Dental_work_depth_dose')
