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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

from KicadModTree import *  # NOQA

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_file_names


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    from .DPAK import TO252, TO263, TO268, ATPAK, Texas_NDW

    config_files = get_spec_file_names(generator_name)
    num_fps_generated = 0
    for config_file in config_files:
        build_list = [
            TO252(config_file),
            TO263(config_file),
            TO268(config_file),
            ATPAK(config_file),
            Texas_NDW(config_file),
        ]
        for package in build_list:
            num_fps_generated += package.build_series(generator_name, verbose=False)
    return num_fps_generated
