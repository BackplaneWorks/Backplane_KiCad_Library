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
from math import  ceil, floor
from kilibs.geom import BoundingBox, Direction
from KicadModTree import *
from generators.tools.footprint.drawing_tools import (
    round_to_grid,
    SilkArrowSize,
)
from generators.tools.footprint.drawing_tools_silk import draw_silk_triangle_clear_of_fab_hline_and_pad
from generators.tools.footprint.drawing_tools_fab import draw_chamfer_rect_fab, draw_pin1_chevron_on_hline
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


lib_by_conn_category = True

series = "84982"
manufacturer = 'TE-Connectivity'
conn_category = "FFC-FPC"
orientation = 'V'
datasheet = "https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=84982&DocType=Customer+Drawing&DocLang=English&PartCntxt=84982-8&DocFormat=pdf"

pincounts = range(4, 31)
d_between_rows = 1.8        # [mm]
pad_height_odd = 1.7        # [mm]
pad_height_even = 1.9       # [mm]
pad_inset_even = 0.7        # [mm] - inside of pad to housing edge on the top edge
pad_width = 0.6             # [mm]
pad_pitch = 1.0             # [mm]
center_to_housing = 1.6     # [mm]
housing_length = 3.0        # [mm]
housing_width_4pin = 6.0    # [mm]
pins_width_4pin = 3.0       # [mm]
pin1_marker_l = 0.566       # [mm]

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pincount, configuration):
    prefix = "" if (pincount < 10) else f"{pincount // 10:d}-"
    partnumber = f"{prefix:s}{series:s}-{pincount % 10}"

    footprint_name = f"TE_{partnumber:s}_2Rows-{pincount:02g}Pins-P1.0mm_Vertical"

    # initialise footprint
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.description = f"TE FPC connector, {pincount:02g} top-side contacts, 1.0mm pitch, SMT, {datasheet}"
    kicad_mod.tags = [partnumber, "vertical"]

    housing_y_offset = housing_length / 2
    even_pad_inner_edge_y = -housing_y_offset + pad_inset_even
    row_offset_even = even_pad_inner_edge_y - pad_height_even / 2
    row_offset_odd = even_pad_inner_edge_y + d_between_rows + pad_height_odd / 2

    # create pads
    if bool(pincount % 2):
        upper_pincount = floor(pincount / 2)
        bottom_pincount = ceil(pincount / 2)
    else:
        upper_pincount = bottom_pincount = round(pincount / 2)

    pins_width = pins_width_4pin + (pincount - 4) * pad_pitch
    pin_edge_offset = -pins_width / 2

    even_pads =PadArray(
        initial=2, increment=2, pincount=upper_pincount, x_spacing=2 * pad_pitch,
        start=[pin_edge_offset + pad_pitch, row_offset_even],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[pad_width, pad_height_even], layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler)

    odd_pads = PadArray(
        initial=1, increment=2, pincount=bottom_pincount, x_spacing=2 * pad_pitch,
        start=[pin_edge_offset, row_offset_odd],
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT,
        size=[pad_width, pad_height_odd], layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler)

    kicad_mod.append(even_pads)
    kicad_mod.append(odd_pads)

    # create fab outline
    housing_width = housing_width_4pin + (pincount - 4) * pad_pitch
    housing_x_offset = housing_width / 2

    body_edges = BoundingBox(
        Vector2D(-housing_x_offset, -housing_y_offset),
        Vector2D(housing_x_offset, housing_y_offset),
    )

    fab_rect = draw_chamfer_rect_fab(
        size=Vector2D(housing_width, housing_length), global_config=global_config
    )
    kicad_mod.append(fab_rect)

    # create fab pin 1 marker
    fab_chevron = draw_pin1_chevron_on_hline(
        line_y=housing_y_offset,
        apex_x=pin_edge_offset,
        chevron_length=0.8,
        direction=Direction.NORTH,
        global_config=global_config,
    )
    kicad_mod.append(fab_chevron)

    # create silkscreen outline
    silk_offset = global_config.silk_fab_offset
    silk_pad_offset = global_config.silk_pad_offset
    housing_x_silk_offset = housing_x_offset + silk_offset
    housing_y_silk_offset = housing_y_offset + silk_offset

    # Left silk end bracket
    kicad_mod.append(PolygonLine(
        shape=[
            [pin_edge_offset + pad_pitch - pad_width / 2 - silk_pad_offset, -housing_y_silk_offset],
            [-housing_x_silk_offset + pin1_marker_l + silk_offset, -housing_y_silk_offset],
            [-housing_x_silk_offset, -housing_y_silk_offset + pin1_marker_l + silk_offset],
            [-housing_x_silk_offset, housing_y_silk_offset],
            [pin_edge_offset - pad_width / 2 - 0.2, housing_y_silk_offset],
        ],
        layer='F.SilkS',
        width=global_config.silk_line_width))

    # Right silk end bracket
    kicad_mod.append(PolygonLine(
        shape=[
            [pin_edge_offset + ((bottom_pincount - 1) * 2) * pad_pitch + pad_width / 2 + silk_pad_offset, housing_y_silk_offset],
            [housing_x_silk_offset, housing_y_silk_offset],
            [housing_x_silk_offset, -housing_y_silk_offset],
            [pin_edge_offset + ((upper_pincount - 1) * 2 + 1) * pad_pitch + pad_width / 2 + silk_pad_offset, -housing_y_silk_offset]],
        layer='F.SilkS',
        width=global_config.silk_line_width))

    # Pin 1 silk marker
    pad1 = odd_pads.get_pad_with_name(1)
    arrow = draw_silk_triangle_clear_of_fab_hline_and_pad(
        global_config=global_config,
        pad=pad1,
        arrow_direction=Direction.EAST,
        line_y=housing_y_silk_offset,
        # 3 is a non-specific number that seems to give nice spacing
        line_clearance_y=3 * global_config.silk_line_width,
        arrow_size=SilkArrowSize.LARGE,
    )
    kicad_mod.append(arrow)

    courtyard_precision = global_config.courtyard_grid
    courtyard_clearance = global_config.get_courtyard_offset(
        GC.GlobalConfig.CourtyardType.CONNECTOR
    )

    courtyard_x = round_to_grid(housing_x_offset + courtyard_clearance, courtyard_precision)
    courtyard_y_south = round_to_grid(row_offset_odd + pad_height_odd / 2.0 + courtyard_clearance, courtyard_precision)
    courtyard_y_north = round_to_grid(row_offset_even - pad_height_even / 2.0 - courtyard_clearance, courtyard_precision)

    kicad_mod.append(Rectangle(start=[-courtyard_x, courtyard_y_south], end=[courtyard_x, courtyard_y_north],
        layer='F.CrtYd', width=global_config.courtyard_line_width))

    courtyard_box = BoundingBox(
        Vector2D(-courtyard_x, courtyard_y_north),
        Vector2D(courtyard_x, courtyard_y_south),
    )

    ########################## Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=global_config, body_edges=body_edges,
        courtyard=courtyard_box, fp_name=footprint_name, text_y_inside_position="center")

    ##################### Output and 3d model ############################
    model3d_path_prefix = global_config.model_3d_prefix
    model3d_path_suffix = global_config.model_3d_suffix

    if lib_by_conn_category:
        lib_name = configuration['lib_name_specific_function_format_string'].format(category=conn_category)
    else:
        lib_name = configuration['lib_name_format_string'].format(man=manufacturer)

    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    for pincount in pincounts:
        generate_one_footprint(generator_name, global_config, pincount, configuration)
    return len(pincounts)
