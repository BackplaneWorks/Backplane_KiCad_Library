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

from ..footprint_scripts_terminal_blocks import makeTerminalBlockStd

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.footprint.save_footprint import write_footprint


# Generic properties
fplib_name = "TerminalBlock" # Name of the footprint library
# Series datasheet: https://www.cnmaixu.com/Sites/maixu/static/upload/file/20240108/1704697250343193.pdf
datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2309150913_MAX-MX126-5-0-03P-GN01-Cu-S-A_C5188435.pdf"

available_pincounts = range(2, 24+1)
rm = 5.0 # Distance beteen any
package_height = 7.8 # Y size of footprint, not height above PCB!
leftbottom_offset=[
    3,
    package_height-4,
    2.5, # This makes the size asymmetric: 0.5mm less wide on the right
]
ddrill=1.3
pad=[2.8,2.8] # Guess, Based on MetzConnect Type011
screw_diameter=3.2 # Guess, Based on MetzConnect Type011
bevel_height=[2,package_height-4.5,package_height-3.5] # Guess, Based on MetzConnect Type011
slit_screw = True # Draw "slit" in F.Fab rendering
screw_pin_offset=[0,0] # ?
secondHoleDiameter=0 # ?
secondHoleOffset=[0,0] # ?
thirdHoleDiameter=0 # ?
thirdHoleOffset=[0,-4] # ?
fourthHoleDiameter=0 # ?
fourthHoleOffset=[0,0] # ?
fabref_offset=[0,2.75]  # ?
nibbleSize = None # ?
nibblePos = None # ?


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    for pins in available_pincounts:
        generateFootprint(pins, generator_name)
    return len(available_pincounts)
    

def part_mpn(pincount):
    return f"MX126-{rm:.1f}-{pincount:02}P"

def get_footprint_name(pincount: int):
    name = part_mpn(pincount)
    return f"TerminalBlock_MaiXu_{name}_1x{pincount:02}_P{rm:3.2f}mm"

def classname_description(pincount: int):
    name = part_mpn(pincount)
    return f"terminal block MaiXu {name}"

def generateFootprint(pincount: int, generator_name: str):
    """Generate all footprints"""

    footprint_name = get_footprint_name(pincount)
    classname = fplib_name

    kicad_mod = makeTerminalBlockStd(
        generator_name,
        footprint_name=footprint_name,
        pins=pincount,
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
        classname=classname,
        classname_description=classname_description(pincount),
        webpage=datasheet,
    )

    kicad_mod.add_standard_3d_model_to_footprint(classname, footprint_name)
    write_footprint(kicad_mod, classname, generator_name)
