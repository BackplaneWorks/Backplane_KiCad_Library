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

from itertools import chain

series = "XH"
manufacturer = 'JST'
orientation = 'V'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/eXH.pdf'

pitch = 2.50
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5 #How much copper should be in y direction?
min_annular_ring = 0.15

#FP name strings
part_base = "B{n}B-XH-{variant:s}" #JST part number format string

variant_params = {
    'A':{
        'boss': False,
        'back_protrusion': False,
        'pin_range': chain(range(2,17), [20])
    },
    'AM':{
        'boss': True,
        'back_protrusion': False,
        'pin_range': chain(range(1,11), [12])
    }
}

fab_first_marker_w = 1.25
pin1_marker_linelen = 1.25
fab_first_marker_h = 1
fab_pin1_marker_type = 2
pin1_marker_offset = 0.3

#FP description and tags

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, variant, configuration):
    #calculate fp dimensions
    boss = variant_params[variant]['boss']
    A = (pins - 1) * pitch
    B = A + 4.9

    #connector thickness
    T = 5.75

    #corners
    x1 = -2.45
    x2 = x1 + B


    x_mid = (x1 + x2) / 2

    y1 = -2.35
    y2 = y1 + T

    #generate the name
    mpn = part_base.format(n=pins, variant=variant)
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("JST {:s} series connector, {:s}{:s} ({:s})".format(
        series, mpn, ', with boss' if boss else '', datasheet))

    tags = configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation])
    if boss:
        tags += " boss"
    #set the FP tags
    kicad_mod.setTags(tags)

    #draw simple outline on F.Fab layer
    kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2],layer='F.Fab', width=configuration['fab_line_width']))

    # set general values
    #kicad_mod.append(Property(name=Property.REFERENCE, text='REF**', at=[x_mid,-3.5], layer='F.SilkS'))

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

    if boss:
        if pins == 1:
            boss_y = 4.35
            boss_x = 0
            boss_drill = 1.75
            kicad_mod.append(Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                                 at=[boss_x, boss_y], size=boss_drill,
                                 drill=boss_drill, layers=Pad.LAYERS_NPTH))
        else:
            boss_y = 2
            boss_x = -1.6
            boss_drill = 1.2
            kicad_mod.append(Pad(type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                                 at=[boss_x, boss_y], size=boss_drill,
                                 drill=boss_drill, layers=Pad.LAYERS_NPTH))

    if boss and pins == 1:
        boss_size_1pin = 1.5
        off = configuration['silk_fab_offset']
        x_boss_fab_off = boss_size_1pin/2 + off
        x_boss_pad_off = boss_drill/2 + configuration['silk_line_width']/2 + configuration['silk_pad_clearance']
        x_boss = x_boss_fab_off
        if x_boss_pad_off > x_boss:
            x_boss=x_boss_pad_off
        out_silk = PolygonLine(shape=[
            {'x': -x_boss, 'y':boss_y},
            {'x': -x_boss, 'y':y2+off},
            {'x': x1-off, 'y':y2+off},
            {'x': x1-off, 'y':y1-off},
            {'x': x2+off, 'y':y1-off},
            {'x': x2+off, 'y':y2+off},
            {'x': x_boss, 'y':y2+off},
            {'x': x_boss, 'y':boss_y}
        ], layer='F.SilkS', width=configuration['silk_line_width'])
        kicad_mod.append(out_silk)
        kicad_mod.append(Arc(center=[0,boss_y], start=[-x_boss, boss_y], angle=-180,
            layer="F.SilkS", width=configuration['silk_line_width']))

        out_fab = PolygonLine(shape=[
            {'x': -boss_size_1pin/2, 'y':boss_y},
            {'x': -boss_size_1pin/2, 'y':y2},
            {'x': x1, 'y':y2},
            {'x': x1, 'y':y1},
            {'x': x2, 'y':y1},
            {'x': x2, 'y':y2},
            {'x': boss_size_1pin/2, 'y':y2},
            {'x': boss_size_1pin/2, 'y':boss_y}
        ], layer='F.Fab', width=configuration['fab_line_width'])
        kicad_mod.append(out_fab)
        kicad_mod.append(Arc(center=[0,boss_y], start=[-boss_size_1pin/2, boss_y], angle=-180,
            layer="F.Fab", width=configuration['fab_line_width']))


    else:
        out = Rectangle(start=[x1,y1], end=[x2,y2], offset=configuration['silk_fab_offset'],
            layer='F.SilkS', width=configuration['silk_line_width'])
        kicad_mod.append(out)
    body_edge={'left':x1, 'right':x2, 'top':y1, 'bottom':y2}

    #draw the courtyard
    cx1 = round_to_grid(x1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(y1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(x2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(y2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    if boss and pins == 1:
        cy2 = round_to_grid(boss_y+boss_drill/2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    #draw the connector outline


    if fab_pin1_marker_type == 2:
        fab_marker_left = -fab_first_marker_w/2.0
        fab_marker_bottom = y1 + fab_first_marker_h
        poly_fab_marker = [
            {'x':fab_marker_left, 'y':y1},
            {'x':0, 'y':fab_marker_bottom},
            {'x':fab_marker_left + fab_first_marker_w, 'y':y1}
        ]
        kicad_mod.append(PolygonLine(shape=poly_fab_marker, layer='F.Fab', width=configuration['fab_line_width']))

    #wall thickness w
    w = 0.75

    #gap size g
    g = 1.5

    off = 0.1

    x1 -= off
    y1 -= off

    x2 += off
    y2 += off

    #draw the center tab
    kicad_mod.append(Rectangle(start=[g/2,y1], end=[A-g/2,y1+w], layer='F.SilkS', width=configuration['silk_line_width']))

    #add left tab
    kicad_mod.append(Rectangle(start=[x1,y1], end=[-g/2,y1+w], layer='F.SilkS', width=configuration['silk_line_width']))
    #right tab
    kicad_mod.append(Rectangle(start=[A+g/2,y1], end=[x2,y1+w], layer='F.SilkS', width=configuration['silk_line_width']))

    #add other line
    line = [
    {'x': x1,'y': y1+w+g},
    {'x': x1+w,'y': y1+w+g},
    {'x': x1+w,'y': y2-w},
    {'x': A/2,'y': y2-w}
    ]
    if boss and pins > 1:
        line2 = line[:2]
        line2.append({'x': x1+w,'y': boss_y - boss_drill/2 - configuration['silk_line_width']/2 - configuration['silk_pad_clearance']})
        kicad_mod.append(PolygonLine(shape=line2, layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Line(start=[A/2, y2-w],
            end=[boss_x+boss_drill/2+ configuration['silk_line_width']/2 + configuration['silk_pad_clearance'], y2-w],
            layer='F.SilkS', width=configuration['silk_line_width']))
    else:
        kicad_mod.append(PolygonLine(shape=line, layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=line, x_mirror=A / 2, layer='F.SilkS', width=configuration['silk_line_width']))

    #pin-1 marker
    y =  -2.75
    m = 0.3

    poly_pin1_marker = [
        {'x':x1-pin1_marker_offset+pin1_marker_linelen, 'y':y1-pin1_marker_offset},
        {'x':x1-pin1_marker_offset, 'y':y1-pin1_marker_offset},
        {'x':x1-pin1_marker_offset, 'y':y1-pin1_marker_offset+pin1_marker_linelen}
    ]
    if fab_pin1_marker_type == 2:
        kicad_mod.append(PolygonLine(shape=poly_pin1_marker, layer='F.SilkS', width=configuration['silk_line_width']))
    if fab_pin1_marker_type == 3:
        kicad_mod.append(PolygonLine(shape=poly_pin1_marker, layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(PolygonLine(shape=poly_pin1_marker, layer='F.Fab', width=configuration['fab_line_width']))

    pin = [
    {'x': 0,'y': y},
    {'x': -m,'y': y-2*m},
    {'x': m,'y': y-2*m},
    {'x': 0,'y': y},
    ]


    if fab_pin1_marker_type == 1:
        kicad_mod.append(PolygonLine(shape=pin, layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(PolygonLine(shape=pin, layer='F.Fab', width=configuration['fab_line_width']))

    ######################### Text Fields ###############################
    text_center_y = 'bottom'
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
