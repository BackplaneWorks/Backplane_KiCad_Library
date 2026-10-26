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
from generators.tools.footprint.footprint_scripts_resistorlike import *

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_file_name_ids_specs


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    for _, ids_specs in get_file_name_ids_specs(generator_name):
        for id, spec_dict in ids_specs:
            if id == 'base':
                # Ignore base from which the entries derive
                continue
            
            # Extract function to run (such as 'makeResistorRadial')
            if not spec_dict.get("func"):
                raise ValueError(f"No func specified for {id}: {spec_dict}")
            func = globals().get(spec_dict["func"])
            if not func:
                raise ValueError(f"Function {spec_dict['func']} not found for {id}: {spec_dict}")
            # Remove invalid parameters
            params = spec_dict.copy()
            params.update({"generator_name": generator_name})
            del params["func"]
            # Generate !
            func(**params)
            num_fps_generated += 1
    return num_fps_generated