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
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.footprint.footprint_scripts_DIP import *


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    footprints_made = 0

    # common settings
    overlen_top=1.27
    overlen_bottom=1.27
    rm=2.54
    ddrill=0.8
    pad=[1.6,1.6]

    # DIP-switches:
    pins=[2,4,6,8,10,12,14,16,18,20,22,24]
    pinrow_distance = 7.62
    package_width = 9.78
    switch_width=4.06
    switch_height=1.27
    overlen_top = 2.36
    overlen_bottom = 2.36
    package_width_narrow = 6.7
    switch_width_narrow = 3.62
    switch_height_narrow = 1.27
    overlen_top_narrow = 2.05
    overlen_bottom_narrow = 2.05
    pad_smd=[2.44,1.12]
    pinrow_distance_smd=8.61
    pinrow_distance_smd_J=6.73
    pad_smd_J=[2.16,1.12]
    switch_width_piano=1.8
    switch_height_piano=1.5
    package_width_piano=10.8
    overlen_top_piano = 2.05
    overlen_bottom_piano = 2.05
    switchtype="SPST"

    for p in pins:
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad, switch_width, switch_height, 'Slide', False, [], webpage="e.g. https://www.ctscorp.com/wp-content/uploads/206-208.pdf",switchtype=switchtype)
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width_narrow, overlen_top_narrow, overlen_bottom_narrow, ddrill, pad, switch_width_narrow, switch_height_narrow, 'Slide', False, ["LowProfile"], webpage="e.g. https://www.ctscorp.com/wp-content/uploads/209-210.pdf",switchtype=switchtype)
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width_piano, overlen_top_piano, overlen_bottom_piano, ddrill, pad, switch_width_piano, switch_height_piano, 'Piano', False, [], webpage="",switchtype=switchtype)

        makeDIPSwitch(generator_name, p, rm, pinrow_distance_smd, package_width_narrow, overlen_top_narrow, overlen_bottom_narrow, ddrill, pad_smd, switch_width_narrow, switch_height_narrow, 'Slide', True,["SMD","LowProfile"], 'Button_Switch_SMD', webpage="e.g. https://www.ctscorp.com/wp-content/uploads/219.pdf",switchtype=switchtype)
        makeDIPSwitch(generator_name, p, rm, pinrow_distance_smd, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, switch_width, switch_height, 'Slide', True,["SMD"], 'Button_Switch_SMD', webpage="e.g. https://www.ctscorp.com/wp-content/uploads/204.pdf",switchtype=switchtype)
        makeDIPSwitch(generator_name, p, rm, pinrow_distance_smd_J, package_width_narrow, overlen_top_narrow, overlen_bottom_narrow, ddrill, pad_smd_J, switch_width_narrow, switch_height_narrow, 'Slide', True,["SMD","LowProfile","JPin"], 'Button_Switch_SMD', webpage="e.g. https://www.ctscorp.com/wp-content/uploads/219.pdf",switchtype=switchtype)
    footprints_made += 6 * len(pins)

    pins=[4,6,8,10,12,14,16,18,20,22,24]
    switch_width_piano=1.14
    switch_height_piano=1.52
    package_width_piano=9.78
    overlen_top_piano = (7.26-2.54)/2
    overlen_bottom_piano = overlen_top_piano

    for p in pins:
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width_piano, overlen_top_piano, overlen_bottom_piano, ddrill, pad, switch_width_piano, switch_height_piano, 'Piano', False, device_name="CTS_Series194-{0}MSTN".format(int(p/2)), webpage="https://www.ctscorp.com/wp-content/uploads/194-195.pdf",switchtype=switchtype)
    footprints_made += len(pins)

    # Copal CVS DIP-switches (http://www.nidec-copal-electronics.com/e/catalog/switch/cvs.pdf):
    pins = [2, 4, 6, 8, 16]
    rm = 1
    pinrow_distance = 5.9
    package_width = 4.7
    switch_width = 2
    switch_height = 0.5
    overlen_top = 1
    overlen_bottom = 1
    ddrill = 0
    pad_smd = [1.2, 0.5]

    for p in pins:
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, switch_width,
                    switch_height, 'Slide', True, [], "Button_Switch_SMD", [0, 0, 0], [1, 1, 1],
                    [0, 0, 0], "", True, [0.7, 0.7], 0.2, 0, webpage="http://www.nidec-copal-electronics.com/e/catalog/switch/cvs.pdf", device_name="Copal_CVS-{0:02}xB".format(int(p/2)),switchtype=switchtype)
    footprints_made += len(pins)

    # Omron A6H DIP-switches (https://www.omron.com/ecb/products/pdf/en-a6h.pdf):
    pins = [4,8,12,16,20]
    rm = 1.27
    pinrow_distance = 6.15
    package_width = 4.5
    switch_width = 3.2
    switch_height = 0.5
    overlen_top = 1.27
    overlen_bottom = 1.27
    ddrill = 0
    pad_smd = [1.25, 0.76]

    for p in pins:
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, switch_width,
                    switch_height, 'Slide', True, [], "Button_Switch_SMD", [0, 0, 0], [1, 1, 1],
                    [0, 0, 0], "", True, webpage="https://www.omron.com/ecb/products/pdf/en-a6h.pdf", device_name="Omron_A6H-{0}101".format(int(p/2)),switchtype=switchtype)
    footprints_made += len(pins)

    # Omron A6S DIP-switches (http://omronfs.omron.com/en_US/ecb/products/pdf/en-a6s.pdf):
    pins = [2,4,6,8,10,12,14,16,18,20]
    rm = 2.54
    pinrow_distance = 8.9
    package_width = 6.2
    switch_width = 3
    switch_height = 1.1
    overlen_top = 1.74
    overlen_bottom = 1.74
    ddrill = 0
    pad_smd = [1.5, 1.1]

    for p in pins:
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, switch_width,
                    switch_height, 'Slide', True, [], "Button_Switch_SMD", [0, 0, 0], [1, 1, 1],
                    [0, 0, 0], "", True, webpage="http://omronfs.omron.com/en_US/ecb/products/pdf/en-a6s.pdf", device_name="Omron_A6S-{0}10x".format(int(p/2)),switchtype=switchtype)
    footprints_made += len(pins)

    # Copal CHS DIP-switches (http://www.nidec-copal-electronics.com/e/catalog/switch/chs.pdf):
    pins = [2, 4, 8, 12, 16, 20]
    rm = 1.27
    pinrow_distance = 5.08
    pinrow_distanceB = 7.62
    package_width = 5.4
    switch_width = 3
    switch_height = 0.5
    overlen_top = 1.27
    overlen_bottom = 1.27
    ddrill = 0
    pad_smd = [1.6, 0.76]

    for p in pins:
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, switch_width,
                    switch_height, 'Slide', True,["SMD","JPin"], "Button_Switch_SMD", [0, 0, 0], [1, 1, 1],
                    [0, 0, 0], "", True, webpage="http://www.nidec-copal-electronics.com/e/catalog/switch/chs.pdf", device_name="Copal_CHS-{0:02}A".format(int(p/2)),switchtype=switchtype)
        makeDIPSwitch(generator_name, p, rm, pinrow_distanceB, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, switch_width,
                    switch_height, 'Slide', True,["SMD"], "Button_Switch_SMD", [0, 0, 0], [1, 1, 1],
                    [0, 0, 0], "", True, webpage="http://www.nidec-copal-electronics.com/e/catalog/switch/chs.pdf", device_name="Copal_CHS-{0:02}B".format(int(p/2)),switchtype=switchtype)
    footprints_made += 2*len(pins)

    # KingTek DSHPxxTS DIP-switches (http://www.kingtek.net.cn/pic/201601201417455112.pdf):
    pins = [4,6,8,10,12,14,16,18,20]
    rm = 1.27
    pinrow_distance = (8.89+6.35)/2
    package_width = 5.4
    switch_width = 2
    switch_height = 0.8
    overlen_top = (9.22-(5*1.27))/2
    overlen_bottom = overlen_top
    ddrill = 0
    pad_smd = [(8.89-6.35)/2, 0.76]

    for p in pins:
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, switch_width,
                    switch_height, 'Slide', True, [], "Button_Switch_SMD", [0, 0, 0], [1, 1, 1],
                    [0, 0, 0], "", True, webpage="http://www.kingtek.net.cn/pic/201601201417455112.pdf", device_name="KingTek_DSHP{0:02}TS".format(int(p/2)),switchtype=switchtype)
    footprints_made += len(pins)

    # KingTek DSHPxxTJ DIP-switches (http://www.kingtek.net.cn/pic/201601201446313350.pdf):
    pins = [4,6,8,10,12,14,16,18,20]
    rm = 1.27
    pinrow_distance = (7.9+2.6)/2
    package_width = 5.4
    switch_width = 2
    switch_height = 0.8
    overlen_top = (6.88-(3*1.27))/2
    overlen_bottom = overlen_top
    ddrill = 0
    pad_smd = [(7.9-2.6)/2, 0.76]

    for p in pins:
        makeDIPSwitch(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, switch_width,
                    switch_height, 'Slide', True, ["JPin"], "Button_Switch_SMD", [0, 0, 0], [1, 1, 1],
                    [0, 0, 0], "", True, webpage="http://www.kingtek.net.cn/pic/201601201446313350.pdf", device_name="KingTek_DSHP{0:02}TJ".format(int(p/2)),switchtype=switchtype)
    footprints_made += len(pins)
    return footprints_made
