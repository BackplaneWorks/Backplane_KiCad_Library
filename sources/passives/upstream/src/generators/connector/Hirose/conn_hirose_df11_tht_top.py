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
from kilibs.config import global_config as GC
from generators.tools.footprint.save_footprint import write_footprint



def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, configuration):
    series = 'DF11'
    series_long = 'DF11 through hole'
    manufacturer = 'Hirose'
    orientation = 'V'
    number_of_rows = 2
    datasheet = 'https://www.hirose.com/product/document?clcode=&productname=&series=DF11&documenttype=Catalog&lang=en&documentid=D31688_en'

    # Part number
    # n = number of circuits total
    part_code = "DF11-{n}DP-2DSA"

    pitch = 2
    drill = 0.85

    pad_to_pad_clearance = 0.8
    max_annular_ring = 0.4
    min_annular_ring = 0.15

    pad_size = [pitch - pad_to_pad_clearance, drill + 2*max_annular_ring]
    if pad_size[0] - drill < 2*min_annular_ring:
        pad_size[0] = drill + 2*min_annular_ring
    if pad_size[0] - drill > 2*max_annular_ring:
        pad_size[0] = drill + 2*max_annular_ring

    pad_shape=Pad.SHAPE_OVAL
    if pad_size[1] == pad_size[0]:
        pad_shape=Pad.SHAPE_CIRCLE

    mpn = part_code.format(n=pins*2)
    pad_silk_off = configuration['silk_line_width']/2 + configuration['silk_pad_clearance']
    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_no_series_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    footprint_name = footprint_name.replace("__",'_')

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("{:s} {:s}, {:s}, {:d} Pins per row ({:s})".format(manufacturer, series_long, mpn, pins, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    A = (pins - 1) * pitch
    B = A + 4

    # create pads
    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    for initial, initial_y in zip([1, 2], [0, pitch]):
        kicad_mod.append(PadArray(start=[0, initial_y], initial=initial, increment=2, pincount=pins, x_spacing=pitch,
            type=Pad.TYPE_THT, shape=pad_shape, size=pad_size,
            drill=drill, layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params))

    x1 = -(B-A) / 2
    y1 = -1.5
    x2 = x1 + B
    y2 = 1.5 + pitch

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = body_edge.copy()

    # Fab
    kicad_mod.append(Rectangle(
        start={'x': x1,'y': y1}, end={'x': x2,'y': y2},
        layer='F.Fab', width=configuration['fab_line_width']))
    sl=1
    pin = [
        {'y': body_edge['top'], 'x': -sl/2},
        {'y': body_edge['top'] + sl/sqrt(2), 'x': 0},
        {'y': body_edge['top'], 'x': sl/2}
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 width=configuration['fab_line_width'], layer='F.Fab'))

    #line offset
    off = 0.1

    x1 -= off
    y1 -= off

    x2 += off
    y2 += off

    #draw the main outline around the footprint
    kicad_mod.append(Rectangle(start={'x':x1,'y':y1},end={'x':x2,'y':y2},
        layer='F.SilkS', width=configuration['silk_line_width']))

    #add pin-1 marker
    p1_off = configuration['silk_fab_offset'] + 0.3
    L = 1.5
    pin = [
        {'y': body_edge['top'] + L, 'x': body_edge['left'] - p1_off},
        {'y': body_edge['top'] - p1_off, 'x': body_edge['left'] - p1_off},
        {'y': body_edge['top'] - p1_off, 'x': body_edge['left'] + L}
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 layer='F.SilkS', width=configuration['silk_line_width']))

    #side-wall thickness S
    S = 0.4

    #bottom line
    kicad_mod.append(PolygonLine(
        shape=[
            {'x':x1,'y':2},
            {'x':x1+S,'y':2},
            {'x':x1+S,'y':y2-S},
            {'x':x2-S,'y':y2-S},
            {'x':x2-S,'y':2},
            {'x':x2,'y':2}],
        layer='F.SilkS', width=configuration['silk_line_width']))

    #left mark
    kicad_mod.append(PolygonLine(
        shape=[
            {'x':x1,'y':1},
            {'x':x1+S,'y':1},
            {'x':x1+S,'y':y1+S},
            {'x':0.5,'y':y1+S},
            {'x':0.5,'y':y1}],
        layer='F.SilkS', width=configuration['silk_line_width']))

    #right mark
    kicad_mod.append(PolygonLine(
        shape=[
            {'x':x2,'y':1},
            {'x':x2-S,'y':1},
            {'x':x2-S,'y':y1+S},
            {'x':x2-2.5-off,'y':y1+S},
            {'x':x2-2.5-off,'y':y1}],
        layer='F.SilkS', width=configuration['silk_line_width']))

    #middle line
    if pins > 2:
        kicad_mod.append(PolygonLine(
            shape=[
                {'x':1.5,'y':y1},
                {'x':1.5,'y':y1+S},
                {'x':x2-3.5-off,'y':y1+S},
                {'x':x2-3.5-off,'y':y1}],
            layer='F.SilkS', width=configuration['silk_line_width']))

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
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='bottom')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))
    
    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    pins_per_row_range = range(2,17)
    for pins_per_row in pins_per_row_range:
        generate_one_footprint(generator_name, global_config, pins_per_row, configuration)
        num_fps_generated += 1
    return num_fps_generated
