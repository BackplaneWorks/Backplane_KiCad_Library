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

import math

from KicadModTree import (
    Footprint,
    FootprintType,
    PolygonLine,
    Property,
    Rectangle,
    Text,
)
from kilibs.config import global_config as GC
from kilibs.geom import Direction, Vector2D

from generators.tools.footprint.declarative_def_tools import (
    ast_evaluator,
    fp_additional_drawing,
)
from generators.tools.footprint.nodes import pin1_arrow
from generators.tools.footprint.save_footprint import write_footprint
from generators.tools.pad_factory import pad_info_to_pads

from .config import GridStagger
from .pad_factory import calculate_stagger, make_pad_factory
from .spec import GridArraySpec


def create_footprints(spec: GridArraySpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: the grid array specification.

    Returns:
        The number of footprints generated.
    """
    if not spec.has_fp_data:
        return 0

    _create_footprint_variant(spec, generator_name)
    return 1


def _create_footprint_variant(config: GridArraySpec, generator_name: str) -> None:
    # Pull out the old-style parameter dictionary
    spec = config.spec

    pad_factory = make_pad_factory(config)
    # Resolve the pads once: they are used for the silk clearance below and are
    # then appended to the footprint at the end.
    pads = list(pad_factory.pads())

    # Grid parts define a pitch symbol for evaluator expressions. Pin-table
    # parts have no pitch to inject.
    evaluator_params = {}
    if config.pitch is not None:
        evaluator_params["pitch"] = config.pitch

    fp_evaluator = ast_evaluator.ASTevaluator(symbols=evaluator_params)  # pyright: ignore

    pkg_x = config.body_size_x
    pkg_y = config.body_size_y
    f_fab_ref_rot = 0.0

    f = Footprint(config.name, FootprintType.SMD)
    if "mask_margin" in spec:
        f.setMaskMargin(spec["mask_margin"])
    if "paste_margin" in spec:
        f.setPasteMargin(spec["paste_margin"])
    if "paste_ratio" in spec:
        f.setPasteMarginRatio(spec["paste_ratio"])

    s1 = [1.0, 1.0]
    if pkg_x < 4.3 and pkg_y > pkg_x:
        s2 = [
            min(1.0, round(pkg_y / 4.3, 2))
        ] * 2  # Y size is greater, so rotate F.Fab reference
        f_fab_ref_rot = -90.0
    else:
        s2 = [min(1.0, round(pkg_x / 4.3, 2))] * 2

    t1 = 0.15 * s1[0]
    t2 = 0.15 * s2[0]

    chamfer = GC.GLOBAL_CONFIG.fab_bevel.get_chamfer_size(min(pkg_x, pkg_y))

    crtYdOffset = GC.GLOBAL_CONFIG.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.BGA
    )

    def crt_round(x: float) -> float:
        # Round away from zero for proper courtyard calculation
        neg = x < 0
        if neg:
            x = -x
        x = math.ceil(x * 100) / 100.0
        if neg:
            x = -x
        return x

    xCenter = 0.0
    xLeftFab = xCenter - pkg_x / 2.0
    xRightFab = xCenter + pkg_x / 2.0
    xChamferFab = xLeftFab + chamfer
    xLeftCrtYd = crt_round(xCenter - (pkg_x / 2.0 + crtYdOffset))
    xRightCrtYd = crt_round(xCenter + (pkg_x / 2.0 + crtYdOffset))

    yCenter = 0.0
    yTopFab = yCenter - pkg_y / 2.0
    yBottomFab = yCenter + pkg_y / 2.0
    yChamferFab = yTopFab + chamfer
    yTopCrtYd = crt_round(yCenter - (pkg_y / 2.0 + crtYdOffset))
    yBottomCrtYd = crt_round(yCenter + (pkg_y / 2.0 + crtYdOffset))
    yRef = yTopFab - 1.0
    yValue = yBottomFab + 1.0

    wFab = GC.GLOBAL_CONFIG.fab_line_width
    wCrtYd = GC.GLOBAL_CONFIG.courtyard_line_width
    wSilkS = GC.GLOBAL_CONFIG.silk_line_width

    # The silk offset must comply with the pad clearance. Rather than relying on
    # the default pad size at the nominal grid edge, compute the true outer pad
    # edges from the factory so that per-layout pad-size overrides and offsets
    # are honored.
    xPadLeftEdge = min(p.position.x - p.size.x / 2.0 for p in pads)
    xPadRightEdge = max(p.position.x + p.size.x / 2.0 for p in pads)
    yPadTopEdge = min(p.position.y - p.size.y / 2.0 for p in pads)
    yPadBottomEdge = max(p.position.y + p.size.y / 2.0 for p in pads)

    xSilkOffset = max(
        GC.GLOBAL_CONFIG.silk_fab_offset,
        xLeftFab + GC.GLOBAL_CONFIG.silk_pad_offset - xPadLeftEdge,
        xPadRightEdge + GC.GLOBAL_CONFIG.silk_pad_offset - xRightFab,
    )
    ySilkOffset = max(
        GC.GLOBAL_CONFIG.silk_fab_offset,
        yTopFab + GC.GLOBAL_CONFIG.silk_pad_offset - yPadTopEdge,
        yPadBottomEdge + GC.GLOBAL_CONFIG.silk_pad_offset - yBottomFab,
    )

    silkSizeX = pkg_x + 2 * (xSilkOffset - GC.GLOBAL_CONFIG.silk_fab_offset)
    silkSizeY = pkg_y + 2 * (ySilkOffset - GC.GLOBAL_CONFIG.silk_fab_offset)

    silkChamfer = GC.GLOBAL_CONFIG.fab_bevel.get_chamfer_size(
        min(silkSizeX, silkSizeY)
    )

    xLeftSilk = xLeftFab - xSilkOffset
    xRightSilk = xRightFab + xSilkOffset
    xChamferSilk = xLeftSilk + silkChamfer
    yTopSilk = yTopFab - ySilkOffset
    yBottomSilk = yBottomFab + ySilkOffset
    yChamferSilk = yTopSilk + silkChamfer

    # Text
    f.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[xCenter, yRef],
            layer="F.SilkS",
            size=s1,
            thickness=t1,
        )
    )
    f.append(
        Property(
            name=Property.VALUE,
            text=config.name,
            at=[xCenter, yValue],
            layer="F.Fab",
            size=s1,
            thickness=t1,
        )
    )
    f.append(
        Text(
            text="${REFERENCE}",
            at=[xCenter, yCenter],
            layer="F.Fab",
            size=s2,
            thickness=t2,
            rotation=f_fab_ref_rot,
        )
    )

    # Fab
    f.append(
        PolygonLine(
            shape=[
                [xRightFab, yBottomFab],
                [xLeftFab, yBottomFab],
                [xLeftFab, yChamferFab],
                [xChamferFab, yTopFab],
                [xRightFab, yTopFab],
                [xRightFab, yBottomFab],
            ],
            layer="F.Fab",
            width=wFab,
        )
    )

    # Courtyard
    f.append(
        Rectangle(
            start=[xLeftCrtYd, yTopCrtYd],
            end=[xRightCrtYd, yBottomCrtYd],
            layer="F.CrtYd",
            width=wCrtYd,
        )
    )

    # Silk

    arrow_apex = Vector2D(xLeftSilk, yTopSilk)
    min_arrow_size = wSilkS * 3
    arrow_size = max(min_arrow_size, crtYdOffset / 2)

    f.append(
        pin1_arrow.Pin1SilkScreenArrow45Deg(
            arrow_apex, Direction.SOUTHEAST, arrow_size, "F.SilkS", wSilkS
        )
    )

    f.append(
        PolygonLine(
            shape=[
                [xChamferSilk, yTopSilk],
                [xRightSilk, yTopSilk],
                [xRightSilk, yBottomSilk],
                [xLeftSilk, yBottomSilk],
                [xLeftSilk, yChamferSilk],
            ],
            layer="F.SilkS",
            width=wSilkS,
        )
    )

    # Append the pads
    for pad_info in pads:
        f.extend(pad_info_to_pads(pad_info))

    dwg_nodes = fp_additional_drawing.create_additional_drawings(  # pyright: ignore
        config.additional_drawings, GC.GLOBAL_CONFIG, fp_evaluator
    )
    f.extend(dwg_nodes)

    if config.pitch is not None:
        # Grid-based part: derive the pitch and layout for the description.
        pitchX, pitchY, staggered = calculate_stagger(config.layouts[0])
        if staggered is not GridStagger.NONE:
            pdesc = str(spec.get("pitch")) if "pitch" in spec else f"{pitchX}x{pitchY}"
            sdesc = f"{staggered.name}-staggered "
        else:
            pdesc = str(pitchX) if pitchX == pitchY else f"{pitchX}x{pitchY}"
            sdesc = ""
        layout_text = f"{sdesc}{config.layout_x}x{config.layout_y} Layout"
        pitch_text = f"{pdesc}mm Pitch"
    else:
        # Pin-table part that adds no documentary grid pitch or layout data.
        pdesc = ""
        layout_text = ""
        pitch_text = ""

    description_parts = [
        config.metadata.description if config.metadata.description else "",
        f"{pkg_x}x{pkg_y}mm",
        f"{config.num_balls} Ball",
    ]
    # The layout and pitch text only exist for grid-based parts.
    if layout_text:
        description_parts.append(layout_text)
    if pitch_text:
        description_parts.append(pitch_text)

    if config.metadata.datasheet:
        description_parts.append(config.metadata.datasheet)

    f.description = ", ".join(description_parts)

    f.tags = [config.package_type, str(config.num_balls)]
    if pdesc:
        f.tags.append(pdesc)
    f.tags += config.metadata.compatible_mpns
    f.tags += config.metadata.additional_tags

    # #################### Output and 3d model ############################
    f.add_standard_3d_model_to_footprint(config.lib_name, config.name)
    write_footprint(f, config.lib_name, generator_name)
