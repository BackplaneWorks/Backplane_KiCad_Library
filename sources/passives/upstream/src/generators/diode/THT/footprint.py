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
        # standard resistors: http://cdn-reichelt.de/documents/datenblatt/B400/1_4W%23YAG.pdf
    type = "cyl"

    d2=0
    R_POW = 0
    clname="D"
    lbname="Diode_THT"
    deco="diode"
    deco_kup="diode_KUP"
    num_fps_generated = 0
    seriesname = "DO-27"; w=9.52; d=5.33; ddrill=1.2; add_description=", http://www.slottechforum.com/slotinfo/Techstuff/CD2%20Diodes%20and%20Transistors/Cases/Diode%20DO-27.jpg"; name_additions=[]
    for rm in [12.7, 15.24]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2

    seriesname = "DO-41_SOD81"; w=5.2; d=2.7; ddrill=1.1; add_description=", https://www.diodes.com/assets/Package-Files/DO-41-Plastic.pdf"; name_additions=[]
    for rm in [7.62, 10.16, 12.7]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [2.54, 3.81, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2

    seriesname = "DO-34_SOD68"; w=3.04; d=1.6; ddrill=0.75; add_description=", https://www.nxp.com/docs/en/data-sheet/KTY83_SER.pdf"; name_additions=[]
    for rm in [7.62, 10.16, 12.7]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [2.54, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2

    seriesname = "DO-35_SOD27"; w=4; d=2; ddrill=0.8; add_description=", http://www.diodes.com/_files/packages/DO-35.pdf"; name_additions=[]
    for rm in [7.62, 10.16, 12.7]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [2.54, 3.81, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "A-405"; w=5.2; d=2.7; ddrill=0.9; add_description=", http://www.diodes.com/_files/packages/A-405.pdf"; name_additions=[]
    for rm in [7.62, 10.16, 12.7]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [2.54, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "DO-15"; w=7.6; d=3.6; ddrill=1.2; add_description=", http://www.diodes.com/_files/packages/DO-15.pdf"; name_additions=[]
    for rm in [10.16, 12.7, 15.24]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [2.54, 3.81, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "DO-201"; w=9.53; d=5.21; ddrill=1.3; add_description=", http://www.diodes.com/_files/packages/DO-201.pdf"; name_additions=[]
    for rm in [12.7, 15.24]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [3.81, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "DO-201AD"; w=9.5; d=5.2; ddrill=1.6; add_description=", http://www.diodes.com/_files/packages/DO-201AD.pdf"; name_additions=[]
    for rm in [12.7, 15.24]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [3.81, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "DO-201AE"; w=9; d=5.3; ddrill=1.3; add_description=", http://www.farnell.com/datasheets/529758.pdf"; name_additions=[]
    for rm in [12.7, 15.24]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [3.81, 5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "P600_R-6"; w=9.1; d=9.1; ddrill=1.6; add_description=", http://www.vishay.com/docs/88692/p600a.pdf, http://www.diodes.com/_files/packages/R-6.pdf"; name_additions=[]
    for rm in [12.7,20]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "5W"; w=8.9; d=3.7; ddrill=1.4; add_description=", http://www.diodes.com/_files/packages/8686949.gif"; name_additions=[]
    for rm in [10.16, 12.7]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [5.08]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "5KP"; w=7.62; d=9.53; ddrill=1.4; add_description=", http://www.diodes.com/_files/packages/8686949.gif"; name_additions=[]
    for rm in [10.16, 12.7]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "5KPW"; w=9; d=8; ddrill=1.6; add_description=", http://www.diodes.com/_files/packages/8686949.gif"; name_additions=[]
    for rm in [12.7]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [7.62]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    seriesname = "T-1"; w=3.2; d=2.6; ddrill=1; add_description=", http://www.diodes.com/_files/packages/T-1.pdf"; name_additions=[]
    for rm in [5.08, 10.16, 12.7]:
        makeResistorAxialHorizontal(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, w=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2,  x_3d=[0,0,0], s_3d=[1,1,1], has3d=1, specialfpname="", add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 1
    for rm in [2.54]:
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco_kup, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        makeResistorAxialVertical(generator_name=generator_name, seriesname=seriesname, rm=rm, rmdisp=rm, l=w, d=d, ddrill=ddrill, R_POW=R_POW, type=type, deco=deco, d2=d2, x_3d=[0, 0, 0], s_3d=[1,1,1], has3d=1, specialfpname="", largepadsx=0, largepadsy=0, add_description=add_description, name_additions=name_additions, classname=clname, lib_name=lbname, specialtags=[])
        num_fps_generated += 2
    return num_fps_generated
