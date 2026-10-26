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

from typing import Any
from kilibs.geom import Direction, GeomRectangle, Vector2D
from KicadModTree import (
    Pad,
    PadArray,
    Footprint,
    FootprintType,
    Polygon,
    Rectangle,
    Model,
    PolygonLine,
)

from generators.tools.footprint.save_footprint import write_footprint
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.drawing_tools_fab import draw_pin1_chevron_on_hline
from generators.tools.footprint.drawing_tools_silk import draw_silk_triangle_for_pad, SilkArrowSize
from kilibs.config import global_config as GC
from generators.tools.footprint.footprint_text_fields import addTextFields


manufacturer = 'Amphenol'
conn_category = 'FFC-FPC'

lib_by_conn_category = True

families = (
    {
        "name": "F32Q",
        "description_name": "F32Q/T",
        "side": "top",
        "compatible_mpns": ["F32T"], # F32T is the no-logo version of F32Q
        "datasheet": "https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/f32q-f32t.pdf",
    },
    {
        "name": "F32R",
        "side": "bottom",
        "description_name": "F32R/J",
        "compatible_mpns": ["F32J"], # F32J is the no-logo version of F32Q
        "datasheet": "https://cdn.amphenol-icc.com/media/wysiwyg/files/drawing/f32r-f32j.pdf",
    },
)

