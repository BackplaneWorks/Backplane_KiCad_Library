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
from math import sqrt

from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


draw_inner_details = False

series = "MATE-N-LOK"
series_long = 'Mini-Universal MATE-N-LOK'
man_lib = 'TE-Connectivity'
man_short_fp_name = 'TE'
orientation = 'H'
datasheet = "http://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=82181_SOFTSHELL_HIGH_DENSITY&DocType=CS&DocLang=EN"

# Molex part number
# n = number of circuits per row
variant_params = {
    'in_line':{
        'pins_per_row_range': [1,2,3],
        'number_of_rows': 1,
        'style': 'in_line',
        'number_pegs': 1,
        'peg_from_center': 0,
        'part_code': {
                1: '1-794374-x',
                2: '1-770966-x',
                3: '1-770967-x'
            }
        },
    'dual1':{
        'pins_per_row_range': range(2,7),
        'number_of_rows': 2,
        'style': 'dual_row',
        'number_pegs': 1,
        'peg_from_center': 0,
        'part_code': {
                4: '1-770968-x',
                6: '1-770969-x',
                8: '1-770970-x',
                10: '1-770971-x',
                12: '1-770972-x'
            }
        },
    'dual2':{
        'pins_per_row_range': [7,9],
        'number_of_rows': 2,
        'style': 'dual_row',
        'number_pegs': 2,
        'peg_from_center': 8.28,
        'part_code': {
                14: '1-770973-x',
                18: '1-794105-x'
            }
        },
    'dual3':{
        'pins_per_row_range': [8,10,12],
        'number_of_rows': 2,
        'style': 'dual_row',
        'number_pegs': 2,
        'peg_from_center': 10.38,
        'part_code': {
                16: '1-770974-x',
                20: '1-794106-x',
                24: '1-794108-x'
            }
        },
    'dual4':{
        'pins_per_row_range': [11],
        'number_of_rows': 2,
        'style': 'dual_row',
        'number_pegs': 2,
        'peg_from_center': 12.42,
        'part_code': {
                22: '1-794107-x'
            }
        },
}

pitch = 4.14
drill = 1.4
pad_to_pad_clearance = 1.5
max_annular_ring = 0.95
min_annular_ring = 0.15

peg_drill = 3.86
peg_to_nearest_pin = 7.34
width = 12.7

peg_to_body_right = 6.86


