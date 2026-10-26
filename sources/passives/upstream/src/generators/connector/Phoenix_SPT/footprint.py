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

from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_spec_dicts
from kilibs.config.global_config import GLOBAL_CONFIG
from ..config import CONNECTOR_CONFIG


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    import generators.connector.Phoenix_SPT.phoenixcontact_terminal_block_spt_tht as con
    num_fps_generated = 0
    _, params = get_spec_dicts(generator_name)[0]
    # Create each part
    for series in params:
        for mpn in params[series]['parts']:
            con.generate_footprint(
                generator_name, GLOBAL_CONFIG, params[series], params[series]['parts'][mpn], mpn, CONNECTOR_CONFIG
            )
            num_fps_generated += 1
    return num_fps_generated
