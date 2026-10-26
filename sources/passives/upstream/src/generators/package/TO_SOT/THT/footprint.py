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
    Arc,
    Circle,
    Footprint,
    Line,
    Node,
    Pad,
    Property,
    Rectangle,
    Text,
    Translation,
)
from KicadModTree.util.courtyard_builder import CourtyardBuilder
from kilibs.geom import GeomRectangle
from kilibs.geom.operations import round_to_grid_e
from generators.tools.footprint.drawing_tools import (
    addCircleLF,
    addHDLineWithKeepout,
    addHLineWithKeepout,
    addKeepoutRect,
    addKeepoutRound,
    addRectAngledBottom,
    addRectAngledBottomNoTop,
    addRectAngledTop,
    addRectAngledTopNoBottom,
    addVDLineWithKeepout,
    addVLineWithKeepout,
    makeRectWithKeepout,
)

from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config
from kilibs.config.global_config import GLOBAL_CONFIG
from .spec import RoundToSpec, RectangularToSpec, CommonToSpec
from ...config import PACKAGE_CONFIG

def save_footprint(fp: Footprint, generator_name: str):
    fp.add_standard_3d_model_to_footprint("Package_TO_SOT_THT", fp.name)
    write_footprint(fp, "Package_TO_SOT_THT", generator_name)


def create_footprints(spec: CommonToSpec, generator_name: str) -> int:
    """Create the footprint(s) corresponding to the spec.

    Args:
        spec: The specification.
        generator_name: The name of this generator.

    Returns:
        The number of footprints generated.
    """
    id = spec.id
    footprint_type = spec.spec.get("generate_footprint_type", [])
    num_fps_generated = 0

    if isinstance(footprint_type, str):
        footprint_type = footprint_type.replace(" ", "")
        footprint_type = footprint_type.split(",")

    if isinstance(spec, RectangularToSpec):
        if "vertical" in footprint_type:
            generate_rect_to_fp_vertical(spec, id, 0, generator_name)
            num_fps_generated += 1
        if "horizontal" in footprint_type:
            generate_rect_to_fp_horizontal_tab_down(spec, id, 0, generator_name)
            num_fps_generated += 1
            if not spec.additional_pin_pad_size:
                generate_rect_to_fp_horizontal_tab_up(spec, id, generator_name)
                num_fps_generated += 1
        if "vertical-odd" in footprint_type:
            generate_rect_to_fp_vertical(spec, id, 1, generator_name)
            num_fps_generated += 1
        if "vertical-even" in footprint_type:
            generate_rect_to_fp_vertical(spec, id, 2, generator_name)
            num_fps_generated += 1
        if "horizontal-odd" in footprint_type:
            generate_rect_to_fp_horizontal_tab_down(spec, id, 1, generator_name)
            num_fps_generated += 1
        if "horizontal-even" in footprint_type:
            generate_rect_to_fp_horizontal_tab_down(spec, id, 2, generator_name)
            num_fps_generated += 1
    elif isinstance(spec, RoundToSpec):
        for type in footprint_type:
            generate_round_to_fp(spec, id, type, generator_name)
            num_fps_generated += 1
    return num_fps_generated

