# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but without any
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

"""

Drawing:
https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Customer+Drawing%7F188275%7FS4%7Fpdf%7FEnglish%7FENG_CD_188275_S4.pdf%7F2-188275-0

"""
import math
from typing import Any
from KicadModTree import *
from generators.tools.footprint.drawing_tools import SilkArrowSize
from generators.tools.footprint.drawing_tools_silk import draw_silk_triangle_for_pad
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC
from kilibs.geom import Direction


man_lib = 'TE-Connectivity'
man_short = 'TE'
series = 'Micro-MaTch'
series_no = '188275'
orientation = 'V'
pitch = 1.27
pad_size_x = 1.5
pad_size_y = 3.0
y_offset_between_rows = pad_size_y + 1.5
body_width = 5.2
# B size in datasheet is rounded, this is the max value, taken from the 20 pin model
b20_size_from_datasheet = 27.5
x_overhang_from_middle_of_pin = (b20_size_from_datasheet - 19 * pitch) / 2
pins_per_row_range = (4, 6, 8, 10, 12, 14, 16, 18, 20)
drawing_url = 'https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Customer+Drawing%7F188275%7FS4%7Fpdf%7FEnglish%7FENG_CD_188275_S4.pdf%7F2-188275-0'


def make_part_number(pincount):
    if pincount < 4 or pincount > 20:
        raise ValueError('Requested pin count out of series range')
    if pincount % 2 != 0:
        raise ValueError('Series supports only even numbers of pins')
    prefix = 7 if pincount < 10 else 8 if pincount < 20 else 9
    return f'{prefix}-{series_no}-{pincount % 10}'


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pincount, configuration):
    partno = make_part_number(pincount)

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(
        man=man_short,
        series=series,
        mpn=partno,
        num_rows=2,
        pins_per_row=pincount // 2,
        mounting_pad='',
        pitch=pitch,
        orientation=orientation_str
    )
    footprint_name = footprint_name.replace(' ', '_')

    # Initialize footprint
    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    descr_str = f'{man_lib} {series} female-on-board SMD {pincount} pin connector, {drawing_url}'
    keywords = []
    keywords.append(configuration['keyword_fp_string'].format(
        man=man_lib,
        series=series,
        entry=orientation_str
    ))
    keywords.append(partno)
    kicad_mod.setDescription(descr_str)
    kicad_mod.setTags(' '.join(keywords))

    # Pad position calculations
    x_pin1 = -(pincount / 2 - 0.5) * pitch
    silk_pad_clearance = configuration['silk_pad_clearance']
    silk_line_width = configuration['silk_line_width']

    # Create pads
    odd_pads = PadArray(
        start=[x_pin1, -y_offset_between_rows / 2],
        initial=1,
        increment=2,
        pincount=pincount // 2,
        x_spacing=pitch * 2,
        type=Pad.TYPE_SMT,
        shape=Pad.SHAPE_ROUNDRECT,
        size=[pad_size_x, pad_size_y],
        layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler,
    )
    kicad_mod.append(odd_pads)
    kicad_mod.append(PadArray(
        start=[x_pin1 + pitch, y_offset_between_rows / 2],
        initial=2,
        increment=2,
        pincount=pincount // 2,
        x_spacing=pitch * 2,
        type=Pad.TYPE_SMT,
        shape=Pad.SHAPE_ROUNDRECT,
        size=[pad_size_x, pad_size_y],
        layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler,
    ))

    # Calculate body edge
    body_edge = {
        'left': x_pin1 - x_overhang_from_middle_of_pin,
        'right': x_pin1 + (pincount - 1) * pitch + x_overhang_from_middle_of_pin,
        'top': -body_width / 2,
        'bottom': body_width / 2,
    }

    # Add fabrication outline (with polarization notch on the left side)
    notch_depth = body_width / 8
    fab_notch_top_y = -body_width / 4
    fab_notch_bottom_y = body_width / 4
    fab_notch_inner_x = body_edge['left'] + notch_depth
    fab_polygon_points = [
        (body_edge['left'], body_edge['top']),
        (body_edge['right'], body_edge['top']),
        (body_edge['right'], body_edge['bottom']),
        (body_edge['left'], body_edge['bottom']),
        (body_edge['left'], fab_notch_bottom_y),
        (fab_notch_inner_x, fab_notch_bottom_y),
        (fab_notch_inner_x, fab_notch_top_y),
        (body_edge['left'], fab_notch_top_y),
        (body_edge['left'], body_edge['top']),
    ]
    kicad_mod.append(PolygonLine(
        shape=fab_polygon_points,
        layer='F.Fab',
        width=configuration['fab_line_width']
    ))

    # Pin 1 silk arrow marker
    pin1_arrow = draw_silk_triangle_for_pad(
        pad=odd_pads.get_pad_with_name(1),
        arrow_size=SilkArrowSize.LARGE,
        arrow_direction=Direction.SOUTH,
        stroke_width=global_config.silk_line_width,
        pad_silk_offset=global_config.silk_pad_offset,
    )
    kicad_mod.append(pin1_arrow)

    # Add silkscreen outline (0.11mm outside the F.Fab lines)
    silk_fab_offset = 0.11
    silk_top = body_edge['top'] - silk_fab_offset
    silk_bottom = body_edge['bottom'] + silk_fab_offset
    silk_body_left = body_edge['left'] - silk_fab_offset
    silk_body_right = body_edge['right'] + silk_fab_offset
    silk_left = x_pin1 - pad_size_x / 2 - silk_pad_clearance - silk_line_width / 2
    silk_right = x_pin1 + (pincount - 2) * pitch + pad_size_x / 2 + silk_pad_clearance + silk_line_width / 2

    # Leftside outline (with polarization notch, no pin-1 stub)
    # For the notch (a concave feature), "outside" means towards the material,
    # so the silk notch is smaller than the fab notch.
    silk_notch_top_y = fab_notch_top_y + silk_fab_offset
    silk_notch_bottom_y = fab_notch_bottom_y - silk_fab_offset
    silk_notch_inner_x = fab_notch_inner_x - silk_fab_offset
    silk_outline_left = [
        (silk_left, silk_top),
        (silk_body_left, silk_top),
        (silk_body_left, silk_notch_top_y),
        (silk_notch_inner_x, silk_notch_top_y),
        (silk_notch_inner_x, silk_notch_bottom_y),
        (silk_body_left, silk_notch_bottom_y),
        (silk_body_left, silk_bottom),
        (x_pin1 + pitch - pad_size_x / 2 - silk_pad_clearance - silk_line_width / 2, silk_bottom),
    ]
    kicad_mod.append(PolygonLine(
        shape=silk_outline_left,
        layer='F.SilkS',
        width=configuration['silk_line_width']
    ))

    # Rightside outline
    silk_outline_right = [
        (silk_right, silk_top),
        (silk_body_right, silk_top),
        (silk_body_right, silk_bottom),
        (x_pin1 + (pincount - 1) * pitch + pad_size_x / 2 + silk_pad_clearance + silk_line_width / 2, silk_bottom),
    ]
    kicad_mod.append(PolygonLine(
        shape=silk_outline_right,
        layer='F.SilkS',
        width=configuration['silk_line_width']
    ))

    # Courtyard
    court_offs = configuration['courtyard_offset']['connector']
    court_grid = configuration['courtyard_grid']
    y_total_pin_size = pad_size_y + y_offset_between_rows
    cx1 = math.floor((body_edge['left'] - court_offs) / court_grid) * court_grid
    cx2 = math.ceil((body_edge['right'] + court_offs) / court_grid) * court_grid
    cy1 = math.floor((-y_total_pin_size / 2 - court_offs) / court_grid) * court_grid
    cy2 = math.ceil((y_total_pin_size / 2 + court_offs) / court_grid) * court_grid
    kicad_mod.append(Rectangle(
        start=(cx1, cy1), end=(cx2, cy2),
        layer='F.CrtYd', width=configuration['courtyard_line_width']
    ))

    # Text fields
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top': cy1, 'bottom': cy2}, fp_name=footprint_name)

    # Output
    model3d_path_prefix = configuration.get('3d_model_prefix', global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix', global_config.model_3d_suffix)
    lib_name = configuration['lib_name_format_string'].format(man=man_lib)
    model_name = f'{model3d_path_prefix}{lib_name}.3dshapes/{footprint_name}{model3d_path_suffix}'
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    for pins_per_row in pins_per_row_range:
        generate_one_footprint(generator_name, global_config, pins_per_row, configuration)
    return len(pins_per_row_range)
