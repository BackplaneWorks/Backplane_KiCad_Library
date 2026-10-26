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
from generators.tools.footprint.footprint_scripts_sip import *
from generators.tools.spec.base_spec import BaseSpec


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    pin_range = range(3, 14)
    for R in range(3, 14):
        pins=R+1
        makeResistorSIP(generator_name, pins, "R_Array_SIP%d" % (pins), "{0}-pin Resistor SIP pack".format(pins, R))
    #for R in range(3,6):
    #    pins=2*R
    #    makeResistorSIP(pins, "Resistor_ArrayParallel_SIP%d" % (R), "{0}-pin Resistor SIP pack, {1} parallel resistors".format(pins, R))
    #for R in range(3,6):
    #    pins=R+2
    #    makeResistorSIP(pins, "Resistor_ArrayDivider_SIP%d" % (R), "{0}-pin Resistor SIP pack, {1} voltage dividers = {2} resistors".format(pins, R, 2*R))
    return len(pin_range)