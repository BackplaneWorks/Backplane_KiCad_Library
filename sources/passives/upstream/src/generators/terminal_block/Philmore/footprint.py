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


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    classname="TerminalBlock_Philmore"

    pins=range(2,3+1)
    rm=5
    package_height=10.2
    leftbottom_offset=[rm/2, 5.4]
    ddrill=1.2
    pad=[2.4,2.4]
    screw_diameter=2.75
    bevel_height=[0.5,1.6]
    slit_screw=False
    screw_pin_offset=[0,0]
    secondHoleDiameter=0
    secondHoleOffset=[0,0]
    thirdHoleDiameter=0
    thirdHoleOffset=[0,-4]
    fourthHoleDiameter=0
    fourthHoleOffset=[0,0]
    fabref_offset=[0,2.5]
    nibbleSize = None
    nibblePos = None
    for p in pins:
        name="TB13{0}".format(p);
        webpage="http://www.philmore-datak.com/mc/Page%20197.pdf";
        classname_description="Terminal Block Philmore ".format(name);
        footprint_name="TerminalBlock_Philmore_{0}_1x{2:02}_P{1:3.2f}mm_Horizontal".format(name, rm, p)
        makeTerminalBlockStd(generator_name, footprint_name=footprint_name,
                                pins=p, rm=rm,
                                package_height=package_height, leftbottom_offset=leftbottom_offset,
                                ddrill=ddrill, pad=pad, screw_diameter=screw_diameter, bevel_height=bevel_height, slit_screw=slit_screw, screw_pin_offset=screw_pin_offset, secondHoleDiameter=secondHoleDiameter, secondHoleOffset=secondHoleOffset, thirdHoleDiameter=thirdHoleDiameter, thirdHoleOffset=thirdHoleOffset, fourthHoleDiameter=fourthHoleDiameter, fourthHoleOffset=fourthHoleOffset,
                                nibbleSize=nibbleSize, nibblePos=nibblePos, fabref_offset=fabref_offset,
                                tags_additional=[], lib_name=classname, classname=classname, classname_description=classname_description,
                                webpage=webpage)
    return len(pins)
