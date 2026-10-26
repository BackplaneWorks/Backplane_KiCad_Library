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
# (C) 2025 Philippe Hartmann (harty911)
# (C) The KiCad Librarian Team

"""
TerminalBlock Barrier generator
"""

import generators.tools.footprint.drawing_tools as DT
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from KicadModTree import Footprint, FootprintType, Pad, Rectangle, Translation
from kilibs.config.global_config import GLOBAL_CONFIG, GlobalConfig
from kilibs.geom import Direction, GeomRectangle, Vector2D

from ..footprint_scripts_terminal_blocks import make_silk_outline_with_pin1_arrow
from .spec import TerminalBlockBarrierProperties


def _generateFootprintVariant(
    cfg: TerminalBlockBarrierProperties, n_pin: int, generator_name: str
):
    #    """ Generate one footprints variant (by pin number)"""

    footprint_name = cfg.getFootprintName(n_pin)

    courtyard_offset = GLOBAL_CONFIG.get_courtyard_offset(
        GlobalConfig.CourtyardType.CONNECTOR
    )

    # Footprint Assembly Board outline
    cell_size = Vector2D(cfg.cell_size.x, cfg.cell_size.y)
    fab_rect = GeomRectangle(
        start=(
            -(cell_size.x / 2 + cfg.side_border),
            -(cell_size.y / 2 + cfg.back_border),
        ),
        size=(
            (n_pin - 1) * cfg.pitch + cell_size.x + cfg.side_border * 2,
            cell_size.y + cfg.back_border,
        ),
    )
    silk_rect = fab_rect.inflated(GLOBAL_CONFIG.silk_line_width)
    crt_rect = fab_rect.inflated(courtyard_offset).round_to_grid(
        grid=GLOBAL_CONFIG.courtyard_grid, outwards=True
    )

    # Meta
    description = (
        f"{cfg.lib_description}, {cfg.metadata.manufacturer} {cfg.metadata.part_number}, {n_pin} pins, pitch {cfg.pitch:.3g}mm, "
        f"size {fab_rect.size.x:.3g}x{fab_rect.size.y:.3g}mm, "
        f"drill diameter {cfg.drill_diameter:.3g}mm, pad size {max(cfg.pad_size):.3g}mm, "
        f"{cfg.metadata.datasheet}, "
        "https://gitlab.com/kicad/libraries/kicad-library-tools/-/tree/main/scripts/TerminalBlock_Barrier"
    )
    tags = ["THT"]

    # create the footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.description = description
    kicad_mod.tags = tags
    kicad_draw = Translation(0, cfg.back_border + cell_size.y / 2 - cfg.pad_to_back)
    kicad_mod.append(kicad_draw)

    addTextFields(
        kicad_mod=kicad_draw,
        configuration=GLOBAL_CONFIG,
        body_edges=fab_rect,
        courtyard=crt_rect,
        fp_name=footprint_name,
        text_y_inside_position=cfg.ref_y_position,
    )

    for n in range(1, n_pin + 1):
        pos = Vector2D((n - 1) * cfg.pitch, 0)
        kicad_mod.append(
            Pad(
                number=n,
                type=Pad.TYPE_THT,
                shape=Pad.SHAPE_ROUNDRECT if n == 1 else Pad.SHAPE_OVAL,
                at=pos,
                size=cfg.pad_size,
                drill=cfg.drill_diameter,
                layers=Pad.LAYERS_THT,
                round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
            )
        )

        # Cell
        kicad_draw.append(
            Rectangle(
                start=pos - cell_size / 2,
                end=pos + cell_size / 2,
                width=GLOBAL_CONFIG.fab_line_width,
                layer="F.Fab",
            )
        )

        # Screw
        screw_pos = pos - Vector2D(0, cfg.screw_offset)
        DT.addSlitScrew(
            kicad_draw,
            screw_pos,
            cfg.screw_diameter / 2,
            "F.Fab",
            GLOBAL_CONFIG.fab_line_width,
        )

        # Screw base
        base = Vector2D(cfg.screw_base_size.x, cfg.screw_base_size.y)
        kicad_draw.append(
            Rectangle(
                start=screw_pos - base / 2,
                end=screw_pos + base / 2,
                width=GLOBAL_CONFIG.fab_line_width,
                layer="F.Fab",
            )
        )

        # Screw base extensions
        ext = Vector2D(base.x / 2, base.y / 5)
        kicad_draw.append(
            Rectangle(
                start=screw_pos + Vector2D(-ext.x / 2, -base.y / 2 - ext.y),
                end=screw_pos + Vector2D(ext.x / 2, -base.y / 2),
                width=GLOBAL_CONFIG.fab_line_width,
                layer="F.Fab",
            )
        )
        kicad_draw.append(
            Rectangle(
                start=screw_pos + Vector2D(-ext.x / 2, +base.y / 2),
                end=screw_pos + Vector2D(ext.x / 2, +base.y / 2 + ext.y),
                width=GLOBAL_CONFIG.fab_line_width,
                layer="F.Fab",
            )
        )

    kicad_draw.append(
        Rectangle(shape=fab_rect, width=GLOBAL_CONFIG.fab_line_width, layer="F.Fab")
    )

    kicad_draw += make_silk_outline_with_pin1_arrow(
        silk_rect,
        0,
        GLOBAL_CONFIG.silk_line_width,
        keepouts=[],
        pin1_keepouts=[],
        arrow_direction=Direction.SOUTH,
    )

    # create courtyard
    kicad_draw.append(
        Rectangle(
            shape=crt_rect,
            layer="F.CrtYd",
            width=GLOBAL_CONFIG.courtyard_line_width,
        )
    )

    # 3D model definition
    kicad_mod.add_standard_3d_model_to_footprint(cfg.lib_name, footprint_name)

    write_footprint(kicad_mod, cfg.lib_name, generator_name)


def create_footprints(spec: TerminalBlockBarrierProperties, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification.
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    for n_pin in spec.n_pin_variants:
        _generateFootprintVariant(spec, n_pin, generator_name)
    return len(spec.n_pin_variants)
