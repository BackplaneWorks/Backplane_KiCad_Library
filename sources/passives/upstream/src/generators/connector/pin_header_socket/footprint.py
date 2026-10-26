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

# check README.md in repository root for installing venv
# For development, from the root of the repository:
# - Enable the vitual env: .\venv\Scripts\Activate or on Windows Powershell: .\venv\Scripts\Activate.ps1
# - cd to ./src/generators
# - python ./generate.py -f ../../../footprints -g connector/pin_header_socket -j1 -v -t
# This generates the IDC/Pinheaders/Pinsockets, on only 1 thread, verbose output and only a strategic test subset.
# Notes: connector/pin_socket will be integrated automatically after re-merge. 
# - Optional: Disable virtual env: .\venv\Scripts\Deactivate or on Windows Powershell: & {. .\venv\Scripts\Activate.ps1; deactivate}

from .spec import FPconfiguration #, makePinHeadOrSocket
from .def_makeIdcHeader import makeIdcHeader
from .def_makePinHeadStraight import makePinHeadStraight
from .def_makePinHeadStraightSMD import makePinHeadStraightSMD
from .def_makePinHeadAngled import makePinHeadAngled
from .def_makeSocketStripAngled import makeSocketStripAngled
from generators.tools.cli_args import CLI_ARGS


def create_footprints(spec: FPconfiguration, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: the Pinheader/Pinsocket/IDC specification.

    Returns:
        The number of footprints generated.
    """
    genFunction = None
    if spec.class_name == "PinHeader" or spec.class_name == "PinSocket":
        if spec.orientation == "Vertical":
            if spec.mount_type == "THT":
                genFunction = makePinHeadStraight
            elif spec.mount_type == "SMD":
                genFunction = makePinHeadStraightSMD
        elif spec.orientation == "Horizontal" and  spec.mount_type == "THT":
            if spec.class_name == "PinHeader":
                genFunction = makePinHeadAngled
            elif spec.class_name == "PinSocket":
                genFunction = makeSocketStripAngled
    elif spec.class_name == "IDC-Header" and (
        spec.mount_type == "THT" or
        (spec.mount_type == "SMD" and spec.orientation == "Vertical")
    ):
        genFunction = makeIdcHeader
    if genFunction == None:
        raise ValueError(
            f"Unsupported mount/orientation combination: {spec.mount_type}/{spec.orientation}"
        )

    num_fps_generated = 0
    test_range = (pos for pos in [1,2,3,4,5,6,10,20,40] if pos in spec.pos_range)
    # print(*test_range)
    if spec.class_name == "IDC-Header":
        for pos_count in test_range if CLI_ARGS.headers else spec.pos_range:
            spec.pos_count = pos_count
            for latch_length in (spec.latch_length_range if spec.latch_length_range is not None else [spec.latch_length]):
                spec.latch_length = latch_length
                genFunction(spec, generator_name)
                num_fps_generated += 1

    elif genFunction:
        for pos_count in test_range if CLI_ARGS.headers else spec.pos_range:
            spec.pos_count = pos_count
            genFunction(spec, generator_name)
            num_fps_generated += 1

    return num_fps_generated
