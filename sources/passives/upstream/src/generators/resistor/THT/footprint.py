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

from KicadModTree import *  # NOQA
from generators.tools.footprint.drawing_tools import *
from generators.tools.footprint.footprint_scripts_resistorlike import *
from generators.tools.spec.base_spec import BaseSpec


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    lib_name="Resistor_THT"

    # standard resistors: http://cdn-reichelt.de/documents/datenblatt/B400/1_4W%23YAG.pdf
    type = "cyl"
    d2=0
    seriesname = "Axial_DIN0204"; w=3.6; d=1.6; ddrill=0.7; R_POW=1.0/6.0; add_description="http://cdn-reichelt.de/documents/datenblatt/B400/1_4W%23YAG.pdf"; name_additions=[]
    for rm in [5.08, 7.62]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1
    for rm in [1.9,2.54, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_DIN0207"; w = 6.3; d = 2.5; ddrill = 0.8; R_POW = 0.25; add_description="http://cdn-reichelt.de/documents/datenblatt/B400/1_4W%23YAG.pdf"; name_additions=[]
    for rm in [7.62, 10.16, 15.24]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [2.54, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname="Axial_DIN0309"; w = 9; d = 3.2; ddrill = 0.8; R_POW = 0.5; add_description="http://cdn-reichelt.de/documents/datenblatt/B400/1_4W%23YAG.pdf"; name_additions=[]
    for rm in [12.7, 15.24, 20.32, 25.4]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [2.54, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_DIN0411"; w = 9.9; d = 3.6; ddrill = 1.2; R_POW = 1; add_description=""; name_additions=[]
    for rm in [12.7,15.24, 20.32, 25.4]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [5.08,7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_DIN0414"; w = 11.9; d = 4.5; ddrill = 1.2; R_POW = 2; add_description="http://www.vishay.com/docs/20128/wkxwrx.pdf"; name_additions=[]
    for rm in [15.24, 20.32, 25.4]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [5.08,7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_DIN0516"; w = 15.5; d = 5; ddrill = 1.2; R_POW = 2; add_description="http://cdn-reichelt.de/documents/datenblatt/B400/1_4W%23YAG.pdf"; name_additions=[]
    for rm in [20.32, 25.4, 30.48]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [5.08, 7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_DIN0614"; w = 14.3; d = 5.7; ddrill = 1.4; R_POW = 1.5; add_description=""
    for rm in [15.24, 20.32, 25.4]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [5.08,7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_DIN0617"; w = 17; d = 6; ddrill = 1.2; R_POW = 2; add_description="http://www.vishay.com/docs/20128/wkxwrx.pdf"; name_additions=[]
    for rm in [20.32, 25.4, 30.48]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [5.08, 7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_DIN0918"; w = 18; d = 9; ddrill = 1.2; R_POW = 4; add_description=""
    for rm in [22.86, 25.4, 30.48]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_DIN0922"; w = 20; d = 9; ddrill = 1.2; R_POW = 5; add_description="http://www.vishay.com/docs/20128/wkxwrx.pdf"; name_additions=[]
    for rm in [25.4, 30.48]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    # POWER Resistors (rectangular)
    type = "box"
    seriesname = "Axial_Power"
    w=20
    d=6.4
    d2=6.4
    ddrill=1.2
    R_POW=4
    add_description="http://cdn-reichelt.de/documents/datenblatt/B400/5WAXIAL_9WAXIAL_11WAXIAL_17WAXIAL%23YAG.pdf"
    name_additions=[]

    for rm in [22.4, 25.4, 30.48]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [5.08,7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_Power"; w=25; d=6.4; d2=6.4; ddrill=1.2; R_POW=5; name_additions=[]
    for rm in [27.94,30.48]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_Power"; w=38; d=6.4; d2=6.4; ddrill=1.2; R_POW=7; name_additions=[]
    for rm in [40.64,45.72]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_Power"; w=25; d=9; d2=9; ddrill=1.2; R_POW=7; name_additions=[]
    for rm in [27.94,30.48]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [7.62,10.16]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_Power"; w=38; d=9; d2=9; ddrill=1.2; R_POW=9; name_additions=[]
    for rm in [40.64,45.72]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_Power"; w=50; d=9; d2=9; ddrill=1.2; R_POW=11; name_additions=[]
    for rm in [55.88,60.96]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_Power"; w=75; d=9; d2=9; ddrill=1.2; R_POW=17; name_additions=[]
    for rm in [81.28,86.36]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_Power"; w=48; d=12.5; d2=12.5; ddrill=1.2; R_POW=15; name_additions=[]
    for rm in [55.88,60.96]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [7.62,10.16]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    seriesname = "Axial_Power"; w=60; d=14; d2=14; ddrill=1.2; R_POW=25; name_additions=[]
    for rm in [66.04,71.12]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    for rm in [10.16]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
        num_fps_generated += 1

    # shunt resistor with additional pins
    type = "box"
    seriesname = "Axial_Shunt";  ddrill=1.5; add_description="http://www.vishay.com/docs/30217/cpsl.pdf"; name_additions=[]
    rm = 25.4; shuntPinsRM=14.3; w=22.2; d=8; d2=d; R_POW=3
    makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2, hasShuntPins=True, shuntPinsRM=shuntPinsRM,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
    num_fps_generated += 1

    rm = 25.4; shuntPinsRM=14.3; w=22.2; d=9.5; d2=d; R_POW=5
    makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2, hasShuntPins=True, shuntPinsRM=shuntPinsRM,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
    num_fps_generated += 1

    rm = 38.1; shuntPinsRM=25.4; w=35.3; d=9.5; d2=d; R_POW=7
    makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2, hasShuntPins=True, shuntPinsRM=shuntPinsRM,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
    num_fps_generated += 1

    rm = 50.8; shuntPinsRM=34.93; w=47.6; d=9.5; d2=d; R_POW=10
    makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2, hasShuntPins=True, shuntPinsRM=shuntPinsRM,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
    num_fps_generated += 1

    rm = 50.8; shuntPinsRM=34.93; w=47.6; d=12.7; d2=d; R_POW=15
    makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2, hasShuntPins=True, shuntPinsRM=shuntPinsRM,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
    num_fps_generated += 1

    # wire bridge/bare metal resistor elements
    type = "bridge"
    seriesname = "Bare_Metal_Element"
    d=4.8
    d2=2
    ddrill=1.5
    add_description="https://www.bourns.com/pdfs/PWR4412-2S.pdf"
    name_additions=[]
    rm = 11.4; w=rm+1; R_POW=1
    makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
    num_fps_generated += 1

    rm = 15.3; w=rm+1; R_POW=3
    makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
    num_fps_generated += 1

    rm = 20.3; w=rm+1; R_POW=5
    makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type,d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, specialtags=[], lib_name=lib_name)
    num_fps_generated += 1

    # radial resistors, 45deg wires
    rm2=0
    w2=0
    type = "simple45"; seriesname = "Radial_Power"; add_description = "http://www.vitrohm.com/content/files/vitrohm_series_kv_-_201601.pdf"; name_additions=[]
    w = 7; h = 8; ddrill = 1.2; rm=2.4; rm2=2.3; R_POW=7
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=False, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=38, lib_name=lib_name)
    num_fps_generated += 1

    w = 9; h = 10; ddrill = 1.2; rm=2.7; rm2=2.3; R_POW=17
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=False, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=75, lib_name=lib_name)
    num_fps_generated += 1

    # radial resistors, simple box
    rm2=0; w2=0
    type = "simple"; seriesname = "Box"; add_description = "http://www.vishay.com/docs/60051/cns020.pdf"; name_additions=[]
    w = 8.38; h = 2.54; ddrill = 0.8; rm=5.08; rm2=0; R_POW=0.5
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=False, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=6.62, lib_name=lib_name)
    num_fps_generated += 1

    add_description = "http://www.produktinfo.conrad.com/datenblaetter/425000-449999/443860-da-01-de-METALLBAND_WIDERSTAND_0_1_OHM_5W_5Pr.pdf"; name_additions=[]
    w = 13.0; h = 4.0; ddrill = 1.0; rm=9.0; rm2=0; R_POW=2
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=False, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=8, lib_name=lib_name)
    num_fps_generated += 1

    w = 14.0; h = 5.0; ddrill = 1.0; rm=9.0; rm2=0; R_POW=5
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=False, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=18, lib_name=lib_name)
    num_fps_generated += 1

    w = 26.0; h = 5.0; ddrill = 1.4; rm=20; rm2=0; R_POW=10
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=False, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=18, lib_name=lib_name)
    num_fps_generated += 1

    # radial resistors, simple
    rm2=0; w2=0
    type = "simple"; seriesname = "Radial_Power"; add_description = "https://www.vishay.com/docs/30218/cpcp-cpcf.pdf"; name_additions=[]
    w = 11.0; w2=w-2.0; h = 7.0; ddrill = 1.2; rm=5.0; rm2=0; R_POW=2
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=True, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=20.5, lib_name=lib_name)
    num_fps_generated += 1

    w = 12.0; w2=w-2.0; h = 8.0; ddrill = 1.2; rm=5.0; rm2=0; R_POW=3
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=True, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=24.99, lib_name=lib_name)
    num_fps_generated += 1

    w = 13.0; w2=w-2.0; h = 9.0; ddrill = 1.2; rm=5.0; rm2=0; R_POW=7
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=True, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=39, lib_name=lib_name)
    num_fps_generated += 1

    w = 16.1; w2=w-3; h = 9; ddrill = 1.4; rm=7.37; rm2=0; R_POW=10
    makeResistorRadial(generator_name=generator_name, seriesname=seriesname, rm=rm, w=w, h=h, ddrill=ddrill, R_POW=R_POW, rm2=rm2, vlines=True, w2=w2, type=type, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", name_additions=name_additions, specialtags=[], add_description=add_description,height3d=34.85, lib_name=lib_name)
    num_fps_generated += 1

    return num_fps_generated