pincounts = range(4, 61)

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, family, pincount, configuration):

    footprint_name = (
        "{mfg:s}_{family:s}-1A7x1-110{pc:02g}_1x{pc:02g}-1MP_P0.5mm_Horizontal".format(
            mfg=manufacturer, family=family["name"], pc=pincount
        )
    )

    datasheet = family["datasheet"]

    # calculate working values
    pitch = 0.5
    pad_width = 0.3
    pad_height = 1.1
    pad_y = -(5.50 - 1.0)/2 -1.2 + pad_height/2  # So that middle of body in fab layer is at (0,0)
    pad_x_span = pitch * (pincount - 1)
    pad1_x = -pad_x_span / 2

    tab_width = 2.10
    tab_height = 1.95
    tab_x = pad_x_span/2 + 3.30 - tab_width/2
    tab_y = pad_y - pad_height/2 + (1.2 - 0.5) + tab_height/2

    body_y1 = pad_y - pad_height/2 + 1.2
    half_body_width = pad_x_span/2 + 2.65
    actuator_y1 = body_y1 + 5.5 - 1.0
    half_actuator_width = half_body_width + 1.25
    ear_height = 1.5  # Measured on STEP model

    body_edge = GeomRectangle(
        start=Vector2D(-half_body_width, body_y1),
        end=Vector2D(half_body_width, actuator_y1)
    )

    courtyard_clearance = global_config.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.CONNECTOR
    )
    courtyard_x = round_to_grid(half_actuator_width + courtyard_clearance, global_config.courtyard_grid)
    courtyard_y1 = round_to_grid(pad_y - pad_height/2 - courtyard_clearance, global_config.courtyard_grid)
    courtyard_y2 = round_to_grid(actuator_y1 + courtyard_clearance, global_config.courtyard_grid)

    courtyard_rect = GeomRectangle(
        start=Vector2D(-courtyard_x, courtyard_y1),
        end=Vector2D(courtyard_x, courtyard_y2)
    )

    desc = "{mfg} {familiy_name} FPC connector, {pc:g} {side}-side contacts, 0.5mm pitch, SMT, {ds}".format(
        mfg=manufacturer,
        familiy_name=family["description_name"],
        pc=pincount,
        side=family["side"],
        ds=datasheet,
    )

    # initialise footprint
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.description = desc

    kicad_mod.tags = family["compatible_mpns"]

    # create pads
    pad_array = PadArray(
        pincount=pincount,
        x_spacing=pitch,
        center=[0, pad_y],
        type=Pad.TYPE_SMT,
        shape=Pad.SHAPE_ROUNDRECT,
        round_radius_handler=global_config.roundrect_radius_handler,
        size=[pad_width, pad_height],
        layers=Pad.LAYERS_SMT,
    )

    pad1 = pad_array.get_pad_with_name(1)

    kicad_mod += pad_array

    mounting_pad_name = global_config.get_pad_name(GC.PadName.MECHANICAL)

    # create tab (smt mounting) pads
    kicad_mod += Pad(
        number=mounting_pad_name,
        at=[tab_x, tab_y],
        type=Pad.TYPE_SMT,
        shape=Pad.SHAPE_CUSTOM,
        size=[1, 1],
        layers=Pad.LAYERS_SMT,
        primitives=[
            Polygon(
                shape=[
                    (-tab_width / 2, -tab_height / 2),
                    (-tab_width / 2, tab_height / 2),
                    (tab_width / 2 - 0.8, tab_height / 2),
                    (tab_width / 2 - 0.8, tab_height / 2 - 0.35),
                    (tab_width / 2, tab_height / 2 - 0.35),
                    (tab_width / 2, -tab_height / 2),
                    (-tab_width / 2, -tab_height / 2),
                ],
                width=0,
                fill=True,
            )
        ],
    )

    kicad_mod += Pad(
        number=mounting_pad_name,
        at=[-tab_x, tab_y],
        type=Pad.TYPE_SMT,
        shape=Pad.SHAPE_CUSTOM,
        size=[1, 1],
        layers=Pad.LAYERS_SMT,
        primitives=[
            Polygon(
                shape=[
                    (-tab_width / 2, -tab_height / 2),
                    (-tab_width / 2, tab_height / 2),
                    (tab_width / 2 - 0.8, tab_height / 2),
                    (tab_width / 2 - 0.8, tab_height / 2 - 0.35),
                    (tab_width / 2, tab_height / 2 - 0.35),
                    (tab_width / 2, -tab_height / 2),
                    (-tab_width / 2, -tab_height / 2),
                ],
                x_mirror=0,
                width=0,
                fill=True,
            )
        ],
    )

    # create fab outline
    kicad_mod += PolygonLine(
        shape=[
            (-half_body_width, body_y1),
            (half_body_width, body_y1),
            (half_body_width, actuator_y1 - ear_height),
            (half_actuator_width, actuator_y1 - ear_height),
            (half_actuator_width, actuator_y1),
            (-half_actuator_width, actuator_y1),
            (-half_actuator_width, actuator_y1 - ear_height),
            (-half_body_width, actuator_y1 - ear_height),
            (-half_body_width, body_y1),
        ],
        layer="F.Fab",
        width=global_config.fab_line_width,
    )

    kicad_mod += draw_pin1_chevron_on_hline(
        line_y=body_y1,
        apex_x=pad1_x,
        global_config=global_config,
        direction=Direction.SOUTH,
        chevron_length=global_config.fab_pin1_marker_length,
    )

    silk_offset = global_config.silk_pad_offset
    silk_fab_offset = global_config.silk_fab_offset
    silk_line_width = global_config.silk_line_width

    # create silkscreen outline
    kicad_mod += PolygonLine(
        shape=[
            (pad1_x + pad_x_span + pad_width/2 + silk_offset, tab_y - tab_height/2 - silk_offset),
            (tab_x + tab_width/2 + silk_offset, tab_y - tab_height/2 - silk_offset),
            (tab_x + tab_width/2 + silk_offset, actuator_y1 - ear_height - silk_fab_offset),
            (half_actuator_width + silk_fab_offset, actuator_y1 - ear_height - silk_fab_offset),
            (half_actuator_width + silk_fab_offset, actuator_y1 + silk_fab_offset),
            (-half_actuator_width - silk_fab_offset, actuator_y1 + silk_fab_offset),
            (-half_actuator_width - silk_fab_offset, actuator_y1 - ear_height - silk_fab_offset),
            (-tab_x - tab_width/2 - silk_offset, actuator_y1 - ear_height - silk_fab_offset),
            (-tab_x - tab_width/2 - silk_offset, tab_y - tab_height/2 - silk_offset),
            (pad1_x - pad_width/2 - silk_offset - 1, tab_y - tab_height/2 - silk_offset),
        ],
        layer='F.SilkS',
        width=silk_line_width
    )  # fmt: skip

    kicad_mod += draw_silk_triangle_for_pad(
        pad=pad1,
        arrow_direction=Direction.EAST,
        pad_silk_offset=global_config.silk_pad_offset,
        arrow_size=SilkArrowSize.MEDIUM,
        stroke_width=global_config.silk_line_width,
    )

    # create courtyard
    kicad_mod += Rectangle(
        start=courtyard_rect.top_left,
        end=courtyard_rect.bottom_right,
        layer="F.CrtYd",
        width=global_config.courtyard_line_width,
    )

    ######################### Text Fields ###############################
    addTextFields(
        kicad_mod=kicad_mod,
        configuration=global_config,
        body_edges=body_edge,
        courtyard=courtyard_rect,
        fp_name=footprint_name,
        text_y_inside_position="center",
    )

    ##################### Output and 3d model ############################
    if lib_by_conn_category:
        lib_name = configuration['lib_name_specific_function_format_string'].format(category=conn_category)
    else:
        lib_name = configuration['lib_name_format_string'].format(man=manufacturer)

    model_name = (
        "{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{suffix}".format(
            model3d_path_prefix=global_config.model_3d_prefix,
            lib_name=lib_name,
            fp_name=footprint_name,
            suffix=global_config.model_3d_suffix,
        )
    )
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    for family in families:
        for pincount in pincounts:
            generate_one_footprint(generator_name, global_config, family, pincount, configuration)
            num_fps_generated += 1
    return num_fps_generated
