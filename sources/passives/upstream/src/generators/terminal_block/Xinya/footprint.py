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
    classname = "TerminalBlock"

    pins = range(2, 24)
    rm = 2.54
    package_height = 6.5
    leftbottom_offset = [1.52, 3.4]
    ddrill = 1.2
    pad = [2, 2]
    screw_diameter = 2
    bevel_height = [0.8, 1.8, 4.9]
    slit_screw = True
    screw_pin_offset = [0, 0]
    secondDrillDiameter = 0
    secondDrillOffset = [0, 0]
    secondDrillPad = [0, 0]
    secondHoleDiameter = 0
    secondHoleOffset = [0, 0]
    thirdHoleDiameter = 0
    thirdHoleOffset = [0, 0]
    fourthHoleDiameter = 0
    fourthHoleOffset = [0, 0]
    fabref_offset = [0, 2.0]
    nibbleSize = None
    nibblePos = None

    for p in pins:
        name = "XY308-{0:3.2f}-{1}P".format(rm, p)
        webpage = "http://www.xinyaelectronic.com/product/xy308-254"
        classname_description = "Terminal Block Xinya {0}".format(name)
        footprint_name = (
            "TerminalBlock_Xinya_{0}_1x{2:02}_P{1:3.2f}mm_Horizontal".format(
                name, rm, p
            )
        )
        makeTerminalBlockStd(
            generator_name,
            footprint_name=footprint_name,
            pins=p,
            rm=rm,
            package_height=package_height,
            leftbottom_offset=leftbottom_offset,
            ddrill=ddrill,
            pad=pad,
            screw_diameter=screw_diameter,
            bevel_height=bevel_height,
            slit_screw=slit_screw,
            screw_pin_offset=screw_pin_offset,
            secondHoleDiameter=secondHoleDiameter,
            secondHoleOffset=secondHoleOffset,
            thirdHoleDiameter=thirdHoleDiameter,
            thirdHoleOffset=thirdHoleOffset,
            fourthHoleDiameter=fourthHoleDiameter,
            fourthHoleOffset=fourthHoleOffset,
            secondDrillDiameter=secondDrillDiameter,
            secondDrillOffset=secondDrillOffset,
            secondDrillPad=secondDrillPad,
            nibbleSize=nibbleSize,
            nibblePos=nibblePos,
            fabref_offset=fabref_offset,
            tags_additional=[],
            lib_name=classname,
            classname=classname,
            classname_description=classname_description,
            webpage=webpage,
        )
    return len(pins)
