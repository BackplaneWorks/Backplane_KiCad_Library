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
from generators.tools.footprint.footprint_scripts_DIP import makeDIP
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.cli_args import CLI_ARGS


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    output_dir = CLI_ARGS.output_dir_footprints

    # common settings
    overlen_top=1.27
    overlen_bottom=1.27
    rm=2.54
    ddrill=0.8
    pad=[1.6,1.6]
    pad_large=[2.4,1.6]
    pad_smdsocket=[3.1,1.6]
    pad_smdsocket_small=[1.6,1.6]

    # narrow 7.62 DIPs
    pins=[4,6,8,10,12,14,16,18,20,22,24,28]
    pinrow_distance=7.62
    package_width=6.35
    socket_width=pinrow_distance+2.54
    for p in pins:
        makeDIP(generator_name, p,rm,pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad,False,0,0,0, outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, 0,0,0, [], ["LongPads"], outdir=output_dir)
        socket_height = (p / 2 - 1) * rm + 2.54
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad, False, socket_width,socket_height,0, ["Socket"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, socket_width,socket_height,0,  ["Socket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket, True, socket_width,socket_height,1.27, ["SMDSocket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket_small, True,socket_width, socket_height, 0, ["SMDSocket"], ["SmallPads"], outdir=output_dir)
        num_fps_generated += 6

    # narrow 7.62 DIPs
    pins=[4,6,8,10,12,14,16,]
    pinrow_distance=10.16
    package_width=6.35
    socket_width=pinrow_distance+2.54
    for p in pins:
        makeDIP(generator_name, p,rm,pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad,False,0,0,0, outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, 0,0,0, [], ["LongPads"], outdir=output_dir)
        num_fps_generated += 2
    # mid 10.16 DIPs
    pins=[22,24]
    pinrow_distance=10.16
    package_width=9.14
    socket_width=pinrow_distance+2.54
    for p in pins:
        makeDIP(generator_name, p,rm,pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad,False,0,0,0, outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, 0,0,0, [], ["LongPads"], outdir=output_dir)
        socket_height = (p / 2 - 1) * rm + 2.54
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad, False, socket_width,socket_height,0, ["Socket"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, socket_width,socket_height,0,  ["Socket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket, True,
            socket_width, socket_height, 1.27, ["SMDSocket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket_small, True,
            socket_width, socket_height, 0, ["SMDSocket"], ["SmallPads"], outdir=output_dir)
        num_fps_generated += 6

    # mid 15.24 DIPs
    pins=[24,26,28,32,40,42,48,64]
    pinrow_distance=15.24
    package_width=14.73
    socket_width=pinrow_distance+2.54
    for p in pins:
        makeDIP(generator_name, p,rm,pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad,False,0,0,0, outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, 0,0,0, [], ["LongPads"], outdir=output_dir)
        socket_height = (p / 2 - 1) * rm + 2.54
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad, False, socket_width,socket_height,0, ["Socket"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, socket_width,socket_height,0,  ["Socket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket, True,
            socket_width, socket_height, 1.27, ["SMDSocket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket_small, True,
            socket_width, socket_height, 0, ["SMDSocket"], ["SmallPads"], outdir=output_dir)
        num_fps_generated += 6

    # large 22.86 DIPs
    pins=[64]
    pinrow_distance=22.86
    package_width=22.35
    socket_width=pinrow_distance+2.54
    for p in pins:
        makeDIP(generator_name, p,rm,pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad,False,0,0,0, outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, 0,0,0, [], ["LongPads"], outdir=output_dir)
        socket_height = (p / 2 - 1) * rm + 2.54
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad, False, socket_width,socket_height,0, ["Socket"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, socket_width,socket_height,0,  ["Socket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket, True,
            socket_width, socket_height, 1.27, ["SMDSocket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket_small, True,
            socket_width, socket_height, 0, ["SMDSocket"], ["SmallPads"], outdir=output_dir)
        num_fps_generated += 6

    # large 25.4 DIPs
    pins=[40,64]
    pinrow_distance=25.4
    package_width=24.89
    socket_width=pinrow_distance+2.54
    for p in pins:
        makeDIP(generator_name, p,rm,pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad,False,0,0,0, outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, 0,0,0, [], ["LongPads"], outdir=output_dir)
        socket_height = (p / 2 - 1) * rm + 2.54
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad, False, socket_width,socket_height,0, ["Socket"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, socket_width,socket_height,0,  ["Socket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket, True,
            socket_width, socket_height, 1.27, ["SMDSocket"], ["LongPads"], outdir=output_dir)
        makeDIP(generator_name, p, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_smdsocket_small, True,
            socket_width, socket_height, 0, ["SMDSocket"], ["SmallPads"], outdir=output_dir)
        num_fps_generated += 6

    # special SMD footprints
    smd_pins=[4,6,8,10,12,14,16,18,20,22,24,32]
    pad_smd = [2, 1.78]
    smd_pinrow_distances=[7.62, 9.53, 11.48]
    package_width=6.35
    for p in smd_pins:
        for prd in smd_pinrow_distances:
            makeDIP(generator_name, p, rm, prd, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, True,  0,0,0, [], [], "Package_DIP", [0, 0, 0], [1, 1, 1], [0, 0, 0], 'SMDIP', 'surface-mounted (SMD) DIP', 'SMD DIP DIL PDIP SMDIP', outdir=output_dir)
            num_fps_generated += 1

    smd_pins=[4,6,8,10,12,14,16,18,20,22]
    pad_smd = [1.5, 1.78]
    smd_pinrow_distances=[9.53]
    package_width=6.35
    for p in smd_pins:
        for prd in smd_pinrow_distances:
            makeDIP(generator_name, p, rm, prd, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, True,  0,0,0, ['Clearance8mm'], [], "Package_DIP", [0, 0, 0], [1, 1, 1], [0, 0, 0], 'SMDIP', 'surface-mounted (SMD) DIP', 'SMD DIP DIL PDIP SMDIP', outdir=output_dir)
            num_fps_generated += 1

    smd_pins=[24,28,32,40,42,48,64]
    pad_smd = [2, 1.78]
    smd_pinrow_distances=[15.24]
    package_width=14.73
    for p in smd_pins:
        for prd in smd_pinrow_distances:
            makeDIP(generator_name, p, rm, prd, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, True,  0,0,0, [], [],"Package_DIP", [0, 0, 0], [1, 1, 1], [0, 0, 0], 'SMDIP', 'surface-mounted (SMD) DIP', 'SMD DIP DIL PDIP SMDIP', outdir=output_dir)
            num_fps_generated += 1
    smd_pins=[40]
    pad_smd = [2, 1.78]
    smd_pinrow_distances=[25.24]
    package_width=24.89
    for p in smd_pins:
        for prd in smd_pinrow_distances:
            makeDIP(generator_name, p, rm, prd, package_width, overlen_top, overlen_bottom, ddrill, pad_smd, True,  0,0,0, [], [], "Package_DIP", [0, 0, 0], [1, 1, 1], [0, 0, 0], 'SMDIP', 'surface-mounted (SMD) DIP', 'SMD DIP DIL PDIP SMDIP', outdir=output_dir)
            num_fps_generated += 1
        
    # Special DIP
    #
    # http://www.experimentalistsanonymous.com/diy/Datasheets/MN3005.pdf
    #
    # common settings
    overlen_top=1.27
    overlen_bottom=1.27
    rm=2.54
    ddrill=0.8
    pad=[1.6,1.6]
    pad_large=[2.4,1.6]
    pad_smdsocket=[3.1,1.6]
    pad_smdsocket_small=[1.6,1.6]

    # narrow 7.62 DIPs
    pins=[8]
    sizes_for_pins=20
    pinrow_distance=7.62
    package_width=6.35
    socket_width=pinrow_distance+2.54
    makeDIP(generator_name,16, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad,       False, 0, 0, 0, prefix_name = '8', skip_pin = [3, 4, 5, 6, 11, 12, 13, 14], skip_count = True, right_cnt_start = 5, outdir=output_dir)
    socket_height = (sizes_for_pins / 2 - 1) * rm + 2.54
    makeDIP(generator_name,16, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad,       False, socket_width, socket_height,0, ["Socket"],            prefix_name = '8', skip_pin = [3, 4, 5, 6, 11, 12, 13, 14], skip_count = True, right_cnt_start = 5, outdir=output_dir)
    makeDIP(generator_name,16, rm, pinrow_distance, package_width, overlen_top, overlen_bottom, ddrill, pad_large, False, socket_width, socket_height,0, ["Socket"], ["LongPads"], prefix_name = '8', skip_pin = [3, 4, 5, 6, 11, 12, 13, 14], skip_count = True, right_cnt_start = 5, outdir=output_dir)
    num_fps_generated += 3

    return num_fps_generated