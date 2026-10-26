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

series = "XH"
manufacturer = 'JST'
orientation = 'H'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/eXH.pdf'


pitch = 2.50
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5 #How much copper should be in y direction?
min_annular_ring = 0.15

#FP name strings
part_base = "S{n}B-XH-{variant:s}" #JST part number format string

fab_pin1_marker_type = 2
fab_first_marker_w = 1.25
fab_first_marker_h = 1

#FP description and tags

variant_params = {
    'A':{
        'V': 9.2,
        'pin_range': range(2,17)
        },
    'A-1':{
        'V': 7.6,
        'pin_range': range(2,16)
        }
    }

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, variant, configuration):
    V=variant_params[variant]['V']
    #calculate fp dimensions
    A = (pins - 1) * pitch
    B = A + 4.9

    #Thickness of connector
    T = 11.5

    #corners
    x1 = -2.45
    x2 = x1 + B

    x_mid = (x1 + x2) / 2

    y2 = V
    y1= y2 - T


    #y at which the plastic tabs end
    y3 = y2 - 7

    #generate the name
    mpn = part_base.format(n=pins, variant=variant)
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("JST {:s} series connector, {:s} ({:s})".format(series, mpn, datasheet))

    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))


    if pins == 2:
        drill = 1.0
    else:
        drill = 0.95

    pad_size = [pitch - pad_to_pad_clearance, drill + 2*pad_copper_y_solder_length]
    if pad_size[0] - drill < 2*min_annular_ring:
        pad_size[0] = drill + 2*min_annular_ring

    #generate the pads
    ############################# Pads ##################################
    # kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
    #                     at=[0, 0], size=pad_size,
    #                     drill=drill, layers=Pad.LAYERS_THT))

    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(PadArray(initial=1, start=[0, 0],
        x_spacing=pitch, pincount=pins,
        size=pad_size, drill=drill,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler,
        **optional_pad_params))

    #draw the courtyard
    cx1 = round_to_grid(x1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(y1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(x2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(y2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    #offset the outline around the connector
    off = configuration['silk_fab_offset']

    xo1 = x1 - off
    yo1 = y1 - off

    xo2 = x2 + off
    yo2 = y2 + off

    #thickness of the notches
    notch = 1.5

    #wall thickness of the outline
    wall = 1.2

    #draw the outline of the connector
    outline = [
    {'x': x_mid,'y': yo2},
    {'x': xo1,'y': yo2},
    {'x': xo1,'y': yo1},
    {'x': xo1+wall+2*off,'y': yo1},
    {'x': xo1+wall+2*off,'y': y3 - off},
    {'x': A/2,'y': y3 - off},
    #{'x': -1.1,'y': y3 + off}
    ]
    if variant == 'A-1':
        outline = outline[:-1]
    kicad_mod.append(PolygonLine(shape=outline, layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=outline, x_mirror=x_mid, layer='F.SilkS', width=configuration['silk_line_width']))

    outline = [
    {'x': x_mid,'y': y2},
    {'x': x1,'y': y2},
    {'x': x1,'y': y1},
    {'x': x1+wall,'y': y1},
    {'x': x1+wall,'y': y3},
    {'x': A/2,'y': y3},
    #{'x': -1.1,'y': y3 + off}
    ]
    kicad_mod.append(PolygonLine(shape=outline, layer='F.Fab', width=configuration['fab_line_width']))
    kicad_mod.append(PolygonLine(shape=outline, x_mirror=x_mid, layer='F.Fab', width=configuration['fab_line_width']))


    #draw the pinsss
    for i in range(pins):

        x = i * pitch
        w = 0.25
        kicad_mod.append(Rectangle(start=[x-w,y3+1], end=[x+w,y2-0.5], layer='F.SilkS', width=configuration['silk_line_width']))

    #add pin-1 designator
    px = 0
    py = -1.5
    m = 0.3

    pin1 = [
    {'x': px,'y': py},
    {'x': px-m,'y': py-2*m},
    {'x': px+m,'y': py-2*m},
    {'x': px,'y': py},
    ]

    kicad_mod.append(PolygonLine(shape=pin1, layer='F.SilkS', width=configuration['silk_line_width']))
    if fab_pin1_marker_type == 1:
        kicad_mod.append(PolygonLine(shape=pin1, layer='F.Fab', width=configuration['fab_line_width']))

    if fab_pin1_marker_type == 2:
        fab_marker_left = -fab_first_marker_w/2.0
        fab_marker_bottom = y3 - fab_first_marker_h
        poly_fab_marker = [
            {'x':fab_marker_left, 'y':y3},
            {'x':0, 'y':fab_marker_bottom},
            {'x':fab_marker_left + fab_first_marker_w, 'y':y3}
        ]
        kicad_mod.append(PolygonLine(shape=poly_fab_marker, layer='F.Fab', width=configuration['fab_line_width']))

    ######################### Text Fields ###############################
    text_center_y = 'center'
    body_edge={'left':x1, 'right':x2, 'top':y1, 'bottom':y2}
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position=text_center_y)


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
    for variant in variant_params:
        for pincount in variant_params[variant]['pin_range']:
            generate_one_footprint(generator_name, global_config, pincount, variant, configuration)
            num_fps_generated += 1
    return num_fps_generated


