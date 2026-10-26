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
    import generators.connector.JST.conn_jst_eh_tht_side as conn_jst_eh_tht_side
    num_fps_generated += conn_jst_eh_tht_side.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_eh_tht_top as conn_jst_eh_tht_top
    num_fps_generated += conn_jst_eh_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_J2100_tht_side as conn_jst_J2100_tht_side
    num_fps_generated += conn_jst_J2100_tht_side.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_J2100_tht_top as conn_jst_J2100_tht_top
    num_fps_generated += conn_jst_J2100_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_JWPF_tht_top as conn_jst_JWPF_tht_top
    num_fps_generated += conn_jst_JWPF_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_NV_tht_top as conn_jst_NV_tht_top
    num_fps_generated += conn_jst_NV_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_ph_tht_side as conn_jst_ph_tht_side
    num_fps_generated += conn_jst_ph_tht_side.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_ph_tht_top as conn_jst_ph_tht_top
    num_fps_generated += conn_jst_ph_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_PHD_horizontal as conn_jst_PHD_horizontal
    num_fps_generated += conn_jst_PHD_horizontal.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_PHD_vertical as conn_jst_PHD_vertical
    num_fps_generated += conn_jst_PHD_vertical.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_PUD_tht_side as conn_jst_PUD_tht_side
    num_fps_generated += conn_jst_PUD_tht_side.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_PUD_tht_top as conn_jst_PUD_tht_top
    num_fps_generated += conn_jst_PUD_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_VH_tht_side_stabilizer as conn_jst_VH_tht_side_stabilizer
    num_fps_generated += conn_jst_VH_tht_side_stabilizer.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_VH_tht_side as conn_jst_VH_tht_side
    num_fps_generated += conn_jst_VH_tht_side.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_VH_tht_top_shrouded as conn_jst_vh_tht_top_shrouded
    num_fps_generated += conn_jst_vh_tht_top_shrouded.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_vh_tht_top as conn_jst_vh_tht_top
    num_fps_generated += conn_jst_vh_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_xh_tht_side as conn_jst_xh_tht_side
    num_fps_generated += conn_jst_xh_tht_side.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_xh_tht_top as conn_jst_xh_tht_top
    num_fps_generated += conn_jst_xh_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_ze_tht_side as conn_jst_ze_tht_side
    num_fps_generated += conn_jst_ze_tht_side.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_ze_tht_top as conn_jst_ze_tht_top
    num_fps_generated += conn_jst_ze_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_zh_tht_top as conn_jst_zh_tht_top
    num_fps_generated += conn_jst_zh_tht_top.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_XA_horizontal as conn_jst_XA_horizontal
    num_fps_generated += conn_jst_XA_horizontal.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    import generators.connector.JST.conn_jst_XA_vertical as conn_jst_XA_vertical
    num_fps_generated += conn_jst_XA_vertical.generate_all(
        generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG
    )

    return num_fps_generated
