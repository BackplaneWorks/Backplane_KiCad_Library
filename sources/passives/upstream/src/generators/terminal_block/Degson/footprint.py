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

from KicadModTree import *
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

    classname = "TerminalBlock_Degson"
    # from manufacturer homepage, not all stores list all the poles
    pins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 18, 19, 20, 24, 44, 45]
    rm = 3.5  # pitch
    package_height = 12  # overall extension in y-direction
    leftbottom_offset = [3.2, 9.65, 1.8]
    ddrill = 1.2
    pad = [2, 3]
    bevel_height = [4.7]
    vsegment_lines_offset = [-1.75]
    even_pin_offset = 5
    opening = [2.9, 2.3]
    opening_xoffset = 0
    opening_yoffset = 2  # estimated
    opening_elliptic = True
    fabref_offset = [0, -1]
    for p in pins:
        name = "DG250-3.5-{:02d}P".format(p)
        webpage = "https://www.degson.com/content/details_552_879717.html?lang=en"
        classname_description = "Terminal Block Degson {0}".format(name)
        footprint_name = (
            "TerminalBlock_Degson_{0}_1x{1:02}_P{2:3.2f}mm_45Degree".format(name, p, rm)
        )
        makeTerminalBlock45Degree(
            generator_name,
            footprint_name=footprint_name,
            pins=p,
            rm=rm,
            package_height=package_height,
            leftbottom_offset=leftbottom_offset,
            ddrill=ddrill,
            pad=pad,
            even_pin_offset=even_pin_offset,
            vsegment_lines_offset=vsegment_lines_offset,
            opening=opening,
            opening_xoffset=opening_xoffset,
            opening_yoffset=opening_yoffset,
            opening_elliptic=opening_elliptic,
            bevel_height=bevel_height,
            fabref_offset=fabref_offset,
            tags_additional=[],
            lib_name=classname,
            classname=classname,
            classname_description=classname_description,
            webpage=webpage,
        )
    return len(pins)