def generate_one_footprint(
    generator_name: str, global_config: GC.GlobalConfig, pins_per_row, variant_param, configuration):
    number_of_rows = variant_param['number_of_rows']

    mpn = variant_param['part_code'][pins_per_row*number_of_rows].format(n=pins_per_row*2)

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=man_short_fp_name,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    descr_format_str = "Molex {:s}, old mpn/engineering number: {:s}, {:d} Pins per row ({:s})"
    kicad_mod.setDescription(descr_format_str.format(
        series_long, mpn, pins_per_row, datasheet))
    tags = configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=man_short_fp_name,
        entry=configuration['entry_direction'][orientation])
    kicad_mod.setTags(tags)

    silk_pad_off = configuration['silk_pad_clearance']+configuration['silk_line_width']/2
    silk_fab_offset = configuration['silk_fab_offset']

    pad_size = [pitch - pad_to_pad_clearance, pitch - pad_to_pad_clearance]
    if number_of_rows == 1:
        pad_size[1] = drill + 2*max_annular_ring
    else:
        if pad_size[1] - drill < 2*min_annular_ring:
            pad_size[1] = drill + 2*min_annular_ring
        if pad_size[1] - drill > 2*max_annular_ring:
            pad_size[1] = drill + 2*max_annular_ring

    if pad_size[0] - drill < 2*min_annular_ring:
        pad_size[0] = drill + 2*min_annular_ring
    if pad_size[0] - drill > 2*max_annular_ring:
        pad_size[0] = drill + 2*max_annular_ring

    pad_shape = Pad.SHAPE_OVAL
    if pad_size[0] == pad_size[1]:
        pad_shape = Pad.SHAPE_CIRCLE

    peg_from_center = variant_param['peg_from_center']

    # Single row and dual row headers have opposite pin orders!
    if number_of_rows == 1:
        first_to_last_pad_x = (pins_per_row-1)*pitch
        first_to_last_pad_y = (number_of_rows-1)*pitch

        center_x = first_to_last_pad_x/2
        peg_x = center_x
        peg_y = (number_of_rows - 1) * pitch + peg_to_nearest_pin
        peg_pos = [[peg_x + peg_from_center, peg_y]]
        if variant_param['number_pegs'] == 2:
            peg_pos.append([peg_x - peg_from_center, peg_y])

        y2 = peg_y + peg_to_body_right
        y1 = y2 - width
        body_length = 5.72 + first_to_last_pad_x
        x1 = -(body_length - first_to_last_pad_x)/2
        x2 = x1 + body_length
    else:
        first_to_last_pad_y = (pins_per_row-1)*pitch
        first_to_last_pad_x = (number_of_rows-1)*pitch

        center_y = first_to_last_pad_y/2
        peg_x = (number_of_rows - 1) * pitch + peg_to_nearest_pin
        peg_pos = [[peg_x, center_y + peg_from_center]]
        if variant_param['number_pegs'] == 2:
            peg_pos.append([peg_x, center_y - peg_from_center])

        x2 = peg_x + peg_to_body_right
        x1 = x2 - width
        body_length = 5.72 + first_to_last_pad_y
        y1 = -(body_length - first_to_last_pad_y) / 2
        y2 = y1 + body_length
    for peg in peg_pos:
        kicad_mod.append(Pad(at=peg, type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
            size=peg_drill, drill=peg_drill, layers=Pad.LAYERS_NPTH))

    #calculate fp dimensions
    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = body_edge.copy()
    if number_of_rows==1:
        bounding_box['top'] = -pad_size[1]/2
    else:
        bounding_box['left'] = -pad_size[0]/2

    #generate the pads
    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    for row_idx in range(number_of_rows):
        initial = row_idx*pins_per_row+1
        kicad_mod.append(PadArray(
            pincount=pins_per_row, initial=initial,
            start=[0, row_idx * pitch] if number_of_rows==1 else [row_idx * pitch, 0],
            spacing=[pitch, 0] if number_of_rows==1 else [0, pitch],
            type=Pad.TYPE_THT,
            shape=pad_shape,
            size=pad_size,
            drill=drill,
            layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params,
        ))

    #draw the outline of the shape
    kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2],
        layer='F.Fab',width=configuration['fab_line_width']))

    if number_of_rows==1:
        dy = body_edge['top'] - silk_fab_offset - (number_of_rows-1)*pitch - (pad_size[1] - pad_size[0])/2

        if dy < (pad_size[1]/2 + silk_pad_off):
            dx = sqrt((pad_size[0]/2 + silk_pad_off)**2-dy**2)
        else:
            dx = 0

        dx_rect = pad_size[0]/2 + silk_pad_off

        left_silk_pad = -dx_rect
        right_silk_pad = (first_to_last_pad_x + dx) if pins_per_row > 1 else dx_rect

        silk_poly = [
            # Top left next to pad
            {'x': left_silk_pad, 'y': body_edge['top']-silk_fab_offset},
            # Top left corner
            {'x': body_edge['left'] - silk_fab_offset, 'y': body_edge['top'] - silk_fab_offset},
            # Bottom left corner
            {'x': body_edge['left'] - silk_fab_offset, 'y': body_edge['bottom'] + silk_fab_offset},
            # Bottom right corner
            {'x': body_edge['right'] + silk_fab_offset, 'y': body_edge['bottom'] + silk_fab_offset},
            # Top right corner
            {'x': body_edge['right'] + silk_fab_offset, 'y': body_edge['top'] - silk_fab_offset},
            # Top right next to pad
            {'x': right_silk_pad, 'y': body_edge['top'] - silk_fab_offset},
        ]
    else:
        dx = body_edge['left'] - silk_fab_offset - (number_of_rows - 1) * pitch - (pad_size[0] - pad_size[1]) / 2

        if dx < (pad_size[1] / 2 + silk_pad_off):
            dy = sqrt((pad_size[1] / 2 + silk_pad_off)**2 - dx**2)
        else:
            dy = 0

        dy_rect = pad_size[1] / 2 + silk_pad_off
        top_silk_pad = -dy
        bottom_silk_pad = (first_to_last_pad_y + dy) if pins_per_row > 1 else dy_rect

        silk_poly = [
            {'x': body_edge['left'] - silk_fab_offset,'y': top_silk_pad},
            {'x': body_edge['left'] - silk_fab_offset,'y': body_edge['top'] - silk_fab_offset},
            {'x': body_edge['right'] + silk_fab_offset,'y': body_edge['top'] - silk_fab_offset},
            {'x': body_edge['right'] + silk_fab_offset,'y': body_edge['bottom'] + silk_fab_offset},
            {'x': body_edge['left'] - silk_fab_offset,'y': body_edge['bottom'] + silk_fab_offset},
            {'x': body_edge['left'] - silk_fab_offset,'y': bottom_silk_pad},
        ]

    kicad_mod.append(PolygonLine(shape=silk_poly,
                                layer='F.SilkS', width=configuration['silk_line_width']))

    # Draw lines across top, between pads
    for i in range(pins_per_row-1):
        if number_of_rows==1:
            line_start_x = i * pitch + (dx if i > 1 else dx_rect)
            line_end_x = (i + 1) * pitch - dx
            line_y = body_edge['top'] - silk_fab_offset
            line_start = [line_start_x, line_y]
            line_end = [line_end_x, line_y]
        else: # 2 rows
            line_start_y = i * pitch + dy
            line_end_y = (i + 1) * pitch - dy
            line_x = body_edge['left'] - silk_fab_offset
            line_start = [line_x, line_start_y]
            line_end = [line_x, line_end_y]
        kicad_mod.append(Line(
            start=line_start,
            end=line_end,
            layer='F.SilkS',
            width=configuration['silk_line_width'],
        ))

    # Draw L shaped polarization marker
    O = silk_pad_off + 0.2

    pin = [
        {'x': 0,'y': -pad_size[1]/2 - O},
        {'x': -pad_size[0]/2 - O,'y': -pad_size[1]/2 - O},
        {'x': -pad_size[0]/2 - O,'y': 0},
    ]

    kicad_mod.append(PolygonLine(shape=pin,
                                 layer="F.SilkS", width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=pin,
                                 width=configuration['fab_line_width'], layer='F.Fab'))

    ########################### CrtYd #################################
    CrtYd_offset = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']

    cx1 = round_to_grid(bounding_box['left'] - CrtYd_offset, CrtYd_grid)
    cy1 = round_to_grid(bounding_box['top'] - CrtYd_offset, CrtYd_grid)

    cx2 = round_to_grid(bounding_box['right'] + CrtYd_offset, CrtYd_grid)
    cy2 = round_to_grid(bounding_box['bottom'] + CrtYd_offset, CrtYd_grid)

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    addTextFields(
        kicad_mod=kicad_mod,
        configuration=configuration,
        body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2},
        fp_name=footprint_name,
        text_y_inside_position='bottom' if number_of_rows==1 else 'right',
    )

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    lib_name = configuration['lib_name_format_string'].format(series=series, man=man_lib)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_generated_fps = 0
    for variant in variant_params:
        variant_param = variant_params[variant]
        for pins_per_row in variant_param['pins_per_row_range']:
            generate_one_footprint(generator_name, global_config, pins_per_row, variant_param, configuration)
            num_generated_fps += 1
    return num_generated_fps
