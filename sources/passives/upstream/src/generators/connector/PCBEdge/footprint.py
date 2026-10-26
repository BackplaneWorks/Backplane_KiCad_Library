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
from kilibs.config.global_config import GLOBAL_CONFIG


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    import generators.connector.PCBEdge.molex_EDGELOCK as molex_EDGELOCK
    num_fps_generated += molex_EDGELOCK.generate_all(generator_name, GLOBAL_CONFIG)

    import generators.connector.PCBEdge.m2_card as m2_card
    num_fps_generated += m2_card.generate_all(generator_name)

    import generators.connector.PCBEdge.dec_card as dec_card
    num_fps_generated += dec_card.generate_all(generator_name)

    return num_fps_generated