# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

from KicadModTree import KicadMod, createNumberedPadsTHT
from kilibs.config import global_config as GC

global_config = GC.GLOBAL_CONFIG

# http://www.jst-mfg.com/product/pdf/eng/ePH.pdf

pitch = 3.3

manu = "Hirose"

suffix = "Straight"

desc = "Hirose DF33 series connector, 3.30mm pitch, top entry PTH"
tags = "connector hirose df33 top straight vertical through thru hole"
lib_name = "Connector_Hirose"

for pincount in range(2,16):

    part = "DF33C-{pincount:02}P-125DSA".format(pincount=pincount)

    footprint_name = "{0}_{1}_{2:02}x{3:.2f}mm_{4}".format(manu,part,pincount,pitch,suffix)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(desc)
    kicad_mod.setTags(tags)

    # set general values
    kicad_mod.append(Property(name=Property.REFERNECE, 'REF**', {'x':0, 'y':2.5}, 'F.SilkS'))
    kicad_mod.addText(Property(name=Property.VALUE, footprint_name, {'x':0, 'y':4}, 'F.Fab'))

    drill = 0.6

    x_dia = 0.95
    y_dia = 1.25

    # create pads
    createNumberedPadsTHT(kicad_mod, pincount, pitch, drill, {'x':x_dia, 'y':y_dia})

    A = (pincount - 1) * pitch
    B = A + 2.9

    x1 = -(B-A) / 2
    y1 = -2.2
    x2 = x1 + B
    y2 = 1.2

    #line offset
    off = 0.1

    x1 -= off
    y1 -= off

    x2 += off
    y2 += off

    #draw the main outline around the footprint
    kicad_mod.addRectangle({'x':x1,'y':y1},{'x':x2,'y':y2})

    #add pin-1 marker

    xm = 0
    ym = -2.8

    m = 0.3

    kicad_mod.addPolygonLine([{'x':xm,'y':ym},
                               {'x':xm - m,'y':ym - 2 * m},
                               {'x':xm + m,'y':ym - 2 * m},
                               {'x':xm,'y':ym}])

    #side-wall thickness S

    S = 0.5

    #bottom line
    kicad_mod.addPolygonLine([{'x':x1,'y':0},
                               {'x':x1+S,'y':0},
                               {'x':x1+S,'y':y2-S},
                               {'x':x2-S,'y':y2-S},
                               {'x':x2-S,'y':0},
                               {'x':x2,'y':0}])

    #left mark

    #gap g
    g = 0.75

    kicad_mod.addPolygonLine([{'x':x1,'y':-g},
                               {'x':x1+S,'y':-g},
                               {'x':x1+S,'y':y1+S*1.5},
                               {'x':x1+2*S,'y':y1+S*1.5},
                               {'x':x1+2*S,'y':y1}])

    kicad_mod.addPolygonLine([{'x':x2,'y':-g},
                               {'x':x2-S,'y':-g},
                               {'x':x2-S,'y':y1+S*1.5},
                               {'x':x2-2*S,'y':y1+S*1.5},
                               {'x':x2-2*S,'y':y1}])

    #middle line
    kicad_mod.addPolygonLine([{'x':x1+2*S,'y':y1+1.5*S},
                               {'x':0.2*pitch,'y':y1+1.5*S},
                               {'x':0.2*pitch,'y':y1+0.5*S},
                               {'x':0.8*pitch,'y':y1+0.5*S},
                               {'x':0.8*pitch,'y':y1+1.5*S},
                               {'x':A-0.8*pitch,'y':y1+1.5*S},
                               {'x':A-0.8*pitch,'y':y1+0.5*S},
                               {'x':A-0.2*pitch,'y':y1+0.5*S},
                               {'x':A-0.2*pitch,'y':y1+1.5*S},
                               {'x':x2-2*S,'y':y1+1.5*S}])

    """
    #add pictures of pins
    #pin-width w
    #pin-length l
    w = 0.32
    l = 3.5

    py = -2.5

    kicad_mod.addLine({'x':x1+T,'y':py},{'x':x2-T,'y':py})

    kicad_mod.addLine({'x':x1+T,'y':py+1},{'x':x2-T,'y':py+1})

    for p in range(pincount):

        px = p * pitch

        kicad_mod.addPolygonLine([{'x': px,'y': py},
                                   {'x': px-w,'y': py},
                                   {'x': px-w,'y': py-l+0.25*w},
                                   {'x': px,'y': py-l},
                                   {'x': px+w,'y': py-l+0.25*w},
                                   {'x': px+w,'y': py},
                                   {'x': px,'y': py}])


    """
    #add a courtyard
    cy = 0.5

    kicad_mod.addRectangle({'x':x1-cy,'y':y1-cy},{'x':x2+cy,'y':y2+cy},"F.CrtYd",0.05)

    kicad_mod.model = global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix

    #shift the model along

    if pincount % 2 == 0: #even
        xOff = (pincount / 2 - 0.5) * pitch
    else:
        xOff = (pincount / 2) * pitch

    kicad_mod.model_pos['x'] = xOff / 25.4
    kicad_mod.model_rot['z'] = 180

    # output kicad model
    f = open(footprint_name + ".kicad_mod","w")

    f.write(kicad_mod.__str__())

    f.close()
