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

from math import sqrt
from typing import Any
from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.footprint_keepout_area import addRectangularKeepout
from kilibs.config import global_config as GC
from generators.tools.footprint.save_footprint import write_footprint


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, idx, pins, configuration):
    series = 'DF13C'
    series_long = 'DF13C SMD'
    manufacturer = 'Hirose'
    orientation = 'V'
    number_of_rows = 1
    datasheet = 'https://www.hirose.com/product/en/products/DF13/DF13C-10P-1.25V%2851%29/'

    mpn_param_1 = ['2','5','8','0','3','6','9','1','4','3','6','1','4']

    part_code = "CL535-04{n:02d}-{param_1:s}-51"

    # x position mounting inner mounting pad edge relative to nearest pad center
    center_pad_to_mounting_pad_edge = 1.45
    # y dimensions for pad given relative to mounting pad edge
    rel_pad_y_outside_edge = 4.7
    rel_pad_y_inside_edge = 2.9
    pad_size_x = 0.7
    # y position for body edge relative to mounting pad edge (positive -> body extends outside bounding box)
    rel_body_edge_y = 0.6
    body_size_y = 3.4
    # body_fin_protrusion: 1.6
    # body_fin_width: 0.8
    # x body edge relative to nearest pin
    rel_body_edge_x = 2.2

    pitch = 1.25
    pad_size = [pad_size_x, rel_pad_y_outside_edge - rel_pad_y_inside_edge]
    mp_size = [1.6, 2.2]

    mpn = part_code.format(n=pins, param_1=mpn_param_1[idx])
    pad_silk_off = configuration['silk_line_width']/2 + configuration['silk_pad_clearance']
    off = configuration['silk_fab_offset']
    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "-1MP",
        pitch=pitch, orientation=orientation_str)

    footprint_name = footprint_name.replace("__",'_')

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription("{:s} {:s}, {:s}, {:d} Pins per row ({:s})".format(manufacturer, series_long, mpn, pins, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    A = (pins - 1) * pitch
    B = A + 2*rel_body_edge_x
    pad_y = -rel_pad_y_outside_edge/2 + pad_size[1]/2
    mpad_y = rel_pad_y_outside_edge/2 - mp_size[1]/2
    mpad_x = A/2 + center_pad_to_mounting_pad_edge + mp_size[0]/2

    mounting_pad_name = global_config.get_pad_name(GC.PadName.MECHANICAL)
    kicad_mod.append(Pad(number=mounting_pad_name, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                        at=[mpad_x, mpad_y], size=mp_size, layers=Pad.LAYERS_SMT))
    kicad_mod.append(Pad(number=mounting_pad_name, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT,
                        at=[-mpad_x, mpad_y], size=mp_size, layers=Pad.LAYERS_SMT))

    # create pads
    #createNumberedPadsTHT(kicad_mod, pincount, pitch, drill, {'x':x_dia, 'y':y_dia})
    kicad_mod.append(PadArray(center=[0,pad_y], pincount=pins, x_spacing=pitch,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, size=pad_size, layers=Pad.LAYERS_SMT))


    x1 = -B/2
    x2 = x1 + B
    y2 = mpad_y + mp_size[1]/2 + rel_body_edge_y
    y1 = y2 - body_size_y

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }

    bounding_box = body_edge.copy()
    bounding_box['top'] = pad_y - pad_size[1]/2
    bb_x = mpad_x + mp_size[0]/2
    if  bb_x > x2:
        bounding_box['left'] = -bb_x
        bounding_box['right'] = bb_x


    kicad_mod.append(Rectangle(
        start={'x': x1,'y': y1}, end={'x': x2,'y': y2},
        layer='F.Fab', width=configuration['fab_line_width']))

    #line offset
    off = 0.1

    x1 -= off
    y1 -= off

    x2 += off
    y2 += off

    #draw the main outline around the footprint
    silk_pad_x_left = -A/2 - pad_size[0]/2 - pad_silk_off
    silk_mp_top = mpad_y - mp_size[1]/2 - pad_silk_off
    silk_mp_bottom = mpad_y + mp_size[1]/2 + pad_silk_off
    kicad_mod.append(PolygonLine(
        shape=[
            {'x': silk_pad_x_left,'y':y1},
            {'x': x1,'y':y1},
            {'x': x1,'y':silk_mp_top}
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygonLine(
        shape=[
            {'x': -silk_pad_x_left,'y':y1},
            {'x': x2,'y':y1},
            {'x': x2,'y':silk_mp_top}
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))

    kicad_mod.append(PolygonLine(
        shape=[
            {'x': x1,'y':silk_mp_bottom},
            {'x': x1,'y':y2},
            {'x': x2,'y':y2},
            {'x': x2,'y':silk_mp_bottom}
        ],
        layer='F.SilkS', width=configuration['silk_line_width']))


    #add pin-1 marker

    kicad_mod.append(Line(
        start=[silk_pad_x_left, y1], end=[silk_pad_x_left, pad_y - pad_size[1]/2],
                layer='F.SilkS', width=configuration['silk_line_width']))

    sl=1
    pin = [
        {'y': body_edge['top'], 'x': -A/2-sl/2},
        {'y': body_edge['top'] + sl/sqrt(2), 'x': -A/2},
        {'y': body_edge['top'], 'x': -A/2+sl/2}
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 width=configuration['fab_line_width'], layer='F.Fab'))


    ########################### KEEPOUT #################################

    k_top = pad_y + pad_size[1]/2 + 0.1
    k_size = [A + pad_size[0], 2.37]
    addRectangularKeepout(kicad_mod, [0, k_top+k_size[1]/2], k_size)


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
    pins_per_row_range = [2,3,4,5,6,7,8,9,10,11,12,14,15]
    idx = 0
    for pins_per_row in pins_per_row_range:
        generate_one_footprint(generator_name, global_config, idx, pins_per_row, configuration)
        idx += 1
        num_fps_generated += 1
    return num_fps_generated
