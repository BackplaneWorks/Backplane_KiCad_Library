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
    import generators.connector.Molex.conn_ffc_molex_200528 as conn_ffc_molex_200528
    num_fps_generated += conn_ffc_molex_200528.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_ffc_molex_502250 as conn_ffc_molex_502250
    num_fps_generated += conn_ffc_molex_502250.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_SPOX_tht_side as conn_molex_SPOX_tht_side
    num_fps_generated += conn_molex_SPOX_tht_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_SPOX_tht_top as conn_molex_SPOX_tht_top
    num_fps_generated += conn_molex_SPOX_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_kk_254_tht_top as conn_molex_kk_254_tht_top
    num_fps_generated += conn_molex_kk_254_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_kk_396_5273_tht_top as conn_molex_kk_396_5273_tht_top
    num_fps_generated += conn_molex_kk_396_5273_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_kk_396_tht_hor as conn_molex_kk_396_tht_hor
    num_fps_generated += conn_molex_kk_396_tht_hor.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_kk_396_tht_top as conn_molex_kk_396_tht_top
    num_fps_generated += conn_molex_kk_396_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_mega_fit_tht_side_dual_row as conn_molex_mega_fit_tht_side_dual_row
    num_fps_generated += conn_molex_mega_fit_tht_side_dual_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_mega_fit_tht_top_dual_row as conn_molex_mega_fit_tht_top_dual_row
    num_fps_generated += conn_molex_mega_fit_tht_top_dual_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_clasp_tht_side as conn_molex_micro_clasp_tht_side
    num_fps_generated += conn_molex_micro_clasp_tht_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_clasp_tht_top as conn_molex_micro_clasp_tht_top
    num_fps_generated += conn_molex_micro_clasp_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_fit_3_0_smd_side_dual_row as conn_molex_micro_fit_3_0_smd_side_dual_row
    num_fps_generated += conn_molex_micro_fit_3_0_smd_side_dual_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_fit_3_0_smd_side_single_row as conn_molex_micro_fit_3_0_smd_side_single_row
    num_fps_generated += conn_molex_micro_fit_3_0_smd_side_single_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_fit_3_0_smd_top_dual_row as conn_molex_micro_fit_3_0_smd_top_dual_row
    num_fps_generated += conn_molex_micro_fit_3_0_smd_top_dual_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_fit_3_0_smd_top_single_row as conn_molex_micro_fit_3_0_smd_top_single_row
    num_fps_generated += conn_molex_micro_fit_3_0_smd_top_single_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_fit_3_0_tht_side_dual_row as conn_molex_micro_fit_3_0_tht_side_dual_row
    num_fps_generated += conn_molex_micro_fit_3_0_tht_side_dual_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_fit_3_0_tht_side_single_row as conn_molex_micro_fit_3_0_tht_side_single_row
    num_fps_generated += conn_molex_micro_fit_3_0_tht_side_single_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_fit_3_0_tht_top_dual_row as conn_molex_micro_fit_3_0_tht_top_dual_row
    num_fps_generated += conn_molex_micro_fit_3_0_tht_top_dual_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_fit_3_0_tht_top_single_row as conn_molex_micro_fit_3_0_tht_top_single_row
    num_fps_generated += conn_molex_micro_fit_3_0_tht_top_single_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_latch_tht_side as conn_molex_micro_latch_tht_side
    num_fps_generated += conn_molex_micro_latch_tht_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_micro_latch_tht_top as conn_molex_micro_latch_tht_top
    num_fps_generated += conn_molex_micro_latch_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_mini_fit_Jr_tht_side_dual_row as conn_molex_mini_fit_Jr_tht_side_dual_row
    num_fps_generated += conn_molex_mini_fit_Jr_tht_side_dual_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_mini_fit_Jr_tht_top_dual_row as conn_molex_mini_fit_Jr_tht_top_dual_row
    num_fps_generated += conn_molex_mini_fit_Jr_tht_top_dual_row.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_mini_fit_sr_tht_side as conn_molex_mini_fit_sr_tht_side
    num_fps_generated += conn_molex_mini_fit_sr_tht_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_mini_fit_sr_tht_top as conn_molex_mini_fit_sr_tht_top
    num_fps_generated += conn_molex_mini_fit_sr_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_mini_fit_sr_tht_top_dual as conn_molex_mini_fit_sr_tht_top_dual
    num_fps_generated += conn_molex_mini_fit_sr_tht_top_dual.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_nano_fit_tht_side as conn_molex_nano_fit_tht_side
    num_fps_generated += conn_molex_nano_fit_tht_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_nano_fit_tht_top as conn_molex_nano_fit_tht_top
    num_fps_generated += conn_molex_nano_fit_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_picoblade_tht_side as conn_molex_picoblade_tht_side
    num_fps_generated += conn_molex_picoblade_tht_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_picoblade_tht_top as conn_molex_picoblade_tht_top
    num_fps_generated += conn_molex_picoblade_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_picoflex_smd_top as conn_molex_picoflex_smd_top
    num_fps_generated += conn_molex_picoflex_smd_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_picoflex_tht_top as conn_molex_picoflex_tht_top
    num_fps_generated += conn_molex_picoflex_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_sabre_tht_side as conn_molex_sabre_tht_side
    num_fps_generated += conn_molex_sabre_tht_side.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_sabre_tht_top as conn_molex_sabre_tht_top
    num_fps_generated += conn_molex_sabre_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_slimstack_501920 as conn_molex_slimstack_501920
    num_fps_generated += conn_molex_slimstack_501920.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_slimstack_502426 as conn_molex_slimstack_502426
    num_fps_generated += conn_molex_slimstack_502426.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_slimstack_502430 as conn_molex_slimstack_502430
    num_fps_generated += conn_molex_slimstack_502430.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_slimstack_52991 as conn_molex_slimstack_52991
    num_fps_generated += conn_molex_slimstack_52991.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_slimstack_53748 as conn_molex_slimstack_53748
    num_fps_generated += conn_molex_slimstack_53748.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_slimstack_54722 as conn_molex_slimstack_54722
    num_fps_generated += conn_molex_slimstack_54722.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_slimstack_55560 as conn_molex_slimstack_55560
    num_fps_generated += conn_molex_slimstack_55560.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    import generators.connector.Molex.conn_molex_stackable_linear_tht_top as conn_molex_stackable_linear_tht_top
    num_fps_generated += conn_molex_stackable_linear_tht_top.generate_all(generator_name, GLOBAL_CONFIG, CONNECTOR_CONFIG)

    return num_fps_generated
