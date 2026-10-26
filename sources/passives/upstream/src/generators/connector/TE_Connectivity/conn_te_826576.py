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
from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


draw_inner_details = False

series = "826576"
manufacturer = 'TE'
manufacturer_lib = 'TE-Connectivity'
orientation = 'V'
datasheet = 'https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=826576&DocType=Customer+Drawing&DocLang=English'
number_of_rows = 1

# only generate active pin counts from TE rev 7 datasheet
#pins_per_row_range = range(1, 37)
pins_per_row_range = [2,3,5,6,7,8,9,13,15,16,17,18,20,36]

# the datasheet has an equation and a table (column 'L') for body length
# the equation of pincount * 3.96 = length is wrong
# the table is roughly correct based on part measurement
# table is nearly pincount * 3.96 - 0.589 but capture the table exactly
body_lengths = {1:3.3, 2:7.3, 3:11.3, 4:15.2, 5:19.2, 6:23.1, 7:27.1, 8:31.1, 9:35.1, 10:39,
                11:43, 12:46.9, 13:50.9, 14:54.8, 15:58.8, 16:62.8, 17:66.7, 18:70.7, 19:74.7, 20:78.6,
                21:82.6, 22:86.5, 23:90.5, 24:94.4, 25:98.4, 26:102.4, 27:106.3, 28:110.3, 29:114.2, 30:118.2,
                31:122.2, 32:126.1, 33:130.1, 34:134, 35:138, 36:141.6}

part_code = "{:s}{:s}826576-{:s}"

pitch = 3.96
drill = 1.4
start_pos_x = 0 # Where should pin 1 be located?
pad_size = [drill + 1, drill + 1]

pad_shape=Pad.SHAPE_OVAL
if pad_size[1] == pad_size[0]:
    pad_shape=Pad.SHAPE_CIRCLE


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, configuration):
    mpn = part_code.format(str(pins)[:1] if pins > 9 else '', '-' if pins > 9 else '', str(pins)[-1])

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_no_series_format_string'].format(man=manufacturer,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("{:s}, {:s}, {:d} Pins ({:s})".format(manufacturer,
        mpn, pins, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    #calculate fp dimensions

    #B = distance between end-point pins
    B = (pins - 1) * pitch
    #A = total connector length
    A = body_lengths[pins]

    #corners
    x1 = -(A-B) / 2
    x2 = x1 + A

    body_width = 6.4
    y2 = body_width / 2
    y1 = y2 - body_width

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = body_edge.copy()

    out = [
    {'x': B/2, 'y': y1},
    {'x': x1, 'y': y1},
    {'x': x1, 'y': y2},
    {'x': B/2, 'y': y2},
    ]
    kicad_mod.append(PolygonLine(shape=out,
                                 layer="F.Fab", width=configuration['fab_line_width']))
    kicad_mod.append(PolygonLine(shape=out, x_mirror=B / 2,
                                 layer="F.Fab", width=configuration['fab_line_width']))

    #offset
    o = configuration['silk_fab_offset']
    x1 -= o
    y1 -= o
    x2 += o
    y2 += o

    out = [
    {'x': B/2, 'y': y1},
    {'x': x1, 'y': y1},
    {'x': x1, 'y': y2},
    {'x': B/2, 'y': y2},
    ]
    kicad_mod.append(PolygonLine(shape=out,
                                 layer="F.SilkS", width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=out, x_mirror=B / 2,
                                 layer="F.SilkS", width=configuration['silk_line_width']))

    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    #generate the pads
    kicad_mod.append(PadArray(
        pincount=pins, x_spacing=pitch, type=Pad.TYPE_THT,
        shape=pad_shape, size=pad_size, drill=drill, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler,
        **optional_pad_params))

    #pin-1 marker
    pin_mark_width = 1
    pin_mark_height = 1
    pin_mask_offset = 0.5

    pin = [
        {'x': -pin_mark_width/2,'y': body_edge['bottom']},
        {'x': 0,'y': body_edge['bottom'] - pin_mark_height},
        {'x': pin_mark_width/2,'y': body_edge['bottom']},
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 layer="F.Fab", width=configuration['fab_line_width']))

    pin = [
        {'x': -pin_mark_width/2,'y': body_edge['bottom'] + pin_mark_height + pin_mask_offset},
        {'x': 0,'y': body_edge['bottom'] + pin_mask_offset},
        {'x': pin_mark_width/2,'y': body_edge['bottom'] + pin_mark_height + pin_mask_offset},
        {'x': -pin_mark_width/2,'y': body_edge['bottom'] + pin_mark_height + pin_mask_offset}
    ]

    kicad_mod.append(PolygonLine(shape=pin,
                                 layer="F.SilkS", width=configuration['silk_line_width']))


    ########################### CrtYd #################################
    cx1 = round_to_grid(bounding_box['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(bounding_box['top']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(bounding_box['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(bounding_box['bottom'] + configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='top')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer_lib)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    for pins_per_row in pins_per_row_range:
        generate_one_footprint(generator_name, global_config, pins_per_row, configuration)
    return len(pins_per_row_range)
