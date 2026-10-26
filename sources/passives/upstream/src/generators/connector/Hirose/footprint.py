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
    import generators.connector.Hirose.conn_ffc_hirose_fh12_smd_side as conn_ffc_hirose_fh12_smd_side
    num_fps_generated += conn_ffc_hirose_fh12_smd_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Hirose.conn_ffc_hirose_fh26 as conn_ffc_hirose_fh26
    num_fps_generated += conn_ffc_hirose_fh26.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Hirose.conn_hirose_df11_tht_top as conn_hirose_df11_tht_top
    num_fps_generated += conn_hirose_df11_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Hirose.conn_hirose_df12c_ds_smd_top as conn_hirose_df12c_ds_smd_top
    num_fps_generated += conn_hirose_df12c_ds_smd_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Hirose.conn_hirose_df12e_dp_smd_top as conn_hirose_df12e_dp_smd_top
    num_fps_generated += conn_hirose_df12e_dp_smd_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Hirose.conn_hirose_df13_tht_side as conn_hirose_df13_tht_side
    num_fps_generated += conn_hirose_df13_tht_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Hirose.conn_hirose_df13_tht_top as conn_hirose_df13_tht_top
    num_fps_generated += conn_hirose_df13_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Hirose.conn_hirose_df13c_smd_top as conn_hirose_df13c_smd_top
    num_fps_generated += conn_hirose_df13c_smd_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Hirose.conn_hirose_df63_tht_top as conn_hirose_df63_tht_top
    num_fps_generated += conn_hirose_df63_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    return num_fps_generated
