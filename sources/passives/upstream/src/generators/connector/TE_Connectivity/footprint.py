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
    
    import generators.connector.TE_Connectivity.conn_ffc_te_84982 as con1
    num_fps_generated += con1.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    
    import generators.connector.TE_Connectivity.conn_fpc_te_1734839 as con2
    num_fps_generated += con2.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    
    import generators.connector.TE_Connectivity.conn_te_826576 as con3
    num_fps_generated += con3.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    
    import generators.connector.TE_Connectivity.conn_te_mate_n_lock_tht_side as con4
    num_fps_generated += con4.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    
    import generators.connector.TE_Connectivity.conn_te_mate_n_lock_tht_top as con5
    num_fps_generated += con5.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)
    
    import generators.connector.TE_Connectivity.conn_te_micro_match_215079 as con6
    num_fps_generated += con6.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.TE_Connectivity.conn_te_micro_match_188275 as con7
    num_fps_generated += con7.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.TE_Connectivity.conn_ffc_te_84952_84953 as con8
    num_fps_generated += con8.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    return num_fps_generated

