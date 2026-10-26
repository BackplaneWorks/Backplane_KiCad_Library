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
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC

#Molex part number
#n = number of circuits per row
#with boss, suffix = 10
#no boss, suffix = 30
part = "55935-{n:02}{boss}"
variant_params = {
    'no_boss':{
        'boss': False,
        'datasheet': 'http://www.molex.com/pdm_docs/sd/559350530_sd.pdf',
        'part_code': "55935-{n:02}30",
        },
    'boss':{
        'boss': True,
        'datasheet': 'http://www.molex.com/pdm_docs/sd/559350210_sd.pdf',
        'part_code': "55935-{n:02}10",
        }
}

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, variant, configuration):

    draw_inner_details = False

    series = "MicroClasp"
    series_long = 'MicroClasp Wire-to-Board System'
    manufacturer = 'Molex'
    orientation = 'H'
    number_of_rows = 1

    pitch = 2
    drill = 0.8
    start_pos_x = 0 # Where should pin 1 be located.
    pad_to_pad_clearance = 0.8
    max_annular_ring = 0.5 #How much copper should be in y direction?
    min_annular_ring = 0.15

    pad_size = [pitch - pad_to_pad_clearance, drill + 2*max_annular_ring]
    if pad_size[0] - drill < 2*min_annular_ring:
        pad_size[0] = drill + 2*min_annular_ring
    if pad_size[0] - drill > 2*max_annular_ring:
        pad_size[0] = drill + 2*max_annular_ring

    pad_shape=Pad.SHAPE_OVAL
    if pad_size[1] == pad_size[0]:
        pad_shape=Pad.SHAPE_CIRCLE


    boss = variant_params[variant]['boss']
    mpn = variant_params[variant]['part_code'].format(n=pins)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("Molex {:s}, {:s}{:s}, {:d} Pins ({:s})".format(series_long,
        mpn, ", with PCB locator" if boss else '',
        pins, variant_params[variant]['datasheet']))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    #calculate fp dimensions

    #B = distance between end-point pins
    B = (pins - 1) * pitch
    #A = total connector length
    A = B + 6
    #C = internal length of connector
    C = B + 3

    #T = length of tab

    if pins == 2:
        T = 5
    else:
        T = 6.78

    #corners
    x1 = -(A-B) / 2
    x2 = x1 + A

    y2 = 9.2
    y1 = y2 - 11.25

    #y-pos of tab
    yt = y1 + 11.75
    xt = B/2 - T/2

    #y-pos backside
    yb = 0

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = body_edge.copy()
    bounding_box['bottom']=yt

    silk_pad_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    out = [
    {'x': B/2, 'y': yt},
    {'x': xt+(yt-y2), 'y': yt},
    {'x': xt, 'y': y2},
    {'x': x1, 'y': y2},
    {'x': x1, 'y': y1},
    {'x': (B-C)/2, 'y': y1},
    {'x': (B-C)/2, 'y': yb},
    {'x': B/2,'y': yb}
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
    yt += o
    xt -= o

    out = [
    {'x': B/2, 'y': yt},
    {'x': xt+(yt-y2), 'y': yt},
    {'x': xt, 'y': y2},
    {'x': x1, 'y': y2},
    {'x': x1, 'y': y1},
    {'x': (B-C)/2+o, 'y': y1},
    {'x': (B-C)/2+o, 'y': yb-o},
    {'x': -pad_size[0]/2-silk_pad_off,'y': yb-o}
    ]
    kicad_mod.append(PolygonLine(shape=out,
                                 layer="F.SilkS", width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=out, x_mirror=B / 2,
                                 layer="F.SilkS", width=configuration['silk_line_width']))

    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    #draw silkscreen in between pads
    for i in range(0,pins-1):
        xa = i * pitch + pad_size[0] / 2 + silk_pad_off
        xb = (i+1) * pitch - pad_size[0] / 2 - silk_pad_off

        kicad_mod.append(Line(start=[xa,yb-o],end=[xb,yb-o], layer='F.SilkS', width=configuration['silk_line_width']))


    #generate the pads
    kicad_mod.append(PadArray(
        pincount=pins, x_spacing=pitch, type=Pad.TYPE_THT,
        shape=pad_shape, size=pad_size, drill=drill, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler,
        **optional_pad_params))

    #add PCB locator if needed
    if boss:
        boss_x = B+2
        boss_y = 2.4
        boss_drill = 1.2
        kicad_mod.append(Pad(at=[boss_x, boss_y], size=boss_drill, drill=boss_drill,
            type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH))
        boss_x = -2
        kicad_mod.append(Pad(at=[boss_x, boss_y], size=boss_drill, drill=boss_drill,
            type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH))

    #pin-1 marker
    y =  3.5
    m = 0.3

    p1m_sl = 2
    p1m_off = o + 0.3
    pin = [
        {'x': body_edge['left'] - p1m_off,'y': body_edge['top']+p1m_sl},
        {'x': body_edge['left'] - p1m_off,'y': body_edge['top']-p1m_off},
        {'x': body_edge['left'] + p1m_sl,'y': body_edge['top']-p1m_off},
    ]

    kicad_mod.append(PolygonLine(shape=pin,
                                 layer="F.SilkS", width=configuration['silk_line_width']))

    p1m_sl = 1

    pin = [
        {'x': -p1m_sl/2,'y': 0},
        {'x': 0,'y': 0 + p1m_sl/sqrt(2)},
        {'x': p1m_sl/2,'y': 0},
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 layer="F.Fab", width=configuration['fab_line_width']))

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
    #pins_per_row_per_row per row
    pins_per_row_range = range(2,16)
    for variant in variant_params:
        for pins_per_row in pins_per_row_range:
            generate_one_footprint(generator_name, global_config, pins_per_row, variant, configuration)
            num_fps_generated += 1
    return num_fps_generated
