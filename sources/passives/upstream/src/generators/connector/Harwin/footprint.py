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
from ..config import CONNECTOR_CONFIG


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    import generators.connector.Harwin.m20_89xx as m20_89xx
    num_fps_generated += m20_89xx.gen_family(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    
    import generators.connector.Harwin.conn_harwin_m20_781xx45_smd_top_dual_row as m20_781xx45
    num_fps_generated += m20_781xx45.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    
    import generators.connector.Harwin.conn_harwin_g125_ms1xx05m1p_smd_top_dual_row as g125_ms1xx05m1p
    num_fps_generated += g125_ms1xx05m1p.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    return num_fps_generated
