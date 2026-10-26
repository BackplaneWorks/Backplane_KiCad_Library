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

from KicadModTree import Footprint, FootprintType, Line
from kilibs.geom import Direction, Vector2D
from kilibs.config.global_config import GLOBAL_CONFIG
from generators.tools.footprint.drawing_tools_silk import SilkArrowSize
from generators.tools.footprint.nodes.layouts.n_pad_box_layout import (
    make_layout_for_smd_two_pad_dimensions,
)
from generators.tools.footprint.nodes.layouts.footprint_layout import SilkStyle
from generators.tools.footprint.save_footprint import write_footprint

from .spec import (
    SmdInductorSpec,
    TwoPadInductorParameters,
)


def create_footprints(spec: SmdInductorSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification.
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    part_dimension = spec.body.get_body_size()

    footprint_name = f"L_{spec.manufacturer}_{spec.part_number}"

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)

    desc = [f"Inductor", spec.manufacturer, spec.part_number]

    if spec.series_description:
        desc.append(f"{spec.series_description} series")

    if spec.additional_description:
        desc.append(spec.additional_description)

    desc += [
        f"{part_dimension.x}x{part_dimension.y}x{part_dimension.z}mm",
        f"({spec.datasheet})",
    ]

    kicad_mod.description = ", ".join(desc)
    kicad_mod.tags = spec.tags

    xy_body_size = Vector2D.from_floats(part_dimension.x, part_dimension.y)

    # For now, all supported inductors are two-pad SMD inductors,
    # but this is where we would dispatch to different layouts
    if isinstance(spec.body, TwoPadInductorParameters):
        if xy_body_size.min_val < 2:
            silk_arrow_size = SilkArrowSize.SMALL
        else:
            silk_arrow_size = SilkArrowSize.MEDIUM

        layout = make_layout_for_smd_two_pad_dimensions(
            global_config=GLOBAL_CONFIG,
            pad_dims=spec.body.landing_dims,
            body_size=xy_body_size,
            silk_style=SilkStyle.RECTANGLE_KEEP_TOP_BOTTOM,
            is_polarized=spec.has_orientation,
            footprint_name=kicad_mod.name,
            silk_arrow_direction_if_inside=Direction.SOUTH,
            silk_arrow_size=silk_arrow_size,
        )

        # We never want the arrow to point in from the left even if the pad
        # is entirely inside the body.
        layout.silk_arrow_direction_if_inside = Direction.SOUTH

        kicad_mod += layout

        # And add an extra fab orientation line if the inductor is polarized
        if spec.has_orientation:
            # This will always produce a gap between the line and the body chamfer
            line_y = part_dimension.y * GLOBAL_CONFIG.fab_bevel_size_relative

            # 10% of the way into the device, but don't let it get too close to the edge
            line_x = min(
                part_dimension.x * 0.4,
                part_dimension.x / 2 - GLOBAL_CONFIG.fab_line_width * 2,
            )

            kicad_mod += Line(
                start=Vector2D.from_floats(-line_x, line_y),
                end=Vector2D.from_floats(-line_x, -line_y),
                width=GLOBAL_CONFIG.fab_line_width,
                layer="F.Fab",
            )
    else:
        raise RuntimeError(
            f"Unsupported inductor body type {type(spec.body)} for {footprint_name}."
        )

    # No variants, so we can just use the footprint name
    kicad_mod.add_standard_3d_model_to_footprint(
        spec.library_name, kicad_mod.name
    )

    write_footprint(kicad_mod, spec.library_name, generator_name)
    return 1
