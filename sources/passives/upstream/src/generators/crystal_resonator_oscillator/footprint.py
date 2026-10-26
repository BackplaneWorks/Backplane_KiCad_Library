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
import argparse

from kilibs.geom import CornerSelection, GeomRectangle
from kilibs.util.param_util import toVectorUseCopyIfNumber
from KicadModTree import *  # NOQA
from KicadModTree import Stadium, ChamferedRectangle, ReferencedPad
from generators.tools.footprint.drawing_tools import *
from generators.tools.footprint import drawing_tools as DT
from generators.tools.footprint import (
    drawing_tools_courtyard,
    footprint_text_fields,
)
from generators.tools.spec.base_spec import BaseSpec
from generators.tools.spec.spec_generator import get_file_name_ids_specs
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC
from kilibs.config.global_config import GLOBAL_CONFIG


slk_clearance = 0.2


def create_footprints(spec: BaseSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification (not used by this generator).
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    num_fps_generated = 0
    for _, ids_specs in get_file_name_ids_specs(generator_name):
        for id, spec_raw in ids_specs:
            generateFootprint(spec_raw, id, generator_name)
            num_fps_generated +=1
    return num_fps_generated


def generateFootprint(
    device_params: dict, pkg_id: str, generator_name: str
):
    _funcs = {
        "makeCrystal": makeCrystal,
        "makeCrystalAll": makeCrystalAll,
        "makeCrystalRoundVert": makeCrystalRoundVert,
        "makeCrystalHC49Vert": makeCrystalHC49Vert,
        "makeSMDCrystal": makeSMDCrystal,
    }
    func_name = device_params.pop("func")
    if func_name not in _funcs:
        raise ValueError(f"Unknown 'func': {func_name}")
    func = _funcs[func_name]

    # Run function
    func(generator_name, **device_params)

def makeSMDCrystalAndHand(
    footprint_name,
    addSizeFootprintName,
    pins,
    pad_sep_x,
    pad_sep_y,
    pad,
    pack_width,
    pack_height,
    pack_bevel,
    hasAdhesive=False,
    adhesivePos=[0, 0],
    adhesiveSize=1,
    style="rect",
    description="Crystal SMD SMT",
    tags=[],
    lib_name="Crystal",
    offset3d=[0, 0, 0],
    scale3d=[1, 1, 1],
    rotate3d=[0, 0, 0],
):
    makeSMDCrystal(
        footprint_name,
        addSizeFootprintName,
        pins,
        pad_sep_x,
        pad_sep_y,
        pad,
        pack_width,
        pack_height,
        pack_bevel,
        hasAdhesive,
        adhesivePos,
        adhesiveSize,
        style,
        description,
        tags,
        lib_name,
        offset3d,
        scale3d,
        rotate3d,
    )
    hsfactorx = 1.75
    hsfactory = 1
    if pins == 2 and pack_width > pad_sep_x + pad[0]:
        hsfactorx = 1
        hsfactory = 1.75
    elif (
        pins == 4
        and pack_width < pad_sep_x + pad[0]
        and pack_height < pad_sep_y + pad[1]
    ):
        hsfactorx = 1.5
        hsfactory = 1.5
    elif (
        pins == 4
        and pack_width > pad_sep_x + pad[0]
        and pack_height < pad_sep_y + pad[1]
    ):
        hsfactorx = 1.1
        hsfactory = 1.5
    elif (
        pins == 4
        and pack_width < pad_sep_x + pad[0]
        and pack_height > pad_sep_y + pad[1]
    ):
        hsfactorx = 1.5
        hsfactory = 1.1

    makeSMDCrystal(
        footprint_name,
        addSizeFootprintName,
        pins,
        pad_sep_x + pad[0] * (hsfactorx - 1),
        pad_sep_y + pad[1] * (hsfactory - 1),
        [pad[0] * hsfactorx, pad[1] * hsfactory],
        pack_width,
        pack_height,
        pack_bevel,
        hasAdhesive,
        adhesivePos,
        adhesiveSize,
        style,
        description + ", hand-soldering",
        tags + " hand-soldering",
        lib_name,
        offset3d,
        scale3d,
        rotate3d,
        name_addition="_HandSoldering",
    )

#
#          <----------pad_sep_x------------->
#        <----------pack_width-------------->
#  #=============#                   #=============#
#  |   4         |                   |         3   |
#  |     +----------------------------------+      |    ^            ^
#  |     |       |                   |      |      |    |            |
#  #=============#                   #=============#    |            |
#        |                                  |           |            |
#        |                                  |           pack_height  |
#        |                                  |           |            pad_sep_y
#        |                                  |           |            |
#  #=============#                   #=============#    |  ^         |
#  |     |       |                   |      |      |    |  |         |
#  |     +----------------------------------+      |    v  |         v
#  |   1         |                   |         2   |       pad[1]
#  #=============#                   #=============#       v
#                                    <---pad[0]---->
#
#
# pins=2,4
# style="rect"/"hc49"/"dip"

def makeSMDCrystal(
    generator_name,
    footprint_name,
    addSizeFootprintName,
    pins,
    pad_sep_x,
    pad_sep_y,
    pad,
    pack_width,
    pack_height,
    pack_bevel,
    hasAdhesive=False,
    adhesivePos=[0, 0],
    adhesiveSize=1,
    style="rect",
    description="Crystal SMD SMT",
    tags=[],
    lib_name="Crystal",
    offset3d=[0, 0, 0],
    scale3d=[1, 1, 1],
    rotate3d=[0, 0, 0],
    name_addition="",
    rotation_in_name=False,
    handsoldering: bool=False,
    datasheet: str=None,
    manufacturer: str=None,
    part_number: str=None,
    frequency: str=None,
):
    fpname = footprint_name
    if addSizeFootprintName:
        fpname += "-{2}Pin_{0:2.1f}x{1:2.1f}mm".format(
            pack_width, pack_height, pins
        )

    modelname = fpname

    # This generator currently only does "B". Some parts need to make
    # that clear as there were rotated in the library manually.
    if rotation_in_name:
        rot_suffix = GLOBAL_CONFIG.get_rotation_suffix(GC.IpcRotation.B)
        fpname += "_" + rot_suffix
        modelname += "_" + rot_suffix

    fpname = fpname + name_addition

    if handsoldering:
        fpname += "_" + GLOBAL_CONFIG.handsoldering_suffix

    overpad_height = pad_sep_y + pad[1]
    overpad_width = pad_sep_x + pad[0]
    if pins == 3:
        overpad_height = pad_sep_y * 2 + pad[1]
        overpad_width = pad_sep_x * 2 + pad[0]

    betweenpads_x_slk = pad_sep_x - pad[0] - 2 * slk_offset - 2 * slk_clearance
    betweenpads_y_slk = pad_sep_y - pad[1] - 2 * slk_offset - 2 * slk_clearance
    overpads_x_slk = pad_sep_x + pad[0] + 2 * slk_offset + 2 * slk_clearance
    overpads_y_slk = pad_sep_y + pad[1] + 2 * slk_offset + 2 * slk_clearance
    if pins == 3:
        overpads_x_slk = pad_sep_x * 2 + pad[0] + 2 * slk_offset + 2 * slk_clearance
        overpads_y_slk = pad_sep_y * 2 + pad[1] + 2 * slk_offset + 2 * slk_clearance
    elif pins == 6:
        overpads_x_slk = pad_sep_x * 2 + pad[0] + 2 * slk_offset + 2 * slk_clearance

    dip_size = 1

    mark_size = max(1.5 * pack_bevel, 1)
    upright_mark = False
    while pack_height < 2 * mark_size or pack_width < 2 * mark_size:
        mark_size = mark_size / 2

    if (
        pack_bevel > 0
        and math.fabs(mark_size / pack_bevel) > 0.7
        and math.fabs(mark_size / pack_bevel) < 1.3
    ):
        upright_mark = True

    h_fab = pack_height
    w_fab = pack_width
    l_fab = -w_fab / 2
    t_fab = -h_fab / 2

    h_slk = h_fab + 2 * slk_offset + 2 * slk_clearance
    w_slk = w_fab + 2 * slk_offset + 2 * slk_clearance
    l_slk = l_fab - slk_offset - slk_clearance
    t_slk = t_fab - slk_offset - slk_clearance
    dip_size_slk = dip_size

    mark_l_slk = -overpads_x_slk / 2
    if math.fabs(l_slk - mark_l_slk) < 2 * lw_slk:
        mark_l_slk = l_slk + 2 * lw_slk
    mark_b_slk = overpads_y_slk / 2
    if math.fabs(t_slk + h_slk - mark_b_slk) < 2 * lw_slk:
        mark_b_slk = overpads_y_slk / 2 + lw_slk * 2.5

    desc = []

    if manufacturer or part_number:
        man_desc = []
        if manufacturer:
            man_desc.append(manufacturer)
        if part_number:
            man_desc.append(part_number)
        desc.append(" ".join(man_desc))

    desc.append(description)

    if frequency:
        desc.append(frequency)

    desc.append("{0:2.1f}x{1:2.1f}mm package".format(pack_width, pack_height))
    desc.append("SMD")

    if handsoldering:
        desc.append("hand-soldering")

    if datasheet:
        desc.append(datasheet)

    # init kicad footprint
    kicad_mod = Footprint(fpname, FootprintType.SMD)
    kicad_mod.description = ", ".join(desc)
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = Vector2D(0, 0)
    kicad_modg = kicad_mod

    body_rect = GeomRectangle(center=offset, size=Vector2D(pack_width, pack_height))

    # create FAB-layer
    if style == "hc49":
        kicad_mod.append(
            Rectangle(
                start=body_rect.top_left,
                end=body_rect.bottom_right,
                layer="F.Fab",
                width=GLOBAL_CONFIG.fab_line_width,
            )
        )
        stadium_rect = body_rect.inflated(-body_rect.size.y * 0.1)
        kicad_mod.append(
            Stadium(
                shape=stadium_rect, layer="F.Fab", width=GLOBAL_CONFIG.fab_line_width
            )
        )
    elif style == "dip":
        DIPRectL(
            kicad_modg, [l_fab, t_fab], [w_fab, h_fab], "F.Fab", lw_fab, dip_size
        )
    elif style == "rect1bevel":
        kicad_modg += ChamferedRectangle(
            center=offset,
            size=Vector2D(w_fab, h_fab),
            layer="F.Fab",
            width=lw_fab,
            corners=CornerSelection({CornerSelection.BOTTOM_LEFT: 1}),
            chamfer=GLOBAL_CONFIG.fab_bevel,
        )
    else:
        kicad_modg += ChamferedRectangle(
            center=offset,
            size=Vector2D(w_fab, h_fab),
            layer="F.Fab",
            width=lw_fab,
            corners=CornerSelection({CornerSelection.BOTTOM_LEFT: 1}),
            chamfer=GLOBAL_CONFIG.fab_bevel,
        )

    # create SILKSCREEN-layer
    if pins == 2:
        if pack_height < pad[1]:
            kicad_modg.append(
                Line(
                    start=[-betweenpads_x_slk / 2, t_slk],
                    end=[betweenpads_x_slk / 2, t_slk],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            kicad_modg.append(
                Line(
                    start=[-betweenpads_x_slk / 2, t_slk + h_slk],
                    end=[betweenpads_x_slk / 2, t_slk + h_slk],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            # pin1 mark
            kicad_modg.append(
                Line(
                    start=[min(l_slk, -overpads_x_slk / 2), -pad[1] / 2],
                    end=[min(l_slk, -overpads_x_slk / 2), pad[1] / 2],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
        else:
            kicad_modg.append(
                PolygonLine(
                    shape=[
                        [l_slk + w_slk, t_slk],
                        [-overpads_x_slk / 2, t_slk],
                        [-overpads_x_slk / 2, t_slk + h_slk],
                        [l_slk + w_slk, t_slk + h_slk],
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
    elif pins == 3:
        if pack_height < overpad_height and pack_width > overpad_width:
            kicad_modg.append(
                PolygonLine(
                    shape=[
                        [overpads_x_slk / 2, t_slk],
                        [l_slk + w_slk, t_slk],
                        [l_slk + w_slk, t_slk + h_slk],
                        [overpads_x_slk / 2, t_slk + h_slk],
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            kicad_modg.append(
                Line(
                    start=[l_slk - 2 * lw_slk, t_slk],
                    end=[l_slk - 2 * lw_slk, t_slk + h_slk],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )

            kicad_modg.append(
                PolygonLine(
                    shape=[
                        [-overpads_x_slk / 2, mark_b_slk],
                        [-overpads_x_slk / 2, t_slk + h_slk],
                        [l_slk, t_slk + h_slk],
                        [l_slk, t_slk],
                        [-overpads_x_slk / 2, t_slk],
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )

        else:
            kicad_modg.append(
                PolygonLine(
                    shape=[
                        [-overpads_x_slk / 2, -overpads_y_slk / 2],
                        [-overpads_x_slk / 2, overpads_y_slk / 2],
                        [overpads_x_slk / 2, overpads_y_slk / 2],
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
    elif pins >= 4:
        if (betweenpads_y_slk < 5 * lw_slk or betweenpads_x_slk < 5 * lw_slk) and (
            pack_height < overpad_height and pack_width < overpad_width
        ):
            kicad_modg.append(
                PolygonLine(
                    shape=[
                        [-overpads_x_slk / 2, -overpads_y_slk / 2],
                        [-overpads_x_slk / 2, overpads_y_slk / 2],
                        [overpads_x_slk / 2, overpads_y_slk / 2],
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
        else:
            if pack_height < overpad_height and pack_width < overpad_width:

                kicad_modg.append(
                    PolygonLine(
                        shape=[
                            [mark_l_slk, betweenpads_y_slk / 2],
                            [l_slk, betweenpads_y_slk / 2],
                            [l_slk, -betweenpads_y_slk / 2],
                        ],
                        layer="F.SilkS",
                        width=lw_slk,
                    )
                )
                kicad_modg.append(
                    PolygonLine(
                        shape=[
                            [l_slk + w_slk, -betweenpads_y_slk / 2],
                            [l_slk + w_slk, betweenpads_y_slk / 2],
                        ],
                        layer="F.SilkS",
                        width=lw_slk,
                    )
                )
                if pins == 4:
                    kicad_modg.append(
                        PolygonLine(
                            shape=[
                                [-betweenpads_x_slk / 2, t_slk],
                                [betweenpads_x_slk / 2, t_slk],
                            ],
                            layer="F.SilkS",
                            width=lw_slk,
                        )
                    )
                    kicad_modg.append(
                        PolygonLine(
                            shape=[
                                [betweenpads_x_slk / 2, t_slk + h_slk],
                                [-betweenpads_x_slk / 2, t_slk + h_slk],
                                [-betweenpads_x_slk / 2, mark_b_slk],
                            ],
                            layer="F.SilkS",
                            width=lw_slk,
                        )
                    )
            elif pack_height < overpad_height and pack_width > overpad_width:
                kicad_modg.append(
                    PolygonLine(
                        shape=[
                            [overpads_x_slk / 2, t_slk],
                            [l_slk + w_slk, t_slk],
                            [l_slk + w_slk, t_slk + h_slk],
                            [overpads_x_slk / 2, t_slk + h_slk],
                        ],
                        layer="F.SilkS",
                        width=lw_slk,
                    )
                )
                if pins == 4:
                    kicad_modg.append(
                        PolygonLine(
                            shape=[
                                [-betweenpads_x_slk / 2, t_slk],
                                [betweenpads_x_slk / 2, t_slk],
                            ],
                            layer="F.SilkS",
                            width=lw_slk,
                        )
                    )
                if style == "dip":

                    # Not quite sure if this is the right way to do the marker
                    # but the old way was under the body so this is only better
                    kicad_modg.append(
                        Line(
                            start=Vector2D(
                                l_slk - 3 * GLOBAL_CONFIG.silk_line_width,
                                1,
                            ),
                            end=Vector2D(
                                l_slk - 3 * GLOBAL_CONFIG.silk_line_width,
                                -1,
                            ),
                            layer="F.SilkS",
                            width=GLOBAL_CONFIG.silk_line_width,
                        )
                    )

                    kicad_modg.append(
                        PolygonLine(
                            shape=[
                                [-overpads_x_slk / 2, mark_b_slk],
                                [-overpads_x_slk / 2, t_slk + h_slk],
                                [l_slk, t_slk + h_slk],
                                [l_slk, t_slk],
                                [-overpads_x_slk / 2, t_slk],
                            ],
                            layer="F.SilkS",
                            width=lw_slk,
                        )
                    )

                    kicad_modg.append(
                        Line(
                            start=[betweenpads_x_slk / 2, t_slk + h_slk],
                            end=[-betweenpads_x_slk / 2, t_slk + h_slk],
                            layer="F.SilkS",
                            width=lw_slk,
                        )
                    )
                else:
                    kicad_modg.append(
                        PolygonLine(
                            shape=[
                                [-overpads_x_slk / 2, mark_b_slk],
                                [-overpads_x_slk / 2, t_slk + h_slk],
                                [l_slk, t_slk + h_slk],
                                [l_slk, t_slk],
                                [-overpads_x_slk / 2, t_slk],
                            ],
                            layer="F.SilkS",
                            width=lw_slk,
                        )
                    )
                    if pins == 4:
                        kicad_modg.append(
                            PolygonLine(
                                shape=[
                                    [betweenpads_x_slk / 2, t_slk + h_slk],
                                    [-betweenpads_x_slk / 2, t_slk + h_slk],
                                    [-betweenpads_x_slk / 2, mark_b_slk],
                                ],
                                layer="F.SilkS",
                                width=lw_slk,
                            )
                        )

            elif pack_height > overpad_height and pack_width < overpad_width:
                kicad_modg.append(
                    PolygonLine(
                        shape=[
                            [l_slk, -overpads_y_slk / 2],
                            [l_slk, t_slk],
                            [l_slk + w_slk, t_slk],
                            [l_slk + w_slk, -overpads_y_slk / 2],
                        ],
                        layer="F.SilkS",
                        width=lw_slk,
                    )
                )
                kicad_modg.append(
                    PolygonLine(
                        shape=[
                            [mark_l_slk, overpads_y_slk / 2],
                            [l_slk, overpads_y_slk / 2],
                            [l_slk, t_slk + h_slk],
                            [l_slk + w_slk, t_slk + h_slk],
                            [l_slk + w_slk, overpads_y_slk / 2],
                        ],
                        layer="F.SilkS",
                        width=lw_slk,
                    )
                )
                if pins == 4:
                    kicad_modg.append(
                        PolygonLine(
                            shape=[
                                [mark_l_slk, betweenpads_y_slk / 2],
                                [l_slk, betweenpads_y_slk / 2],
                                [l_slk, -betweenpads_y_slk / 2],
                            ],
                            layer="F.SilkS",
                            width=lw_slk,
                        )
                    )
                    kicad_modg.append(
                        PolygonLine(
                            shape=[
                                [l_slk + w_slk, -betweenpads_y_slk / 2],
                                [l_slk + w_slk, betweenpads_y_slk / 2],
                            ],
                            layer="F.SilkS",
                            width=lw_slk,
                        )
                    )

    courtyard_offset_body = GLOBAL_CONFIG.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.CRYSTAL
    )
    courtyard_offset_pads = GLOBAL_CONFIG.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.DEFAULT
    )

    w_crt = max(
        overpad_width + 2 * courtyard_offset_pads,
        pack_width + 2 * courtyard_offset_body,
    )
    h_crt = max(
        overpad_height + 2 * courtyard_offset_pads,
        pack_height + 2 * courtyard_offset_body,
    )

    court_rect = GeomRectangle(center=offset, size=Vector2D(w_crt, h_crt)).round_to_grid(
        grid=GLOBAL_CONFIG.courtyard_grid, outwards=True
    )

    # create courtyard
    kicad_mod.append(
        Rectangle(
            start=court_rect.top_left,
            end=court_rect.bottom_right,
            layer="F.CrtYd",
            width=GLOBAL_CONFIG.courtyard_line_width,
        )
    )

    # Texts
    footprint_text_fields.addTextFields(
        kicad_mod=kicad_mod,
        configuration=GLOBAL_CONFIG,
        body_edges=body_rect,
        courtyard=court_rect,
        fp_name=fpname,
        text_y_inside_position="center",
    )

    # create pads
    pad_pts = []

    if pins == 2:
        pad_pts += [
            (-pad_sep_x / 2, 0),
            (pad_sep_x / 2, 0),
        ]
    elif pins == 3:
        pad_pts += [
            (-pad_sep_x, 0),
            (0, 0),
            (pad_sep_x, 0),
        ]
    elif pins == 4:
        pad_pts += [
            (-pad_sep_x / 2, pad_sep_y / 2),
            (pad_sep_x / 2, pad_sep_y / 2),
            (pad_sep_x / 2, -pad_sep_y / 2),
            (-pad_sep_x / 2, -pad_sep_y / 2),
        ]
    elif pins == 6:
        pad_pts += [
            (-pad_sep_x, pad_sep_y / 2),
            (0, pad_sep_y / 2),
            (pad_sep_x, pad_sep_y / 2),
            (pad_sep_x, -pad_sep_y / 2),
            (0, -pad_sep_y / 2),
            (-pad_sep_x, -pad_sep_y / 2),
        ]
    else:
        raise ValueError("Unsupported number of pins: {}".format(pins))

    for i, pos in enumerate(pad_pts):
        new_pad = Pad(
            number=i + 1,
            type=Pad.TYPE_SMT,
            shape=Pad.SHAPE_ROUNDRECT,
            at=Vector2D(pos[0], pos[1]),
            size=pad,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
        )
        kicad_mod.append(new_pad)

    if hasAdhesive:
        kicad_modg += Circle(
            center=adhesivePos,
            radius=adhesiveSize / 2,
            width=0.1,
            layer="F.Adhes",
            fill=True,
        )

    # add model
    kicad_modg.append(
        Model(
            filename=kicad_mod.get_standard_3d_model_path(lib_name, modelname),
            at=offset3d,
            scale=scale3d,
            rotate=rotate3d,
        )
    )

    # write file
    write_footprint(kicad_mod, lib_name, generator_name)

def makeCrystalAll(
    generator_name,
    footprint_name,
    rm,
    pad_size,
    ddrill,
    pack_width,
    pack_height,
    pack_offset,
    pack_rm,
    style="flat",
    package_pad=False,
    package_pad_add_holes=False,
    package_pad_offset=0,
    package_pad_size=[0, 0],
    package_pad_drill_size=[1.2, 1.2],
    package_pad_ddrill=0.8,
    description="Crystal THT",
    lib_name="Crystal",
    tags="",
    offset3d=[0, 0, 0],
    scale3d=[1, 1, 1],
    rotate3d=[0, 0, 0],
    name_addition="",
    pad_style="tht",
    height3d=4.65,
    iheight3d=4,
):
    makeCrystal(
        footprint_name,
        rm,
        pad_size,
        ddrill,
        pack_width,
        pack_height,
        pack_offset,
        pack_rm,
        style,
        False,
        False,
        package_pad_offset,
        package_pad_size,
        package_pad_drill_size,
        package_pad_ddrill,
        description,
        lib_name,
        tags,
        offset3d,
        scale3d,
        rotate3d,
        name_addition,
        pad_style,
        height3d,
        iheight3d,
    )
    if package_pad:
        makeCrystal(
            footprint_name,
            rm,
            pad_size,
            ddrill,
            pack_width,
            pack_height,
            pack_offset,
            pack_rm,
            style,
            True,
            False,
            package_pad_offset,
            package_pad_size,
            package_pad_drill_size,
            package_pad_ddrill,
            description,
            lib_name,
            tags,
            offset3d,
            scale3d,
            rotate3d,
            name_addition + "_1EP_style1",
            pad_style,
            height3d,
            iheight3d,
        )
    if package_pad_add_holes and package_pad:
        makeCrystal(
            footprint_name,
            rm,
            pad_size,
            ddrill,
            pack_width,
            pack_height,
            pack_offset,
            pack_rm,
            style,
            True,
            True,
            package_pad_offset,
            package_pad_size,
            package_pad_drill_size,
            package_pad_ddrill,
            description,
            lib_name,
            tags,
            offset3d,
            scale3d,
            rotate3d,
            name_addition + "_1EP_style2",
            pad_style,
            height3d,
            iheight3d,
        )

#                    +---------------------------------------------------------------+   ^
#   OOOOO            |                                                               |   |
#   OO1OO----^---    |                                                               |   |
#   OOOOO    |   ----+ ^                                                             |   |
#            |       | |                                                             |   |
#           rm       | pack_rm                                                       |   pack_height
#            |       | |                                                             |   |
#   OOOOO    |   ----+ v                                                             |   |
#   OO2OO ---v---    |                                                               |   |
#   OOOOO            |                                                               |   |
#                    +---------------------------------------------------------------+   v
#                    <-----------------pack_width------------------------------------>
#     <------------->pack_offset
#
#
# pins=2,3
# style="flat"/"hc49"
# pad_style=tht/smd for pin 1/2

def makeCrystal(
    generator_name,
    footprint_name,
    rm,
    pad_size,
    ddrill,
    pack_width,
    pack_height,
    pack_offset,
    pack_rm,
    style="flat",
    package_pad=False,
    package_pad_add_holes=False,
    package_pad_offset=0,
    package_pad_size=[0, 0],
    package_pad_drill_size=[1.2, 1.2],
    package_pad_ddrill=0.8,
    manufacturer=None,
    part_number=None,
    description="Crystal THT",
    lib_name="Crystal",
    tags="",
    offset3d=[0, 0, 0],
    scale3d=[1, 1, 1],
    rotate3d=[0, 0, 0],
    name_addition="",
    pad_style="tht",
    height3d=4.65,
    iheight3d=4,
    datasheet: str=None,
):
    fpname = footprint_name
    fpname = fpname + name_addition
    if type(pad_size) is list:
        pad = [pad_size[1], pad_size[0]]
    else:
        pad = [pad_size, pad_size]

    pad3pos = [rm / 2, package_pad_offset + package_pad_size[0] / 2]
    pad3dril_xoffset = package_pad_size[1] / 2 + package_pad_ddrill / 2

    h_fab = pack_width
    w_fab = pack_height
    l_fab = -(w_fab - rm) / 2
    t_fab = pack_offset

    h_slk = h_fab + 2 * slk_offset + 2 * slk_clearance
    w_slk = w_fab + 2 * slk_offset + 2 * slk_clearance
    l_slk = l_fab - slk_offset - slk_clearance
    t_slk = t_fab - slk_offset - slk_clearance

    bev = 0
    if style == "hc49":
        bev = min(0.35, max(2 * lw_slk, w_slk / 7))

    slk_u_line = False
    if package_pad:
        if package_pad_size[1] < pack_width / 2:
            h_slk = (
                math.fabs(
                    (pad3pos[1] - package_pad_size[0] / 2 - slk_offset) - t_slk
                )
                + 2 * slk_clearance
            )
            slk_u_line = True
        else:
            h_slk = (
                max(
                    t_slk + h_slk,
                    pad3pos[1]
                    + package_pad_size[0] / 2
                    + slk_offset
                    + slk_clearance,
                )
                - t_slk
            )
        l_slk = min(
            l_slk, rm / 2 - package_pad_size[1] / 2 - slk_offset - slk_clearance
        )
        w_slk = (
            max(
                l_slk + w_slk,
                rm / 2 + package_pad_size[1] / 2 + slk_offset + slk_clearance,
            )
            - l_slk
        )
        if package_pad_add_holes:
            l_crt = (
                pad3pos[0]
                - pad3dril_xoffset
                - package_pad_drill_size[0] / 2
                - crt_offset
            )

    extra_textoffset = 0
    if l_slk > -(pad[0] / 2 + slk_offset + lw_slk):
        extra_textoffset = pad[0] / 2 + slk_offset + lw_slk - 0.5

    t_crt = -pad[1] / 2 - crt_offset
    w_crt = (
        max(pack_height + 2 * bev + 4 * crt_offset, pad[0] + rm, w_slk)
        + 2 * crt_offset
    )
    h_crt = (
        max(
            t_slk + h_slk - t_crt,
            pad3pos[1] + package_pad_size[0] / 2 - t_crt - crt_offset,
            pack_width + pack_offset + pad[1] / 2,
        )
        + 2 * crt_offset
    )
    l_crt = rm / 2 - w_crt / 2

    if package_pad and package_pad_add_holes and (pad[1] < pack_width / 2):
        l_crt = min(
            l_crt,
            pad3pos[0]
            - pad3dril_xoffset
            - package_pad_drill_size[0] / 2
            - crt_offset,
        )
        w_crt = max(
            w_crt,
            pad3pos[0]
            + pad3dril_xoffset
            + package_pad_drill_size[0] / 2
            + crt_offset
            - l_crt,
        )

    footprint_type = FootprintType.SMD if pad_style == "smd" else FootprintType.THT

    desc = []

    if manufacturer or part_number:
        desc.append(" ".join([x for x in [manufacturer, part_number] if x]))

    desc.append(description)

    # Yes these are backwards
    desc.append(f"length {pack_width:.1f}mm")
    desc.append(f"width {pack_height:.1f}mm")

    desc.append("SMD" if pad_style == "smd" else "THT")

    if datasheet:
        desc.append(datasheet)

    # init kicad footprint
    kicad_mod = Footprint(fpname, footprint_type)
    kicad_mod.description = ", ".join(desc)
    kicad_mod.tags = tags

    offset = [0, 0]
    if pad_style == "smd":
        offset = [-rm / 2, -pad3pos[1] / 2]
        kicad_modg = Translation(offset[0], offset[1])
        kicad_mod.append(kicad_modg)
    else:
        kicad_modg = kicad_mod

    # set general values
    kicad_modg.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[l_slk - bev / 2 - txt_offset - extra_textoffset, t_crt + h_crt / 4],
            layer="F.SilkS",
            rotation=90,
        )
    )
    kicad_modg.append(
        Text(
            text="${REFERENCE}",
            at=[l_crt + w_crt / 2, t_crt + 3 * h_crt / 5],
            layer="F.Fab",
            rotation=90,
        )
    )
    kicad_modg.append(
        Property(
            name=Property.VALUE,
            text=fpname,
            at=[
                l_slk + w_slk + txt_offset + extra_textoffset + bev / 2,
                t_crt + h_crt / 4,
            ],
            layer="F.Fab",
            rotation=90,
        )
    )

    # create FAB-layer
    kicad_modg.append(
        Rectangle(
            start=[l_fab, t_fab],
            end=[l_fab + w_fab, t_fab + h_fab],
            layer="F.Fab",
            width=lw_fab,
        )
    )
    kicad_modg.append(
        PolygonLine(
            shape=[
                [l_fab + w_fab / 2 - pack_rm / 2, t_fab],
                [0, t_fab / 2],
                [0, 0],
            ],
            layer="F.Fab",
            width=lw_fab,
        )
    )
    kicad_modg.append(
        PolygonLine(
            shape=[
                [l_fab + w_fab / 2 + pack_rm / 2, t_fab],
                [rm, t_fab / 2],
                [rm, 0],
            ],
            layer="F.Fab",
            width=lw_fab,
        )
    )
    if package_pad and package_pad_add_holes:
        kicad_modg.append(
            Line(
                start=[pad3pos[0] - pad3dril_xoffset, pad3pos[1]],
                end=[pad3pos[0] + pad3dril_xoffset, pad3pos[1]],
                layer="F.Fab",
                width=lw_fab,
            )
        )
    if style == "hc49":
        kicad_modg.append(
            Rectangle(
                start=[l_fab - bev, t_fab],
                end=[l_fab + w_fab + bev, t_fab - lw_fab],
                layer="F.Fab",
                width=lw_fab,
            )
        )
    # create SILKSCREEN-layer
    if package_pad and package_pad_add_holes:
        kicad_modg.append(
            PolygonLine(
                shape=[
                    [
                        l_slk,
                        pad3pos[1]
                        - package_pad_drill_size[1] / 2
                        - slk_offset
                        - slk_clearance,
                    ],
                    [l_slk, t_slk],
                    [l_slk + w_slk, t_slk],
                    [
                        l_slk + w_slk,
                        pad3pos[1]
                        - package_pad_drill_size[1] / 2
                        - slk_offset
                        - slk_clearance,
                    ],
                ],
                layer="F.SilkS",
                width=lw_slk,
            )
        )
    else:
        if slk_u_line:
            kicad_modg.append(
                PolygonLine(
                    shape=[
                        [l_slk, t_slk + h_slk],
                        [l_slk, t_slk],
                        [l_slk + w_slk, t_slk],
                        [l_slk + w_slk, t_slk + h_slk],
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
        else:
            kicad_modg.append(
                Rectangle(
                    start=[l_slk, t_slk],
                    end=[l_slk + w_slk, t_slk + h_slk],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
    kicad_modg.append(
        PolygonLine(
            shape=[
                [l_slk + w_slk / 2 - pack_rm / 2, t_slk],
                [0, max(t_slk / 2, pad[1] / 2 + slk_offset)],
                [0, pad[1] / 2 + slk_offset],
            ],
            layer="F.SilkS",
            width=lw_slk,
        )
    )
    kicad_modg.append(
        PolygonLine(
            shape=[
                [l_slk + w_slk / 2 + pack_rm / 2, t_slk],
                [rm, max(t_slk / 2, pad[1] / 2 + slk_offset)],
                [rm, pad[1] / 2 + slk_offset],
            ],
            layer="F.SilkS",
            width=lw_slk,
        )
    )
    if style == "hc49":
        kicad_modg.append(
            Rectangle(
                start=[l_slk - bev, t_slk],
                end=[l_slk + w_slk + bev, t_slk - lw_slk],
                layer="F.SilkS",
                width=lw_slk,
            )
        )

    # create courtyard
    kicad_mod.append(
        Rectangle(
            start=[roundCrt(l_crt + offset[0]), roundCrt(t_crt + offset[1])],
            end=[
                roundCrt(l_crt + w_crt + offset[0]),
                roundCrt(t_crt + h_crt + offset[1]),
            ],
            layer="F.CrtYd",
            width=lw_crt,
        )
    )

    # create pads
    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_CIRCLE
    pad_layers = "*"
    if pad_style == "smd":
        kicad_modg.append(
            Pad(
                number=1,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_ROUNDRECT,
                at=[0, 0],
                size=pad,
                drill=0,
                layers=["F.Cu", "F.Mask", "F.Paste"],
                round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
            )
        )
        kicad_modg.append(
            Pad(
                number=2,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_ROUNDRECT,
                at=[rm, 0],
                size=pad,
                drill=0,
                layers=["F.Cu", "F.Mask", "F.Paste"],
                round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
            )
        )
    else:
        kicad_modg.append(
            Pad(
                number=1,
                type=pad_type,
                shape=pad_shape1,
                at=[0, 0],
                size=pad,
                drill=ddrill,
                layers=[pad_layers + ".Cu", pad_layers + ".Mask"],
                round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
            )
        )
        kicad_modg.append(
            Pad(
                number=2,
                type=pad_type,
                shape=pad_shape1,
                at=[rm, 0],
                size=pad,
                drill=ddrill,
                layers=[pad_layers + ".Cu", pad_layers + ".Mask"],
                round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
            )
        )

    if package_pad:
        kicad_modg.append(
            Pad(
                number=3,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_ROUNDRECT,
                at=pad3pos,
                size=[package_pad_size[1], package_pad_size[0]],
                drill=0,
                layers=["F.Cu", "F.Mask", "F.Paste"],
                round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
            )
        )
        if package_pad_add_holes:
            kicad_modg.append(
                Pad(
                    number=3,
                    type=Pad.TYPE_THT,
                    shape=Pad.SHAPE_RECT,
                    at=[pad3pos[0] - pad3dril_xoffset, pad3pos[1]],
                    size=package_pad_drill_size,
                    drill=package_pad_ddrill,
                    layers=[pad_layers + ".Cu", pad_layers + ".Mask"],
                    round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
                )
            )
            kicad_modg.append(
                Pad(
                    number=3,
                    type=Pad.TYPE_THT,
                    shape=Pad.SHAPE_RECT,
                    at=[pad3pos[0] + pad3dril_xoffset, pad3pos[1]],
                    size=package_pad_drill_size,
                    drill=package_pad_ddrill,
                    layers=[pad_layers + ".Cu", pad_layers + ".Mask"],
                    round_radius_handler=GLOBAL_CONFIG.roundrect_radius_handler,
                )
            )

    # add model
    kicad_modg.append(
        Model(
            filename=kicad_mod.get_standard_3d_model_path(lib_name, fpname),
            at=offset3d,
            scale=scale3d,
            rotate=rotate3d,
        )
    )

    # write file
    write_footprint(kicad_mod, lib_name, generator_name)

#      +----------------------------------------------------+       ^
#    /                                                       \      |
#   /       OOOOO                              OOOOO          \     |
#  |        OOOOO                              OOOOO          |     pack_height
#   \       OOOOO                              OOOOO         /      |
#    \                                                      /       |
#      +----------------------------------------------------+       v
#  <-------------------------pack_width----------------------->
#              <-------------rm------------------>
#
#
# pins=2,3

def makeCrystalHC49Vert(
    generator_name,
    footprint_name,
    pins,
    rm,
    pad_size,
    ddrill,
    pack_width,
    pack_height,
    innerpack_width,
    innerpack_height,
    description="Crystal THT",
    lib_name="Crystal",
    tags="",
    addSizeFootprintName=False,
    height3d: float = None,
    datasheet: str | None = None,
    manufacturer: str | None = None,
    part_number: str | None = None,
):
    fpname = footprint_name
    desc = []

    if manufacturer or part_number:
        desc.append(" ".join([x for x in [manufacturer, part_number] if x]))

    desc.append(description)

    if addSizeFootprintName:
        fpname += "-{2}Pin_W{0:2.1f}mm_H{1:2.1f}mm".format(
            pack_width, pack_height, pins
        )
        desc.append(f"length {pack_height:2.1f}mm")
        desc.append(f"width {pack_width:2.1f}mm")
        desc.append(f"{pins} pins")

    if datasheet:
        desc.append(datasheet)

    pad_size = toVectorUseCopyIfNumber(pad_size)

    centerpos = Vector2D(rm * (pins - 1) / 2, 0)
    pin1pos = Vector2D(0, 0)

    body_bounds = GeomRectangle(
        center=centerpos,
        size=Vector2D(pack_width, pack_height),
    )

    # init kicad footprint
    kicad_mod = Footprint(fpname, FootprintType.THT)
    kicad_mod.description = ", ".join(desc)
    kicad_mod.tags = tags

    kicad_modg = kicad_mod

    pad_array = PadArray(
        start=pin1pos,
        initial=1,
        pincount=pins,
        increment=1,
        x_spacing=rm,
        size=pad_size,
        drill=ddrill,
        type=Pad.TYPE_THT,
        shape=Pad.SHAPE_CIRCLE,
        tht_pad1_shape=Pad.SHAPE_CIRCLE,
        layers=Pad.LAYERS_THT,
    )
    kicad_modg += pad_array

    keepouts = DT.getKeepoutsForPads(
        list(pad_array.children), GLOBAL_CONFIG.silk_pad_offset
    )
    fab_stadium = Stadium(
        shape=body_bounds, layer="F.Fab", width=GLOBAL_CONFIG.fab_line_width
    )
    kicad_modg += fab_stadium
    # This would be easier with a KeepoutNode to append to that handles this,
    # Then we could just add a Stadium
    # But to get this to generate now, we just steal the primitives
    # and apply keepouts ourselves.

    silk_stadium = fab_stadium.inflated(GLOBAL_CONFIG.silk_fab_offset)
    silk_stadium.layer = "F.SilkS"
    silk_stadium.width = GLOBAL_CONFIG.silk_line_width

    kicad_modg += makeNodesWithKeepout(
        list(silk_stadium.get_shapes()),
        layer="F.SilkS",
        width=GLOBAL_CONFIG.silk_line_width,
        keepouts=keepouts,
    )

    body_courtyard_offset = GLOBAL_CONFIG.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.CRYSTAL
    )
    pad_courtyard_offset = GLOBAL_CONFIG.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.DEFAULT
    )

    cy_height = max(
        body_bounds.size.y + 2 * body_courtyard_offset,
        pad_size.y + 2 * pad_courtyard_offset,
    )
    cy_width = max(
        body_bounds.size.x + 2 * body_courtyard_offset,
        rm * (pins - 1) + pad_size.x + 2 * pad_courtyard_offset,
    )

    courtyard_rect = GeomRectangle(center=centerpos, size=Vector2D(cy_width, cy_height))

    kicad_mod += drawing_tools_courtyard.make_round_or_stadium_courtyard(
        GLOBAL_CONFIG, courtyard_rect
    )

    footprint_text_fields.addTextFields(
        kicad_modg,
        GLOBAL_CONFIG,
        body_edges=body_bounds,
        courtyard=courtyard_rect,
        fp_name=kicad_mod.name,
        text_y_inside_position="center",
        allow_rotation=True,
    )

    kicad_modg += Model(filename=kicad_mod.get_standard_3d_model_path(lib_name, fpname))

    write_footprint(kicad_mod, lib_name, generator_name)

#       +---------------------------------------+
#      /                                         \
#     /                                           \
#    /                                             \
#   /       OOOOO                    OOOOO          \
#  |        OOOOO                    OOOOO          |
#   \       OOOOO                    OOOOO         /
#    \                                            /
#     \                                          /
#      \                                        /
#       +--------------------------------------+
#  <-----------------pack_diameter------------------>
#              <-------------rm-------->
#
#
# pins=2,3

def makeCrystalRoundVert(
    generator_name: str,
    footprint_name: str,
    rm: float,
    pad_size: Vector2D | float,
    ddrill: float,
    pack_diameter: float,
    pack_length: float,
    description: str,
    lib_name:str,
    tags: str = "",
    datasheet: str | None = None,
    manufacturer: str | None = None,
    part_number: str | None = None,
):
    pad = toVectorUseCopyIfNumber(pad_size)

    center_pos = Vector2D(rm / 2, 0)
    pin1_pos = Vector2D(0, 0)

    desc = []

    if manufacturer or part_number:
        desc.append(" ".join([x for x in [manufacturer, part_number] if x]))

    desc.append(description)

    desc.append(f"length {pack_length}mm")
    desc.append(f"width {pack_diameter}mm")

    if datasheet is not None:
        desc.append(datasheet)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.description = ", ".join(desc)
    kicad_mod.tags = tags

    kicad_modg = kicad_mod

    silk_dia = pack_diameter + 2 * GLOBAL_CONFIG.silk_fab_offset

    kicad_mod.append(
        Circle(
            center=center_pos,
            radius=pack_diameter / 2,
            layer="F.Fab",
            width=GLOBAL_CONFIG.fab_line_width,
        )
    )

    pad1 = Pad(
            number=1,
            type=Pad.TYPE_THT,
            shape=Pad.SHAPE_CIRCLE,
            at=pin1_pos,
            size=pad,
            drill=ddrill,
            layers=Pad.LAYERS_THT,
        )
    pad2 = ReferencedPad(reference_pad=pad1, number=2,
        at=pin1_pos + Vector2D(rm, 0),
    )
    kicad_modg.extend([pad1, pad2])

    keepouts = DT.getKeepoutsForPads(
        [pad1, pad2],
        GLOBAL_CONFIG.silk_pad_offset,
    )

    DT.addCircleWithKeepout(
        kicad_modg,
        center_pos.x,
        center_pos.y,
        radius=silk_dia / 2,
        layer="F.SilkS",
        width=GLOBAL_CONFIG.silk_line_width,
        keepouts=keepouts,
    )

    courtyard_offset_body = GLOBAL_CONFIG.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.CRYSTAL
    )
    courtyard_offset_pad = GLOBAL_CONFIG.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.DEFAULT
    )

    # The total width of the courtyard
    cy_width_x = max(
        pack_diameter + 2 * courtyard_offset_body,
        rm + pad.x + 2 * courtyard_offset_pad
    )
    cy_height_y = pack_diameter + 2 * courtyard_offset_body

    courtyard_rect = GeomRectangle(
        center=center_pos, size=Vector2D(cy_width_x, cy_height_y)
    )

    kicad_mod += drawing_tools_courtyard.make_round_or_stadium_courtyard(
        GLOBAL_CONFIG, courtyard_rect
    )

    body_rect = GeomRectangle(center=center_pos, size=Vector2D(pack_diameter, pack_diameter))

    footprint_text_fields.addTextFields(
        kicad_modg,
        GLOBAL_CONFIG,
        body_edges=body_rect,
        courtyard=courtyard_rect,
        fp_name=kicad_mod.name,
        text_y_inside_position="center",
        allow_rotation=True,
    )

    kicad_modg.append(
        Model(
            filename=kicad_mod.get_standard_3d_model_path(lib_name,
                                                        footprint_name),
        )
    )

    write_footprint(kicad_mod, lib_name, generator_name)
