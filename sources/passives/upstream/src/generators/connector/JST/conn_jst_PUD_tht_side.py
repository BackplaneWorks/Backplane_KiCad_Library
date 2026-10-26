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

series = "PUD"
manufacturer = 'JST'
orientation = 'H'
number_of_rows = 2
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/ePUD.pdf'

pitch = 2.0
row_pitch = 2
drill = 0.75 # 0.7 +0.1/-0 -> 0.75+/-0.05
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5 #How much copper should be in y direction?
min_annular_ring = 0.15

mh_drill = 1.65
mh_y = row_pitch + 7.7

pin_range = range(4,21) #number of pins in each row

#FP name strings
part_base = "S{n:02}B-PUDSS-1" #JST part number format string

#FP description and tags

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, configuration):
    mpn = part_base.format(n=pins*number_of_rows) #JST part number format string
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

    #calculate fp dimensions
    A = (pins - 1) * pitch
    B = A + 4

    #generate the pads (row 1)
    size = [pitch - pad_to_pad_clearance, row_pitch - pad_to_pad_clearance]
    if size[0] - drill < 2*min_annular_ring:
        size[0] = drill + 2*min_annular_ring
    if size[0] - drill > 2*pad_copper_y_solder_length:
        size[0] = drill + 2*pad_copper_y_solder_length

    if size[1] - drill < 2*min_annular_ring:
        size[1] = drill + 2*min_annular_ring
    if size[1] - drill > 2*pad_copper_y_solder_length:
        size[1] = drill + 2*pad_copper_y_solder_length

    if size[0] == size[1]:
        pad_shape = Pad.SHAPE_CIRCLE
    else:
        pad_shape = Pad.SHAPE_OVAL

    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    for row_idx in range(2):
        kicad_mod.append(PadArray(
            pincount=pins, x_spacing=pitch,
            type=Pad.TYPE_THT, shape=pad_shape,
            start=[0, row_idx*row_pitch], initial=row_idx+1, increment=2,
            size=size, drill=drill,  layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params))

    #draw the component outline
    x1 = A/2 - B/2
    x2 = x1 + B
    y2 = row_pitch + 7.7 + 2.4
    y1 = y2 - 12.7
    body_edge={'left':x1, 'right':x2, 'top':y1, 'bottom':y2}

    #draw simple outline on F.Fab layer
    kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2],layer='F.Fab',width=configuration['fab_line_width']))
    ########################### CrtYd #################################
    cx1 = round_to_grid(x1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    if y1 < -size[1]/2:
        cy1 = round_to_grid(y1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    else:
        cy1 = round_to_grid(-size[1]/2-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])


    cx2 = round_to_grid(x2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(y2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    #offset off
    off = configuration['silk_fab_offset']

    x1 -= off
    y1 -= off
    x2 += off
    y2 += off

    #outline
    side = [
    {'x': -1,'y': y1},
    {'x': x1,'y': y1},
    {'x': x1,'y': y2},
    {'x': A/2,'y': y2},
    ]

    kicad_mod.append(PolygonLine(shape=side, width=configuration['silk_line_width'], layer='F.SilkS'))
    kicad_mod.append(PolygonLine(shape=side, x_mirror=A / 2, width=configuration['silk_line_width'], layer='F.SilkS'))

    #add mounting holes
    m1 = Pad(at=[-0.9,mh_y],layers=Pad.LAYERS_NPTH,shape=Pad.SHAPE_CIRCLE,type=Pad.TYPE_NPTH,size=mh_drill, drill=mh_drill)
    m2 = Pad(at=[A+0.9,mh_y],layers=Pad.LAYERS_NPTH,shape=Pad.SHAPE_CIRCLE,type=Pad.TYPE_NPTH,size=mh_drill, drill=mh_drill)

    kicad_mod.append(m1)
    kicad_mod.append(m2)

    D = 0.3
    L = 2.5

    #add p1 marker
    marker = [
        {'x': pitch/2 , 'y': y1-D+0.25},
        {'x': pitch/2 , 'y': y1-D},
        {'x': x1-D,'y': y1-D},
        {'x': x1-D,'y': y1-D+L}
    ]

    kicad_mod.append(PolygonLine(shape=marker, width=configuration['silk_line_width'], layer='F.SilkS'))
    sl = 1
    marker =[
        {'x': sl/2 , 'y': body_edge['top']},
        {'x': 0 , 'y': body_edge['top']+sl/sqrt(2)},
        {'x': -sl/2 , 'y': body_edge['top']}
    ]
    kicad_mod.append(PolygonLine(shape=marker, layer='F.Fab', width=configuration['fab_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center')

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
    for pincount in pin_range:
        generate_one_footprint(generator_name, global_config, pincount, configuration)
        num_fps_generated += 1
    return num_fps_generated