def generate_rect_to_fp_vertical(
    pkg: RectangularToSpec, id: str, staggered_type: int, generator_name: str
):
    fp = pkg.init_footprint("Vertical", "", staggered_type, PACKAGE_CONFIG, generator_name)
    c = GLOBAL_CONFIG
    courtyard_offset = GLOBAL_CONFIG.get_courtyard_offset(
        global_config.GlobalConfig.CourtyardType.DEFAULT
    )

    width_fab_plastic = pkg.plastic_dimensions[0]
    height_fab_plastic = pkg.plastic_dimensions[2]
    left_fab_plastic = -pkg.pin_offset_x
    right_fab_plastic = left_fab_plastic + width_fab_plastic
    top_fab_plastic = -pkg.pin_offset_z
    bottom_fab_plastic = top_fab_plastic + height_fab_plastic

    height_fab_metal = pkg.metal_dimensions[2]
    bottom_fab_metal = top_fab_plastic + height_fab_metal

    bottom_silk_plastic = bottom_fab_plastic + c.silk_fab_offset
    x_mount_hole = left_fab_plastic + pkg.mounting_hole_position[0]

    # calculate y-translation of pin 1
    yshift = 0
    y1 = 0
    y2 = 0
    if staggered_type:
        if staggered_type == 1:
            y1 = pkg.staggered_pitch[0]
            yshift = -pkg.staggered_pitch[0]
        else:
            y2 = pkg.staggered_pitch[0]

    fpt = Translation(0, yshift)
    fp.append(fpt)

    ###  PADS  ############################################################

    pads = []
    y = y1
    x = 0
    for p in range(pkg.pins):
        y = y2 if p % 2 else y1
        pads.append((x, y))
        if pkg.pitch_list and p < len(pkg.pitch_list):
            x += pkg.pitch_list[p]
        else:
            x += pkg.pitch

    for p in range(len(pads)):
        if p == 0:
            pad_shape = Pad.SHAPE_RECT
        else:
            pad_shape = Pad.SHAPE_OVAL
        fpt.append(
            Pad(
                number=p + 1,
                type=Pad.TYPE_THT,
                shape=pad_shape,
                at=pads[p],
                size=pkg.pad_dimensions,
                drill=pkg.drill,
                layers=Pad.LAYERS_THT,
            )
        )

    ###  FAB LAYER   ######################################################

    outline = GeomRectangle(
        start=[left_fab_plastic, top_fab_plastic],
        end=[right_fab_plastic, bottom_fab_plastic],
    )
    fab_outline = Rectangle(
        shape=outline,
        layer="F.Fab",
        width=c.fab_line_width,
    )
    fpt.append(fab_outline)

    for pad in pads:
        yl1 = bottom_fab_plastic
        yl2 = pad[1]
        if yl2 > yl1:
            fpt.append(
                Rectangle(
                    start=[pad[0] - pkg.pin_width_height[0] / 2, yl1],
                    end=[pad[0] + pkg.pin_width_height[0] / 2, yl2],
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )

    if pkg.metal_dimensions[2] > 0:
        metal_h_line = Line(
            start=[left_fab_plastic, bottom_fab_metal],
            end=[right_fab_plastic, bottom_fab_metal],
            layer="F.Fab",
            width=c.fab_line_width,
        )
        fpt.append(metal_h_line)
        y_hole_bottom = bottom_fab_metal
        y_hole_bottom_slk = bottom_fab_metal
    else:
        y_hole_bottom = bottom_fab_plastic
        y_hole_bottom_slk = bottom_fab_metal + c.silk_fab_offset
    if pkg.mounting_hole_diameter > 0:
        x_hole_left = x_mount_hole - pkg.mounting_hole_diameter / 2
        x_hole_right = x_mount_hole + pkg.mounting_hole_diameter / 2
        hole_v_line_left = Line(
            start=[x_hole_left, top_fab_plastic],
            end=[x_hole_left, y_hole_bottom],
            layer="F.Fab",
            width=c.fab_line_width,
        )
        hole_v_line_right = Line(
            start=[x_hole_right, top_fab_plastic],
            end=[x_hole_right, y_hole_bottom],
            layer="F.Fab",
            width=c.fab_line_width,
        )
        fpt.append(hole_v_line_left)
        fpt.append(hole_v_line_right)

    ###  COURTYYRD  #######################################################

    cb = CourtyardBuilder.from_node(
        node=fpt, global_config=GLOBAL_CONFIG, offset_fab=courtyard_offset
    )
    fpt += cb.node

    ###  SILKSCREEN LAYER  ################################################

    keepouts = []
    for p in range(len(pads)):
        if p == 0:
            addKeepout = addKeepoutRect
        else:
            addKeepout = addKeepoutRound
        keepouts += addKeepout(
            pads[p][0],
            pads[p][1],
            pkg.pad_dimensions[0] + 2 * c.silk_pad_clearance + c.silk_line_width,
            pkg.pad_dimensions[1] + 2 * c.silk_pad_clearance + c.silk_line_width,
        )

    silk_rect = outline.inflated(GLOBAL_CONFIG.silk_fab_offset)
    silk_nodes = makeRectWithKeepout(
        rect=silk_rect,
        layer="F.SilkS",
        keepouts=keepouts,
        width=GLOBAL_CONFIG.silk_line_width,
    )
    fpt += silk_nodes

    if pkg.metal_dimensions[2] > 0:
        addHLineWithKeepout(
            fpt,
            x0=left_fab_plastic - c.silk_fab_offset,
            x1=right_fab_plastic + c.silk_fab_offset,
            y=bottom_fab_metal,
            layer="F.SilkS",
            width=c.silk_line_width,
            keepouts=keepouts
        )

    if pkg.mounting_hole_diameter > 0:
        addVLineWithKeepout(
            fpt,
            x=x_hole_left,
            y0=top_fab_plastic - c.silk_fab_offset,
            y1=y_hole_bottom_slk,
            layer="F.SilkS",
            width=c.silk_line_width,
            keepouts=keepouts
        )
        addVLineWithKeepout(
            fpt,
            x=x_hole_right,
            y0=top_fab_plastic - c.silk_fab_offset,
            y1=y_hole_bottom_slk,
            layer="F.SilkS",
            width=c.silk_line_width,
            keepouts=keepouts
        )

    for p in range(len(pads)):
        yl1 = bottom_silk_plastic
        yl2 = pads[p][1]
        if yl2 > yl1:
            addVLineWithKeepout(
                fpt,
                pads[p][0] - pkg.pin_width_height[0] / 2 - c.silk_fab_offset,
                yl1,
                yl2,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )
            addVLineWithKeepout(
                fpt,
                pads[p][0] + pkg.pin_width_height[0] / 2 + c.silk_fab_offset,
                yl1,
                yl2,
                "F.SilkS",
                c.silk_line_width,
                keepouts,
            )

    ### TEXT FIELDS  ######################################################

    addTextFields(
        fpt,
        configuration=GLOBAL_CONFIG,
        body_edges=outline,
        courtyard=cb.bbox,
        fp_name=fp.name,
        text_y_inside_position="center",
        allow_rotation=True,
    )

    save_footprint(fp, generator_name)

def generate_rect_to_fp_horizontal_tab_down(
    pkg: RectangularToSpec, id: str, staggered_type: int, generator_name: str
):
    fp = pkg.init_footprint(
        "Horizontal", "TabDown", staggered_type, PACKAGE_CONFIG, generator_name
    )
    c = GLOBAL_CONFIG
    courtyard_offset = GLOBAL_CONFIG.get_courtyard_offset(
        global_config.GlobalConfig.CourtyardType.DEFAULT
    )

    width_fab_plastic = pkg.plastic_dimensions[0]
    height_fab_plastic = pkg.plastic_dimensions[1]
    bottom_fab_plastic = -pkg.pin_min_length_before_90deg_bend
    top_fab_plastic = bottom_fab_plastic - height_fab_plastic
    left_fab_plastic = -pkg.pin_offset_x
    right_fab_plastic = left_fab_plastic + width_fab_plastic

    width_fab_metal = pkg.metal_dimensions[0]
    height_fab_metal = pkg.metal_dimensions[1]
    top_fab_metal = bottom_fab_plastic - height_fab_metal
    left_fab_metal = left_fab_plastic + pkg.metal_offset_x
    right_fab_metal = left_fab_metal + width_fab_metal

    width_silk_plastic = width_fab_plastic + 2 * c.silk_fab_offset
    height_silk_plastic = height_fab_plastic + 2 * c.silk_fab_offset
    left_silk_plastic = left_fab_plastic - c.silk_fab_offset
    right_silk_plastic = left_silk_plastic + width_silk_plastic
    bottom_silk_plastic = bottom_fab_plastic + c.silk_fab_offset
    top_silk_plastic = bottom_silk_plastic - height_silk_plastic

    height_silk_metal = height_fab_metal + 2 * c.silk_fab_offset
    top_silk_metal = bottom_silk_plastic - height_silk_metal
    x_mount_hole = left_fab_plastic + pkg.mounting_hole_position[0]
    y_mount_hole = bottom_fab_plastic - pkg.mounting_hole_position[1]

    # calculate y-translation of pin 1
    yshift = 0
    y1 = 0
    y2 = 0
    if staggered_type == 1:
        y1 = pkg.staggered_pitch[1]
        yshift = -pkg.staggered_pitch[1]
        y2 = 0
    elif staggered_type == 2:
        y1 = 0
        yshift = 0
        y2 = pkg.staggered_pitch[1]

    fpt = Translation(0, yshift)
    fp.append(fpt)

    ###  PADS  ############################################################

    pads = []
    y = y1
    x = 0
    for p in range(1, pkg.pins + 1):
        if (p % 2) == 1:
            y = y1
        else:
            y = y2
        pads.append([x, y])
        if len(pkg.pitch_list) > 0 and p <= len(pkg.pitch_list):
            x += pkg.pitch_list[p - 1]
        else:
            x += pkg.pitch

    # create additional pad
    if len(pkg.additional_pin_pad_size) > 0:
        additional_pin_pad_position_x = round(pkg.plastic_dimensions[0] / 2, 3)
        additional_pin_pad_position_y = round(
            pkg.metal_dimensions[1] - pkg.additional_pin_pad_size[1] / 3, 3
        )
        additional_pad_x = left_fab_plastic + additional_pin_pad_position_x
        additional_pad_y = bottom_fab_plastic - additional_pin_pad_position_y
        fpt.append(
            Pad(
                number=pkg.pins + 1,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_RECT,
                at=[additional_pad_x, additional_pad_y],
                size=pkg.additional_pin_pad_size,
                drill=0,
                layers=Pad.LAYERS_SMT,
            )
        )

    # create mounting hole
    if pkg.mounting_hole_drill > 0:
        fpt.append(
            Pad(
                type=Pad.TYPE_NPTH,
                shape=Pad.SHAPE_OVAL,
                at=[x_mount_hole, y_mount_hole],
                size=[pkg.mounting_hole_drill, pkg.mounting_hole_drill],
                drill=pkg.mounting_hole_drill,
                layers=Pad.LAYERS_THT,
            )
        )

    # create THT pads
    for p in range(len(pads)):
        if p == 0:
            pad_shape = Pad.SHAPE_RECT
        else:
            pad_shape = Pad.SHAPE_OVAL
        fpt.append(
            Pad(
                number=p + 1,
                type=Pad.TYPE_THT,
                shape=pad_shape,
                at=pads[p],
                size=pkg.pad_dimensions,
                drill=pkg.drill,
                layers=Pad.LAYERS_THT,
            )
        )

    ###  FAB LAYER   ######################################################

    # Metal outline
    if height_fab_metal > 0:
        if len(pkg.plastic_angled) > 0:
            if len(pkg.metal_angled) > 0:
                addRectAngledTopNoBottom(
                    fpt,
                    [
                        left_fab_metal,
                        top_fab_plastic + pkg.plastic_angled[1],
                    ],
                    [
                        right_fab_metal,
                        top_fab_metal,
                    ],
                    pkg.metal_angled,
                    "F.Fab",
                    c.fab_line_width,
                )
            else:
                fpt.append(
                    Rectangle(
                        start=[
                            left_fab_metal,
                            top_fab_metal,
                        ],
                        end=[
                            right_fab_metal,
                            top_fab_plastic - pkg.plastic_angled[1],
                        ],
                        layer="F.Fab",
                        width=c.fab_line_width,
                    )
                )
        else:
            if len(pkg.metal_angled) > 0:
                addRectAngledTop(
                    fpt,
                    [
                        left_fab_metal,
                        top_fab_plastic,
                    ],
                    [
                        right_fab_metal,
                        top_fab_metal,
                    ],
                    pkg.metal_angled,
                    "F.Fab",
                    c.fab_line_width,
                )
            else:
                fpt.append(
                    Rectangle(
                        start=[
                            left_fab_metal,
                            top_fab_metal,
                        ],
                        end=[
                            right_fab_metal,
                            top_fab_plastic,
                        ],
                        layer="F.Fab",
                        width=c.fab_line_width,
                    )
                )

    # Plastic outline
    if len(pkg.plastic_angled) > 0:
        addRectAngledTop(
            fpt,
            [left_fab_plastic, bottom_fab_plastic],
            [
                right_fab_plastic,
                top_fab_plastic,
            ],
            pkg.plastic_angled,
            "F.Fab",
            c.fab_line_width,
        )
    else:
        fpt.append(
            Rectangle(
                start=[left_fab_plastic, bottom_fab_plastic],
                end=[
                    right_fab_plastic,
                    top_fab_plastic,
                ],
                layer="F.Fab",
                width=c.fab_line_width,
            )
        )

    # Mounting hole
    if pkg.mounting_hole_diameter > 0:
        fpt.append(
            Circle(
                center=[x_mount_hole, y_mount_hole],
                radius=pkg.mounting_hole_diameter / 2,
                layer="F.Fab",
                width=c.fab_line_width,
            )
        )

    # Pins
    for p in range(len(pads)):
        fpt.append(
            Rectangle(
                start=[
                    pads[p][0] - pkg.pin_width_height[0] / 2,
                    bottom_fab_plastic,
                ],
                end=[pads[p][0] + pkg.pin_width_height[0] / 2, pads[p][1]],
                layer="F.Fab",
                width=c.fab_line_width,
            )
        )

    ###  COURTYYRD  #######################################################

    cb = CourtyardBuilder.from_node(
        node=fpt, global_config=GLOBAL_CONFIG, offset_fab=courtyard_offset
    )
    fpt += cb.node

    ###  SILKSCREEN LAYER   ###############################################

    keepouts = []
    for p in range(len(pads)):
        if p == 0:
            addKeepout = addKeepoutRect
        else:
            addKeepout = addKeepoutRound
        keepouts += addKeepout(
            pads[p][0],
            pads[p][1],
            pkg.pad_dimensions[0] + 2 * c.silk_pad_clearance + c.silk_line_width,
            pkg.pad_dimensions[1] + 2 * c.silk_pad_clearance + c.silk_line_width,
        )
    if len(pkg.additional_pin_pad_size) > 0:
        clearance = c.silk_pad_clearance + c.silk_line_width / 2
        keepouts += addKeepoutRect(
            additional_pad_x,
            additional_pad_y,
            pkg.additional_pin_pad_size[0] + 2 * clearance,
            pkg.additional_pin_pad_size[1] + 2 * clearance,
        )

    addHLineWithKeepout(
        fpt,
        left_silk_plastic,
        right_silk_plastic,
        bottom_silk_plastic,
        "F.SilkS",
        c.silk_line_width,
        keepouts,
    )
    if height_fab_metal:
        addHLineWithKeepout(
            fpt,
            left_silk_plastic,
            right_silk_plastic,
            top_silk_metal,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fpt,
            left_silk_plastic,
            bottom_silk_plastic,
            top_silk_metal,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fpt,
            right_silk_plastic,
            bottom_silk_plastic,
            top_silk_metal,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
    else:
        addHLineWithKeepout(
            fpt,
            left_silk_plastic,
            right_silk_plastic,
            top_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fpt,
            left_silk_plastic,
            bottom_silk_plastic,
            top_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fpt,
            right_silk_plastic,
            bottom_silk_plastic,
            top_silk_plastic,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )

    for p in range(len(pads)):
        addVLineWithKeepout(
            fpt,
            pads[p][0] - c.silk_fab_offset - pkg.pin_width_height[0] / 2,
            bottom_silk_plastic,
            pads[p][1],
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fpt,
            pads[p][0] + c.silk_fab_offset + pkg.pin_width_height[0] / 2,
            bottom_silk_plastic,
            pads[p][1],
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )

    ### TEXT FIELDS  ######################################################

    addTextFields(
        fpt,
        configuration=GLOBAL_CONFIG,
        body_edges=cb.bbox,
        courtyard=cb.bbox,
        fp_name=fp.name,
        text_y_inside_position="center",
        allow_rotation=True,
    )

    save_footprint(fp, generator_name)

def generate_rect_to_fp_horizontal_tab_up(
    pkg: RectangularToSpec, id: str, generator_name: str
):
    fp = pkg.init_footprint("Horizontal", "TabUp", 0, PACKAGE_CONFIG, generator_name)
    c = GLOBAL_CONFIG
    courtyard_offset = GLOBAL_CONFIG.get_courtyard_offset(
        global_config.GlobalConfig.CourtyardType.DEFAULT
    )

    width_fab_plastic = pkg.plastic_dimensions[0]
    height_fab_plastic = pkg.plastic_dimensions[1]
    left_fab_plastic = -pkg.pin_offset_x
    right_fab_plastic = left_fab_plastic + width_fab_plastic
    top_fab_plastic = pkg.pin_min_length_before_90deg_bend
    bottom_fab_plastic = top_fab_plastic + height_fab_plastic

    width_fab_metal = pkg.metal_dimensions[0]
    height_fab_metal = pkg.metal_dimensions[1]
    bottom_fab_metal = top_fab_plastic + height_fab_metal
    left_fab_metal = left_fab_plastic + pkg.metal_offset_x
    right_fab_metal = left_fab_metal + width_fab_metal

    width_silk_plastic = width_fab_plastic + 2 * c.silk_fab_offset
    height_silk_plastic = height_fab_plastic + 2 * c.silk_fab_offset
    left_silk_plastic = left_fab_plastic - c.silk_fab_offset
    right_silk_plastic = left_silk_plastic + width_silk_plastic
    top_silk_plastic = top_fab_plastic - c.silk_fab_offset
    bottom_silk_plastic = top_silk_plastic + height_silk_plastic

    width_silk_metal = width_fab_metal + 2 * c.silk_fab_offset
    height_silk_metal = height_fab_metal + 2 * c.silk_fab_offset

    x_mount_hole = left_fab_plastic + pkg.mounting_hole_position[0]
    y_mount_hole = top_fab_plastic + pkg.mounting_hole_position[1]

    ###  PADS  ############################################################

    # create mounting hole
    if pkg.mounting_hole_drill > 0:
        fp.append(
            Pad(
                type=Pad.TYPE_NPTH,
                shape=Pad.SHAPE_OVAL,
                at=[x_mount_hole, y_mount_hole],
                size=[pkg.mounting_hole_drill, pkg.mounting_hole_drill],
                drill=pkg.mounting_hole_drill,
                layers=Pad.LAYERS_THT,
            )
        )

    # create pads
    x = 0
    for p in range(1, pkg.pins + 1):
        if p == 1:
            pad_shape = Pad.SHAPE_RECT
        else:
            pad_shape = Pad.SHAPE_OVAL
        fp.append(
            Pad(
                number=p,
                type=Pad.TYPE_THT,
                shape=pad_shape,
                at=[x, 0],
                size=pkg.pad_dimensions,
                drill=pkg.drill,
                layers=Pad.LAYERS_THT,
            )
        )

        if len(pkg.pitch_list) > 0 and p <= len(pkg.pitch_list):
            x += pkg.pitch_list[p - 1]
        else:
            x += pkg.pitch

    ###  FAB LAYER   ######################################################

    # Metal outline
    if height_fab_metal > 0:
        if len(pkg.metal_angled) > 0:
            addRectAngledBottomNoTop(
                fp,
                [
                    left_fab_metal,
                    bottom_fab_plastic - pkg.plastic_angled[1],
                ],
                [
                    right_fab_metal,
                    bottom_fab_metal,
                ],
                pkg.metal_angled,
                "F.Fab",
                c.fab_line_width,
            )
        else:
            fp.append(
                Rectangle(
                    start=[
                        left_fab_metal,
                        bottom_fab_plastic,
                    ],
                    end=[
                        right_fab_metal,
                        bottom_fab_metal,
                    ],
                    layer="F.Fab",
                    width=c.fab_line_width,
                )
            )

    # Plastic outline
    if len(pkg.plastic_angled) > 0:
        addRectAngledBottom(
            fp,
            [left_fab_plastic, top_fab_plastic],
            [
                right_fab_plastic,
                bottom_fab_plastic,
            ],
            pkg.plastic_angled,
            "F.Fab",
            c.fab_line_width,
        )
    else:
        fp.append(
            Rectangle(
                start=[left_fab_plastic, top_fab_plastic],
                end=[
                    right_fab_plastic,
                    bottom_fab_plastic,
                ],
                layer="F.Fab",
                width=c.fab_line_width,
            )
        )

    # Mounting hole
    if pkg.mounting_hole_diameter > 0:
        fp.append(
            Circle(
                center=[x_mount_hole, y_mount_hole],
                radius=pkg.mounting_hole_diameter / 2,
                layer="F.Fab",
                width=c.fab_line_width,
            )
        )
    x = 0

    # Pads
    for p in range(1, pkg.pins + 1):
        fp.append(
            Rectangle(
                start=[x - pkg.pin_width_height[0] / 2, top_fab_plastic],
                end=[x + pkg.pin_width_height[0] / 2, 0],
                layer="F.Fab",
                width=c.fab_line_width,
            )
        )
        if len(pkg.pitch_list) > 0 and p <= len(pkg.pitch_list):
            x = x + pkg.pitch_list[p - 1]
        else:
            x = x + pkg.pitch

    ###  COURTYYRD  #######################################################

    cb = CourtyardBuilder.from_node(
        node=fp, global_config=GLOBAL_CONFIG, offset_fab=courtyard_offset
    )
    fp += cb.node

    ###  SILKCSCREEN LAYER   ##############################################

    keepouts = []
    x = 0
    for p in range(1, pkg.pins + 1):
        if p == 1:
            keepouts = keepouts + addKeepoutRect(
                x,
                0,
                pkg.pad_dimensions[0]
                + 2 * c.silk_pad_clearance
                + c.silk_line_width,
                pkg.pad_dimensions[1]
                + 2 * c.silk_pad_clearance
                + c.silk_line_width,
            )
        else:
            keepouts = keepouts + addKeepoutRound(
                x,
                0,
                pkg.pad_dimensions[0]
                + 2 * c.silk_pad_clearance
                + c.silk_line_width,
                pkg.pad_dimensions[1]
                + 2 * c.silk_pad_clearance
                + c.silk_line_width,
            )
        x = x + pkg.pitch

    addHLineWithKeepout(
        fp,
        left_silk_plastic,
        right_silk_plastic,
        top_silk_plastic,
        "F.SilkS",
        c.silk_line_width,
        keepouts,
    )
    addHLineWithKeepout(
        fp,
        left_silk_plastic,
        right_silk_plastic,
        bottom_silk_plastic,
        "F.SilkS",
        c.silk_line_width,
        keepouts,
    )
    addVLineWithKeepout(
        fp,
        left_silk_plastic,
        top_silk_plastic,
        bottom_silk_plastic,
        "F.SilkS",
        c.silk_line_width,
        keepouts,
    )
    addVLineWithKeepout(
        fp,
        right_silk_plastic,
        top_silk_plastic,
        bottom_silk_plastic,
        "F.SilkS",
        c.silk_line_width,
        keepouts,
    )
    if height_fab_metal > 0:
        addHDLineWithKeepout(
            fp,
            left_silk_plastic + pkg.metal_offset_x,
            left_silk_plastic + pkg.metal_offset_x + width_silk_metal,
            top_silk_plastic + height_silk_metal,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVDLineWithKeepout(
            fp,
            left_silk_plastic + pkg.metal_offset_x,
            bottom_silk_plastic + c.silk_line_width * 2,
            top_silk_plastic + height_silk_metal,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVDLineWithKeepout(
            fp,
            left_silk_plastic + pkg.metal_offset_x + width_silk_metal,
            bottom_silk_plastic + c.silk_line_width * 2,
            top_silk_plastic + height_silk_metal,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
    x = 0
    for p in range(1, pkg.pins + 1):
        addVLineWithKeepout(
            fp,
            x - c.silk_fab_offset - pkg.pin_width_height[0] / 2,
            top_silk_plastic,
            pkg.pad_dimensions[1] / 2
            + c.silk_pad_clearance
            + c.silk_line_width / 2,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        addVLineWithKeepout(
            fp,
            x + c.silk_fab_offset + pkg.pin_width_height[0] / 2,
            top_silk_plastic,
            pkg.pad_dimensions[1] / 2
            + c.silk_pad_clearance
            + c.silk_line_width / 2,
            "F.SilkS",
            c.silk_line_width,
            keepouts,
        )
        if len(pkg.pitch_list) > 0 and p <= len(pkg.pitch_list):
            x += pkg.pitch_list[p - 1]
        else:
            x += pkg.pitch

    ### TEXT FIELDS  ######################################################

    addTextFields(
        fp,
        configuration=GLOBAL_CONFIG,
        body_edges=cb.bbox,
        courtyard=cb.bbox,
        fp_name=fp.name,
        text_y_inside_position="center",
        allow_rotation=True,
    )

    save_footprint(fp, generator_name)

def add_outline(node: Node, pkg: RoundToSpec, layer: str):
    c = GLOBAL_CONFIG
    match layer:
        case "F.Fab":
            mark_width = pkg.mark_width
            mark_length = pkg.mark_length
            diameter = pkg.diameter_outer
            line_width = c.fab_line_width
        case "F.SilkS":
            mark_width = pkg.mark_width + 2 * c.silk_fab_offset
            diameter = pkg.diameter_outer + 2 * c.silk_fab_offset
            line_width = c.silk_line_width
            u1 = math.cos(math.asin(pkg.mark_width / pkg.diameter_outer))
            u2 = math.cos(math.asin(mark_width / diameter))
            dr = pkg.diameter_outer * (u1 - u2) / 2
            mark_length = pkg.mark_length + dr
        case "F.CrtYd":
            courtyard_offset = c.get_courtyard_offset(
                global_config.GlobalConfig.CourtyardType.DEFAULT
            )
            mark_width = pkg.mark_width + 2 * courtyard_offset
            diameter = pkg.diameter_outer + 2 * courtyard_offset
            line_width = c.courtyard_line_width
            u1 = math.cos(math.asin(pkg.mark_width / pkg.diameter_outer))
            u2 = math.cos(math.asin(mark_width / diameter))
            dr = pkg.diameter_outer * (u1 - u2) / 2
            mark_length = pkg.mark_length + dr

    if pkg.mark_width > 0 and pkg.mark_length > 0:
        a = math.radians(pkg.mark_angle)
        da = math.asin(mark_width / diameter)
        a1 = a + da
        a2 = a - da
        x1 = [
            (diameter / 2) * math.cos(a1),
            (diameter / 2) * math.sin(a1),
        ]
        x3 = [
            (diameter / 2) * math.cos(a2),
            (diameter / 2) * math.sin(a2),
        ]
        dx = mark_length * math.cos(a)
        dy = mark_length * math.sin(a)
        x2 = [x1[0] + dx, x1[1] + dy]
        x4 = [x3[0] + dx, x3[1] + dy]
        node.append(
            Arc(
                center=[0, 0],
                start=x1,
                angle=(360 - 2 * math.degrees(da)),
                layer=layer,
                width=line_width,
            )
        )
        node.append(Line(start=x1, end=x2, layer=layer, width=line_width))
        node.append(Line(start=x2, end=x4, layer=layer, width=line_width))
        node.append(Line(start=x4, end=x3, layer=layer, width=line_width))
    else:
        node.append(
            Circle(
                center=[0, 0],
                radius=diameter / 2,
                layer=layer,
                width=line_width,
            )
        )

def generate_round_to_fp(
    pkg: RoundToSpec, id: str, footprint_type: str, generator_name: str
):
    fp = pkg.init_footprint(footprint_type, generator_name)
    c = GLOBAL_CONFIG
    text_offset = 1

    d_slk = pkg.diameter_outer + 2 * c.silk_fab_offset

    # calculate pad positions
    pads = []
    yshift = 0
    xshift = 0
    a = pkg.pin1_angle
    firstPin = True
    for p in range(1, pkg.pins + 1):
        x = pkg.pin_circle_diameter / 2 * math.cos(math.radians(a))
        y = pkg.pin_circle_diameter / 2 * math.sin(math.radians(a))
        a += pkg.angle_between_pins
        if p in pkg.deleted_pins:
            continue
        pads.append([x, y])
        if firstPin:
            xshift = -x
            yshift = -y
            firstPin = False

    txt_t = -d_slk / 2 - text_offset
    txt_b = d_slk / 2 + text_offset

    fpt = Translation(xshift, yshift)
    fp.append(fpt)

    # set general values
    fpt.append(
        Property(
            name=Property.REFERENCE, text="REF**", at=[0, txt_t], layer="F.SilkS"
        )
    )
    fpt.append(Text(text="${REFERENCE}", at=[0, txt_t], layer="F.Fab"))
    fpt.append(
        Property(name=Property.VALUE, text=fp.name, at=[0, txt_b], layer="F.Fab")
    )

    # create FAB layer
    add_outline(fpt, pkg, "F.Fab")

    fpt.append(
        Circle(
            center=[0, 0],
            radius=pkg.diameter_inner / 2,
            layer="F.Fab",
            width=c.fab_line_width,
        )
    )

    if footprint_type == "window" or footprint_type == "lens":
        addCircleLF(
            fpt,
            [0, 0],
            pkg.window_diameter / 2,
            "F.Fab",
            c.fab_line_width,
            4 * c.fab_line_width,
        )

    # create silkscreen layer
    add_outline(fpt, pkg, "F.SilkS")

    # Courtyard
    add_outline(fpt, pkg, "F.CrtYd")

    # create pads
    for p in range(len(pads)):
        if p == 0:
            fpt.append(
                Pad(
                    number=p + 1,
                    type=Pad.TYPE_THT,
                    shape=Pad.SHAPE_OVAL,
                    at=pads[p],
                    size=[
                        round_to_grid_e(pkg.pad_dimensions[0] * 1.3, 0.1),
                        pkg.pad_dimensions[1],
                    ],
                    drill=pkg.drill,
                    layers=Pad.LAYERS_THT,
                )
            )
        else:
            fpt.append(
                Pad(
                    number=p + 1,
                    type=Pad.TYPE_THT,
                    shape=Pad.SHAPE_OVAL,
                    at=pads[p],
                    size=pkg.pad_dimensions,
                    drill=pkg.drill,
                    layers=Pad.LAYERS_THT,
                )
            )

    save_footprint(fp, generator_name)

