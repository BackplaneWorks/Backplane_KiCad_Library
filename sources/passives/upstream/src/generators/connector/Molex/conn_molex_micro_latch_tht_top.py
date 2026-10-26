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


series = "Micro-Latch"
series_long = 'Micro-Latch Wire-to-Board Connector System'
manufacturer = 'Molex'
orientation = 'V'
number_of_rows = 1
datasheet = 'http://www.molex.com/pdm_docs/sd/532530770_sd.pdf'

#pins_per_row per row
pins_per_row_range = range(2,16)

#Molex part number
#n = number of circuits per row
part_code = "53253-{n:02d}70"

alternative_codes = [
"53253-{n:02d}50"
]

pitch = 2
drill = 0.8
start_pos_x = 0 # Where should pin 1 be located.
pad_to_pad_clearance = 0.8
max_annular_ring = 0.5
min_annular_ring = 0.15



pad_size = [pitch - pad_to_pad_clearance, drill + 2*max_annular_ring]
if pad_size[0] - drill < 2*min_annular_ring:
    pad_size[0] = drill + 2*min_annular_ring
if pad_size[0] - drill > 2*max_annular_ring:
    pad_size[0] = drill + 2*max_annular_ring

pad_shape=Pad.SHAPE_OVAL
if pad_size[1] == pad_size[0]:
    pad_shape=Pad.SHAPE_CIRCLE



def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins_per_row, configuration):
    mpn = part_code.format(n=pins_per_row*number_of_rows)
    alt_mpn = [code.format(n=pins_per_row*number_of_rows) for code in alternative_codes]

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("Molex {:s}, {:s} (compatible alternatives: {:s}), {:d} Pins per row ({:s})".format(series_long, mpn, ', '.join(alt_mpn), pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    #calculate fp dimensions
    A = (pins_per_row - 1) * pitch
    B = A + 3.1
    C = A + 4

    #connector thickness
    T = 5.75

    #corners
    x1 = -2
    x2 = x1 + C

    T = 3.65

    y1 = -1.5
    y2 = y1 + T

    off = configuration['silk_fab_offset']
    pad_silk_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = body_edge.copy()

    #add simple outline to F.Fab layer
    kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2],layer='F.Fab', width=configuration['fab_line_width']))

    #wall-thickness W
    w = 0.4

    #offset
    o = configuration['silk_fab_offset']
    x1 -= o
    y1 -= o
    x2 += o
    y2 += o

    #generate the pads
    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(PadArray(
        pincount=pins_per_row, x_spacing=pitch, type=Pad.TYPE_THT,
        shape=pad_shape, size=pad_size, drill=drill, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler,
        **optional_pad_params))

    #draw the courtyard

    #draw the connector outline
    out = Rectangle(start=[x1,y1], end=[x2,y2],
        width=configuration['silk_line_width'], layer="F.SilkS")
    kicad_mod.append(out)

    #pin-1 marker
    y =  -2
    m = 0.3

    O = 0.3
    L = 2
    pin = [
        {'x': x1 + L, 'y': y1 - O},
        {'x': x1 - O, 'y': y1 - O},
        {'x': x1 - O, 'y': y1 + L},
        ]

    kicad_mod.append(PolygonLine(shape=pin,
                                 width=configuration['silk_line_width'], layer="F.SilkS"))

    p1m_sl = 1
    pin =[
        {'x': -p1m_sl/2, 'y': body_edge['top']},
        {'x': 0, 'y': body_edge['top'] + p1m_sl/sqrt(2)},
        {'x': p1m_sl/2, 'y': body_edge['top']}
    ]
    kicad_mod.append(PolygonLine(shape=pin, width=configuration['fab_line_width'], layer='F.Fab'))

    kicad_mod.append(Line(start=[x1,2*w],end=[x1+w,2*w],
        width=configuration['silk_line_width'], layer="F.SilkS"))
    kicad_mod.append(Line(start=[x2,2*w],end=[x2-w,2*w],
        width=configuration['silk_line_width'], layer="F.SilkS"))

    #add the 'wall'
    wall = [
    {'x': A/2,'y': y1+w},
    {'x': x1+w,'y': y1+w},
    {'x': x1+w,'y': 0},
    {'x': x1+2*w,'y': 0},
    {'x': x1+2*w,'y': w},
    {'x': x1+w,'y': w},
    {'x': x1+w,'y': y2},
    ]

    kicad_mod.append(PolygonLine(shape=wall,
                                 width=configuration['silk_line_width'], layer="F.SilkS"))
    kicad_mod.append(PolygonLine(shape=wall, x_mirror=A / 2,
                                 width=configuration['silk_line_width'], layer="F.SilkS"))

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
    pins_per_row_range = range(2, 16)
    for pins_per_row in pins_per_row_range:
        generate_one_footprint(generator_name, global_config, pins_per_row, configuration)
        num_fps_generated += 1
    return num_fps_generated
