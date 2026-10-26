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
from generators.tools.footprint.save_footprint import write_footprint

class FourUcon_TerminalBlock:

    classname = "TerminalBlock_4Ucon"


class FourUcon_H8_3_TerminalBlock(FourUcon_TerminalBlock):

    # Pins known to be available for this footprint type
    PINS = [2,3,4,5,6,7,8,9,10,11,12,13,14,15]

    def generateFootprint(self, pins: int, generator_name: str):

        rm = 3.5
        package_height = 8.3
        leftbottom_offset = [2.25, package_height - 3.7]
        ddrill = 1.3
        pad = [2.6, 2.6]
        bevel_height = [3.5]
        opening = [2.8, 3.75]
        opening_yoffset = package_height - 0.7 - opening[1]
        secondHoleDiameter = 2
        secondHoleOffset = [0, -(3.7 - 2.1)]
        thirdHoleDiameter = 0
        thirdHoleOffset = [0, 0]
        fourthHoleDiameter = 0
        fourthHoleOffset = [0, 0]
        fabref_offset = [0, 3]
        nibbleSize = None
        nibblePos = None

        itemno = 10691 + pins

        webpage = f"http://www.4uconnector.com/online/object/4udrawing/{itemno}.pdf"
        classname_description = f"Terminal Block 4Ucon ItemNo. {itemno}"
        footprint_name = f"TerminalBlock_4Ucon_1x{pins:02}_P{rm:3.2f}mm_Vertical"

        kicad_mod = makeTerminalBlockVertical(
            generator_name,
            footprint_name=footprint_name,
            pins=pins,
            rm=rm,
            package_height=package_height,
            leftbottom_offset=leftbottom_offset,
            ddrill=ddrill,
            pad=pad,
            opening=opening,
            opening_yoffset=opening_yoffset,
            bevel_height=bevel_height,
            secondHoleDiameter=secondHoleDiameter,
            secondHoleOffset=secondHoleOffset,
            thirdHoleDiameter=thirdHoleDiameter,
            thirdHoleOffset=thirdHoleOffset,
            fourthHoleDiameter=fourthHoleDiameter,
            fourthHoleOffset=fourthHoleOffset,
            nibbleSize=nibbleSize,
            nibblePos=nibblePos,
            fabref_offset=fabref_offset,
            tags_additional=[],
            lib_name=None,
            classname=self.classname,
            classname_description=classname_description,
            webpage=webpage,
        )

        kicad_mod.add_standard_3d_model_to_footprint(self.classname, footprint_name)
        write_footprint(kicad_mod, self.classname, generator_name)


class FourUCon_H7_TerminalBlock(FourUcon_TerminalBlock):

    PINS = [2,3,4,5,6,7,8,9,10,11,12,13,14,15]
    ITEM_NOS=[19963,20193,20001,20223,19964,10684,19965,10686,10687,10688,10689,10690,10691,10692]

    def generateFootprint(self, pins: int, generator_name: str):

        assert pins in self.PINS, f"Invalid number of pins: {pins}"
        index = self.PINS.index(pins)
        itemno = self.ITEM_NOS[index]

        rm=3.5
        package_height=7
        leftbottom_offset=[2.1, package_height-3.4]
        ddrill=1.2
        pad=[2.4,2.4]
        screw_diameter=2.75
        bevel_height=[1.5]
        slit_screw=False
        screw_pin_offset=[0,0]
        secondHoleDiameter=0
        secondHoleOffset=[0,0]
        thirdHoleDiameter=0
        thirdHoleOffset=[0,-4]
        fourthHoleDiameter=0
        fourthHoleOffset=[0,0]
        fabref_offset=[0,2.8]
        nibbleSize = None
        nibblePos = None

        webpage=f"http://www.4uconnector.com/online/object/4udrawing/{itemno}.pdf"
        classname_description=f"Terminal Block 4Ucon ItemNo. {itemno}"
        footprint_name=f"TerminalBlock_4Ucon_1x{pins:02}_P{rm:3.2f}mm_Horizontal"

        kicad_mod = makeTerminalBlockStd(
            generator_name,
            footprint_name=footprint_name,
            pins=pins,
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
            nibbleSize=nibbleSize,
            nibblePos=nibblePos,
            fabref_offset=fabref_offset,
            tags_additional=[],
            lib_name=None,
            classname=self.classname,
            classname_description=classname_description,
            webpage=webpage,
        )

        kicad_mod.add_standard_3d_model_to_footprint(self.classname, footprint_name)
        write_footprint(kicad_mod, self.classname, generator_name)


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    
    g = FourUcon_H8_3_TerminalBlock()
    for pins in g.PINS:
        g.generateFootprint(pins, generator_name)
    num_fps_generated += len(g.PINS)

    g = FourUCon_H7_TerminalBlock()
    for pins in g.PINS:
        g.generateFootprint(pins, generator_name)
    num_fps_generated += len(g.PINS)

    return num_fps_generated