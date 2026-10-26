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


def make_module(generator_name: str, global_config: GC.GlobalConfig, pin_count, configuration):

    series = ""
    series_long = 'JAE 0.2mm pitch, 1mm overall height FFC/FPC connector'
    manufacturer = 'JAE'
    orientation = 'H'
    number_of_rows = 2
    datasheet='http://www.jae.com/z-en/pdf_download_exec.cfm?param=SJ108178.pdf'

    conn_category = "FFC-FPC"

    lib_by_conn_category = True

    part_code = "FF08{:02d}SA1"

    # def get_name(pin_count):
    #     return 'Molex-502250-{0}91_2Rows-{0}Pins_P0.3mm_Horizontal'.format(pin_count)

    cable_pitch = 0.2
    odd_pad_size = (0.55, 0.18) # bottom
    even_pad_size = (0.7, 0.18) # top
    pad_silk_off = configuration['silk_line_width']/2 + configuration['silk_pad_clearance']
    off = configuration['silk_fab_offset']

    mpn = part_code.format(pin_count)

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_unequal_row_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins=pin_count, mounting_pad = "",
        pitch=cable_pitch*2, orientation=orientation_str)

    footprint_name = footprint_name.replace("__",'_')

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription("Molex {:s}, {:s}, {:d} Circuits ({:s})".format(series_long, mpn, pin_count, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    pad_to_pad_inside = 2
    pad_to_pad_outside = pad_to_pad_inside + odd_pad_size[0] + even_pad_size[0]
    row_spacing = pad_to_pad_outside - odd_pad_size[0]/2 - even_pad_size[0]/2

    odd_pad_x = -pad_to_pad_outside/2 + odd_pad_size[0]/2
    even_pad_x = odd_pad_x + row_spacing


    B = cable_pitch * (pin_count - 1)

    A = B + (7.05-4.8)
    bar_width_max = 2*3.8
    bar_chamfer_y = 1
    bar_from_side_min = 0.1

    bar_width = A - 2*bar_from_side_min
    if bar_width > bar_width_max:
        bar_width = bar_width_max

    body_edge = {
        'top': -A/2,
        'bottom': A/2,
        'left': odd_pad_x - odd_pad_size[0]/2 + 0.35
    }
    body_edge['right'] = body_edge['left'] + 2.85

    bar_down_edge = body_edge['left'] + 3.23


    bounding_box = {
        'top': body_edge['top'],
        'bottom': body_edge['bottom'],
        'left': odd_pad_x - odd_pad_size[0]/2,
        'right': bar_down_edge
    }

    kicad_mod.append(Rectangle(
        start=[body_edge['left'], body_edge['top']],
        end=[body_edge['right'], body_edge['bottom']],
        layer="F.Fab", width=configuration['fab_line_width']
    ))
    kicad_mod.append(PolygonLine(
        shape=[
            {'x': body_edge['right'], 'y': -bar_width/2},
            {'x': bar_down_edge, 'y': -bar_width/2 + bar_chamfer_y},
            {'x': bar_down_edge, 'y': bar_width/2 - bar_chamfer_y},
            {'x': body_edge['right'], 'y': bar_width/2}
        ],
        layer="F.Fab", width=configuration['fab_line_width']
    ))

    odd_pins_outside = B/2 + odd_pad_size[1]/2 + pad_silk_off
    silk_outline = [
        {'x': body_edge['left']-off, 'y':odd_pins_outside},
        {'x': body_edge['left']-off, 'y':body_edge['bottom']+off},
        {'x': body_edge['right'] + off, 'y':body_edge['bottom']+off},
        {'x': body_edge['right'] + off, 'y': bar_width/2 + off},
        {'x': bar_down_edge + off, 'y': bar_width/2 - bar_chamfer_y + off},
        {'x': bar_down_edge + off, 'y': 0}
    ]
    kicad_mod.append(PolygonLine(
        shape=silk_outline,
        layer="F.SilkS", width=configuration['silk_line_width']
    ))
    kicad_mod.append(PolygonLine(
        shape=silk_outline, y_mirror=0,
        layer="F.SilkS", width=configuration['silk_line_width']
    ))

    even_pins = pin_count//2
    odd_pins = pin_count - even_pins
    kicad_mod.append(PadArray(
            center=[odd_pad_x,0], pincount=odd_pins,
            initial=1, increment=2, y_spacing=2*cable_pitch,
            type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
            size=odd_pad_size, layers=Pad.LAYERS_SMT))
    kicad_mod.append(PadArray(
            center=[even_pad_x, 0], pincount=even_pins,
            initial=2, increment=2, y_spacing=2*cable_pitch,
            type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
            size=even_pad_size, layers=Pad.LAYERS_SMT))

    pin1_y = -B/2
    ps1_m = 0.3
    p1s_x = bounding_box['left'] - pad_silk_off
    pin = [
        {'x': p1s_x -  ps1_m/sqrt(2), 'y': pin1_y-ps1_m/2},
        {'x': p1s_x, 'y': pin1_y},
        {'x': p1s_x -  ps1_m/sqrt(2), 'y': pin1_y+ps1_m/2},
        {'x': p1s_x -  ps1_m/sqrt(2), 'y': pin1_y-ps1_m/2}
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 layer="F.SilkS", width=configuration['silk_line_width']))

    sl=0.6
    pin = [
        {'x': body_edge['left'], 'y': pin1_y-sl/2},
        {'x': body_edge['left'] + sl/sqrt(2), 'y': pin1_y},
        {'x': body_edge['left'], 'y': pin1_y+sl/2}
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 width=configuration['fab_line_width'], layer='F.Fab'))

    ########################### CrtYd #################################
    cx1 = round_to_grid(bounding_box['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(bounding_box['top']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(bounding_box['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(bounding_box['bottom']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='right')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    if lib_by_conn_category:
        lib_name = configuration['lib_name_specific_function_format_string'].format(category=conn_category)
    else:
        lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)

    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))
    
    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    pinrange = [25, 29, 41, 51, 71, 81]
    for pincount in pinrange:
        make_module(generator_name, global_config, pincount, configuration)
        num_fps_generated += 1
    return num_fps_generated
