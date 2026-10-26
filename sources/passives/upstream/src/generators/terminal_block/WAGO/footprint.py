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
from ..footprint_scripts_terminal_blocks import *

from generators.tools.spec.base_spec import BaseSpec

# These terminal blocks can be split and joined as needed to make terminal strips
# of any length, the last terminal in the row usually gets a cover plate.
# They are usually sold as loose terminals and cover plates but can be ordered
# as pre-assembled strips of various terminal counts as well. Not all the types
# are available in all pre-assembled sizes, though.
# The 804-xx series seems to be sold only pre-assembled in strips of two terminals
# and more (12/2024).


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    classname="TerminalBlock_WAGO"

    # 2 through 12 is available from WAGO as of 2024
    # 1, 16, 24 used to be in the library in addition
    pins=[ *range(2, 1+12), 1, 16, 24 ]
    rm=7.5
    package_height=15
    leftbottom_offset=[2.75, 6.7, 3.75]
    ddrill=1.2
    pad=[2,3]
    screw_diameter=2.2
    bevel_height=[2.9]
    vsegment_lines_offset=[-1.25]
    opening=[2.9,2.3]
    opening_xoffset=1.25
    opening_yoffset=1.45
    opening_elliptic=True
    secondDrillDiameter=ddrill
    secondDrillOffset=[2.5,-5]
    secondDrillPad=pad
    secondHoleDiameter=[4,4.4]
    secondHoleOffset=[1.25,0]
    thirdHoleDiameter=[4,1]
    thirdHoleOffset=[1.25,0]
    fourthHoleDiameter=3#4
    fourthHoleOffset=[1.25,-5.75]
    fifthHoleDiameter=0
    fifthHoleOffset=[2.5,-0.75]
    secondEllipseSize=[0,0]
    secondEllipseOffset=[1.25,2.5]
    fabref_offset=[0,-1]
    nibbleSize = None
    nibblePos = None
    for p in pins:
        name="804-{0}".format(300+p);
        webpage="";
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_45Degree".format(name, rm, p)
        makeTerminalBlock45Degree(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad, vsegment_lines_offset=vsegment_lines_offset,
                                opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset, opening_elliptic=opening_elliptic,
                                bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset, fifthHoleDiameter=fifthHoleDiameter,fifthHoleOffset=fifthHoleOffset,
                                secondDrillDiameter=secondDrillDiameter,secondDrillOffset=secondDrillOffset,secondDrillPad=secondDrillPad,
                                secondEllipseSize=secondEllipseSize,secondEllipseOffset=secondEllipseOffset,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += len(pins)

    # 2 through 16 is available from WAGO as of 2024
    # 1, 24 used to be in the library in addition
    pins=[ *range(2, 1+16), 1, 24 ]
    rm=5
    package_height=15
    leftbottom_offset=[2.75, 6.7, 3.75]
    ddrill=1.2
    pad=[2,3]
    screw_diameter=2.2
    bevel_height=[2.9]
    vsegment_lines_offset=[-1.25]
    opening=[2.9,2.3]
    opening_xoffset=1.25
    opening_yoffset=1.45
    opening_elliptic=True
    secondDrillDiameter=ddrill
    secondDrillOffset=[2.5,-5]
    secondDrillPad=pad
    secondHoleDiameter=[4,4.4]
    secondHoleOffset=[1.25,0]
    thirdHoleDiameter=[4,1]
    thirdHoleOffset=[1.25,0]
    fourthHoleDiameter=3#4
    fourthHoleOffset=[1.25,-5.75]
    fifthHoleDiameter=0
    fifthHoleOffset=[1.25,-0.75]
    secondEllipseSize=[0,0]
    secondEllipseOffset=[1.25,2.5]
    fabref_offset=[0,-1]
    nibbleSize = None
    nibblePos = None
    for p in pins:
        name="804-{0}".format(100+p);
        webpage="";
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_45Degree".format(name, rm, p)
        makeTerminalBlock45Degree(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad,  vsegment_lines_offset=vsegment_lines_offset,
                                opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset, opening_elliptic=opening_elliptic,
                                bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset, fifthHoleDiameter=fifthHoleDiameter,fifthHoleOffset=fifthHoleOffset,
                                secondDrillDiameter=secondDrillDiameter,secondDrillOffset=secondDrillOffset,secondDrillPad=secondDrillPad,
                                secondEllipseSize=secondEllipseSize,secondEllipseOffset=secondEllipseOffset,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += len(pins)

    # Available as individual terminals
    # Provide 1 through 16 for the sake of completeness, and 24, 36, 48  for historic reasons
    pins=[ *range(1, 1+16), 24, 36, 48 ]
    rm=5
    package_height=14
    leftbottom_offset=[3.5, 9, 3.8]
    ddrill=1.15
    pad=[1.5,3]
    screw_diameter=2.2
    bevel_height=[1,6.7,9.5]
    opening=[4,3.3]
    opening_xoffset=0.5
    opening_yoffset=1.3#package_height-leftbottom_offset[1]-opening[1]/2
    secondDrillDiameter=ddrill
    secondDrillOffset=[0,5]
    secondDrillPad=pad
    secondHoleDiameter=[5,14]
    secondHoleOffset=[0.5,2]
    thirdHoleDiameter=[4,1]
    thirdHoleOffset=[0.5,3.2]
    fourthHoleDiameter=[1,2.5]
    fourthHoleOffset=[0.5,-3.4]
    fabref_offset=[0,-1]
    nibbleSize = None
    nibblePos = None
    for p in pins:
        name="236-{0}".format(100+p);
        webpage="";
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_45Degree".format(name, rm, p)
        makeTerminalBlock45Degree(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad,
                                opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset,
                                bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
        name="236-{0}".format(400+p);
        webpage="";
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_45Degree".format(name, rm, p)
        makeTerminalBlock45Degree(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad,
                                opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset,
                                bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                secondDrillDiameter=secondDrillDiameter,secondDrillOffset=secondDrillOffset,secondDrillPad=secondDrillPad,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 2*len(pins)

    # Available as individual terminals
    # Provide 1 through 16 for the sake of completeness, and 24 for historic reasons
    pins=[ *range(1, 1+16), 24 ]
    rm=7.5
    package_height=14
    leftbottom_offset=[3.5, 9, 6.3]
    ddrill=1.15
    pad=[1.5,3]
    screw_diameter=2.2
    bevel_height=[1,6.7,9.5]
    opening=[4,3.3]
    opening_xoffset=0.5
    opening_yoffset=1.3#package_height-leftbottom_offset[1]-opening[1]/2
    secondDrillDiameter=ddrill
    secondDrillOffset=[0,5]
    secondDrillPad=pad
    secondHoleDiameter=[rm,package_height]
    secondHoleOffset=[1.75,2]
    thirdHoleDiameter=[4,1]
    thirdHoleOffset=[0.5,3.2]
    fourthHoleDiameter=1,2.5
    fourthHoleOffset=[0.5,-3.4]
    fabref_offset=[0,-1]
    nibbleSize = None
    nibblePos = None
    for p in pins:
        name="236-{0}".format(200+p);
        webpage="";
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_45Degree".format(name, rm, p)
        makeTerminalBlock45Degree(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad,
                                opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset,
                                bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
        name="236-{0}".format(500+p);
        webpage="";
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_45Degree".format(name, rm, p)
        makeTerminalBlock45Degree(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad,
                                opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset,
                                bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                secondDrillDiameter=secondDrillDiameter,secondDrillOffset=secondDrillOffset,secondDrillPad=secondDrillPad,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 2*len(pins)

    # Available as individual terminals
    # Provide 1 through 16 for the sake of completeness, and 24 for historic reasons
    pins=[ *range(1, 1+16), 24 ]
    rm=10
    package_height=14
    leftbottom_offset=[3.5, 9, 8.8]
    ddrill=1.15
    pad=[1.5,3]
    screw_diameter=2.2
    bevel_height=[1,6.7,9.5]
    opening=[4,3.3]
    opening_xoffset=0.5
    opening_yoffset=1.3#package_height-leftbottom_offset[1]-opening[1]/2
    secondDrillDiameter=ddrill
    secondDrillOffset=[0,5]
    secondDrillPad=pad
    secondHoleDiameter=[rm,package_height]
    secondHoleOffset=[3,2]
    thirdHoleDiameter=[4,1]
    thirdHoleOffset=[0.5,3.2]
    fourthHoleDiameter=1,2.5
    fourthHoleOffset=[0.5,-3.4]
    fabref_offset=[0,-1]
    nibbleSize = None
    nibblePos = None
    for p in pins:
        name="236-{0}".format(300+p);
        webpage="";
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_45Degree".format(name, rm, p)
        makeTerminalBlock45Degree(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad,
                                opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset,
                                bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
        name="236-{0}".format(600+p);
        webpage="";
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_45Degree".format(name, rm, p)
        makeTerminalBlock45Degree(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad,
                                opening=opening, opening_xoffset=opening_xoffset, opening_yoffset=opening_yoffset,
                                bevel_height=bevel_height, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                secondDrillDiameter=secondDrillDiameter,secondDrillOffset=secondDrillOffset,secondDrillPad=secondDrillPad,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description, webpage=webpage)
    num_fps_generated += 2*len(pins)

    # WAGO 2601

    pins=[2,3,4,5,6,8,9,10,11,12]
    rm=3.5
    package_height=14.5
    leftbottom_offset=[2.44, 5.35, 2.56]
    ddrill=1.2
    pad=[1.5,2.3]
    secondDrillOffset=[0,-5]

    for p in pins:
        name="2601-11{0:02}".format(p);
        webpage="https://www.wago.com/global/pcb-terminal-blocks-and-pluggable-connectors/pcb-terminal-block/p/{0}".format(name);
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_Horizontal".format(name, rm, p)

        makeTerminalBlockStd(generator_name, footprint_name=footprint_name,
            pins=p,
            rm=rm,
            package_height=package_height,
            leftbottom_offset=leftbottom_offset,
            ddrill=ddrill,
            pad=pad,
            screw_diameter=0,
            bevel_height=[],
            slit_screw=False,
            screw_pin_offset=[0,0],
            secondHoleDiameter=0,
            secondHoleOffset=[0,0],
            thirdHoleDiameter=0,
            thirdHoleOffset=[0,0],
            fourthHoleDiameter=0,
            fourthHoleOffset=[0,0],
            secondDrillDiameter=ddrill,
            secondDrillOffset=secondDrillOffset,
            secondDrillPad=pad,
            fabref_offset=[0,0],
            stackable=False,
            tags_additional=[],
            lib_name=classname,
            classname=classname,
            classname_description="Terminal Block WAGO {0}".format(name),
            webpage=webpage,
        )
    num_fps_generated += len(pins)

    pins=[2,3,4,5,6,7,8,9,10,11,12,14,24]
    rm=3.5
    package_height=12.75
    leftbottom_offset=[2.56, 5.45, 2.44]
    ddrill=1.2
    pad=[1.5,2.3]
    secondDrillOffset=[0,-5]

    for p in pins:
        name="2601-31{0:02}".format(p);
        webpage="https://www.wago.com/global/pcb-terminal-blocks-and-pluggable-connectors/pcb-terminal-block/p/{0}".format(name);
        classname_description="Terminal Block WAGO {0}".format(name);
        footprint_name="TerminalBlock_WAGO_{0}_1x{2:02}_P{1:3.2f}mm_Vertical".format(name, rm, p)

        makeTerminalBlockStd(generator_name, footprint_name=footprint_name,
            pins=p,
            rm=rm,
            package_height=package_height,
            leftbottom_offset=leftbottom_offset,
            ddrill=ddrill,
            pad=pad,
            screw_diameter=0,
            bevel_height=[],
            slit_screw=False,
            screw_pin_offset=[0,0],
            secondHoleDiameter=0,
            secondHoleOffset=[0,0],
            thirdHoleDiameter=0,
            thirdHoleOffset=[0,0],
            fourthHoleDiameter=0,
            fourthHoleOffset=[0,0],
            secondDrillDiameter=ddrill,
            secondDrillOffset=secondDrillOffset,
            secondDrillPad=pad,
            fabref_offset=[0,0],
            stackable=False,
            tags_additional=[],
            lib_name=classname,
            classname=classname,
            classname_description="Terminal Block WAGO {0}".format(name),
            webpage=webpage,
        )
    num_fps_generated += len(pins)
    return num_fps_generated
