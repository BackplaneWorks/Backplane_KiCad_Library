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
from kilibs.config import global_config as GC
from generators.tools.footprint.save_footprint import write_footprint


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, idx, pins, configuration):
    series = 'DF12'
    series_long = 'DF12E SMD'
    manufacturer = 'Hirose'
    orientation = 'V'
    number_of_rows = 2
    datasheet = 'https://www.hirose.com/product/document?clcode=CL0537-0834-6-81&productname=DF12E(3.0)-50DP-0.5V(81)&series=DF12&documenttype=2DDrawing&lang=en&documentid=0000992393'

    #Hirose part number
    part_code = "DF12E3.0-{n:02}DP-0.5V"

    pitch = 0.5
    pad_size = [0.3, 1.6]
    pad_size_paste = [0.28,1.2]

    mpn = part_code.format(n=pins)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=int(pins/2), mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription("{:s} {:s}, {:s}, {:d} Pins per row ({:s})".format(manufacturer, series_long, mpn, pins, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    ########################## Dimensions ##############################
    if(idx == 6):       #80 Pins
        A = 22.2
        B = 19.5
    elif(idx == 7):     #14 Pins
        A = 5.7
        B = 3.0
    elif (idx == 8):    #32 Pins
        A = 10.2
        B = 7.5
    elif (idx == 9):    #36 Pins
        A = 11.2
        B = 8.5
    else:
        A = 4.7 + (idx * 2.5)
        B = A - 2.7

    body_edge_out={
        'left': round(-A/2 ,2),
        'right': round(A/2 ,2),
        'top': -1.9,
        'bottom': 1.9
        }

    D = A - 1.5

    body_edge_in={
        'left': round(-D/2 ,2),
        'right': round(D/2 ,2),
        'top': -1.225,
        'bottom': 1.225
        }

    ############################# Pads ##################################
    #
    # Add pads
    #
    #Pad only with F.Cu and F.Mask
    CPins=int(pins / 2)
    kicad_mod.append(PadArray(start=[-B/2, 1.8], initial=1,
        pincount=CPins, increment=1,  x_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=["F.Cu", "F.Mask"]))

    kicad_mod.append(PadArray(start=[-B/2, -1.8], initial=CPins + 1,
        pincount=CPins, increment=1,  x_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=["F.Cu", "F.Mask"]))

    #F.Paste
    kicad_mod.append(PadArray(start=[-B/2, 2], initial='', increment=0,
        pincount=CPins,  x_spacing=pitch, size=pad_size_paste,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=["F.Paste"]))

    kicad_mod.append(PadArray(start=[-B/2, -2], initial='', increment=0,
        pincount=CPins,  x_spacing=pitch, size=pad_size_paste,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=["F.Paste"]))

    ######################## Fabrication Layer ###########################
    main_body_out_poly= [
        {'x': body_edge_out['left'], 'y': body_edge_out['bottom']},
        {'x': body_edge_out['left'], 'y': body_edge_out['top']},
        {'x': body_edge_out['right'], 'y': body_edge_out['top']},
        {'x': body_edge_out['right'], 'y': body_edge_out['bottom']},
        {'x': body_edge_out['left'], 'y': body_edge_out['bottom']}
    ]
    kicad_mod.append(PolygonLine(shape=main_body_out_poly,
                                 width=configuration['fab_line_width'], layer="F.Fab"))

    main_body_in_poly= [
        {'x': body_edge_in['left'], 'y': body_edge_in['bottom']},
        {'x': body_edge_in['left'], 'y': body_edge_in['top']},
        {'x': body_edge_in['right'], 'y': body_edge_in['top']},
        {'x': body_edge_in['right'], 'y': body_edge_in['bottom']},
        {'x': body_edge_in['left'], 'y': body_edge_in['bottom']}
    ]
    kicad_mod.append(PolygonLine(shape=main_body_in_poly,
                                 width=configuration['fab_line_width'], layer="F.Fab"))

    main_arrow_poly= [
        {'x': (-B/2)-0.2, 'y': body_edge_out['bottom'] + 0.75},
        {'x': -B/2, 'y': 1.8},
        {'x': (-B/2)+0.2, 'y': body_edge_out['bottom'] + 0.75},
        {'x': (-B/2)-0.2, 'y': body_edge_out['bottom'] + 0.75}
    ]
    kicad_mod.append(PolygonLine(shape=main_arrow_poly,
                                 width=configuration['fab_line_width'], layer="F.Fab"))

    ######################## SilkS Layer ###########################
    offset = (pad_size[0]/2)+0.2+.06

    poly_left= [
        {'x': -(B/2) - offset, 'y': body_edge_out['bottom'] + (pad_size[1]/3)},
        {'x': -(B/2) - offset, 'y': body_edge_out['bottom'] + configuration['silk_fab_offset']},
        {'x': -(A/2) - configuration['silk_fab_offset'], 'y': body_edge_out['bottom'] + configuration['silk_fab_offset']},
        {'x': body_edge_out['left'] - configuration['silk_fab_offset'], 'y': body_edge_out['top'] - configuration['silk_fab_offset']},
        {'x': -(B/2) - offset, 'y': body_edge_out['top'] - configuration['silk_fab_offset']}
    ]

    kicad_mod.append(PolygonLine(shape=poly_left,
                                 width=configuration['silk_line_width'], layer="F.SilkS"))

    poly_right= [
        {'x': (B/2) + offset, 'y': body_edge_out['bottom'] + configuration['silk_fab_offset']},
        {'x': (A/2) + configuration['silk_fab_offset'], 'y': body_edge_out['bottom'] + configuration['silk_fab_offset']},
        {'x': body_edge_out['right'] + configuration['silk_fab_offset'], 'y': body_edge_out['top'] - configuration['silk_fab_offset']},
        {'x': (B/2) + offset, 'y': body_edge_out['top'] - configuration['silk_fab_offset']}
    ]

    kicad_mod.append(PolygonLine(shape=poly_right,
                                 width=configuration['silk_line_width'], layer="F.SilkS"))

    ######################## CrtYd Layer ###########################
    CrtYd_offset = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']

    poly_yd = [
        {'x': round_to_grid(body_edge_out['left'] - CrtYd_offset, CrtYd_grid), 'y': round_to_grid(-2.6 - CrtYd_offset, CrtYd_grid)},
        {'x': round_to_grid(body_edge_out['left'] - CrtYd_offset, CrtYd_grid), 'y': round_to_grid(2.6 + CrtYd_offset, CrtYd_grid)},
        {'x': round_to_grid(body_edge_out['right'] + CrtYd_offset, CrtYd_grid), 'y': round_to_grid(2.6 + CrtYd_offset, CrtYd_grid)},
        {'x': round_to_grid(body_edge_out['right'] + CrtYd_offset, CrtYd_grid), 'y': round_to_grid(-2.6 - CrtYd_offset, CrtYd_grid)},
        {'x': round_to_grid(body_edge_out['left'] - CrtYd_offset, CrtYd_grid), 'y': round_to_grid(-2.6 - CrtYd_offset, CrtYd_grid)}
    ]

    kicad_mod.append(PolygonLine(shape=poly_yd,
                                 layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    cy1 = round_to_grid(body_edge_out['top'] -1 - configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(body_edge_out['bottom'] + 1 + configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge_out,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='top')

    ##################### Write to File and 3D ############################
    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    #pins_per_row per row
    pins_per_row_range = [10,20,30,40,50,60,80,14,32,36]
    idx = 0
    for pincount in pins_per_row_range:
        generate_one_footprint(generator_name, global_config, idx, pincount, configuration)
        idx += 1
    return idx
