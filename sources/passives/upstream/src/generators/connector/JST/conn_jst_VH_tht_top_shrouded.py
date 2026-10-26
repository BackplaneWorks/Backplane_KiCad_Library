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

series = "VH"
manufacturer = 'JST'
orientation = 'V'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/eVH.pdf'

pitch = 3.96
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5 #How much copper should be in y direction?
min_annular_ring = 0.15
drill = 1.7 # 1.65 +0.1/-0.0 -> 1.7+/-0.05
mh_drill = 1.45
mh_at = [-1.5, -3.4]

pin_range = range(2, 11) #number of pins in each row

#FP name strings
part_base = "B{n:d}P-VH-FB-B" #JST part number format string

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, configuration):
    mpn = part_base.format(n=pins)
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("JST {:s} series connector, {:s}, shrouded ({:s})".format(series, mpn, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    #calculate dimensions
    A = (pins - 1) * pitch
    B = A + 5.84



    #coordinate locations (latch is not drawn but is 2.3mm above y5 and width varies)
    #    x1 x5 x3           x4 x6 x2
    # y1 ______             ______
    # y3 | O  |_____________|    |
    # y5 |  ___________________  |
    #    |  | 1 2 3 4 5 6 7 8  | |
    # y4 |  |__________________| |
    # y2 |_______________________|

    #draw the component outline
    x1 = A/2 - B/2
    x2 = x1 + B
    x3 = x1 + 2.9
    x4 = x2 - 2.9
    x5 = -2
    x6 = pitch * (pins - 1) + 2
    y2 = 5.2
    y1 = y2 - 9.7
    y3 = y1 + 1.2
    y4 = 4.3
    y5 = y4 - 6.4
    body_edge={'left':x1, 'right':x2, 'top':y1, 'bottom':y2}

    #draw outline on F.Fab layer
    kicad_mod.append(PolygonLine(shape=[{ 'x':x1, 'y':y2 },
                                           {'x':x1,'y':y1},
                                           {'x':x3,'y':y1},
                                           {'x':x3,'y':y3},
                                           {'x':x4,'y':y3},
                                           {'x':x4,'y':y1},
                                           {'x':x2,'y':y1},
                                           {'x':x2,'y':y2},
                                           {'x':x1,'y':y2}],
                                 layer='F.Fab', width=configuration['fab_line_width']))

    #draw rectangle on F.Fab for shroud walls
    kicad_mod.append(Rectangle(start=[x5,y4],end=[x6,y5],layer='F.Fab',width=configuration['fab_line_width']))

	#draw pin1 mark on F.Fab
    kicad_mod.append(PolygonLine(shape=[{ 'x':x1, 'y':-1 }, { 'x':(x1 + 1), 'y':0 }], layer='F.Fab', width=configuration['fab_line_width']))
    kicad_mod.append(PolygonLine(shape=[{ 'x':x1, 'y':1 }, { 'x':(x1 + 1), 'y':0 }], layer='F.Fab', width=configuration['fab_line_width']))

    ########################### CrtYd #################################
    cx1 = round_to_grid(x1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(y1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(x2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(y2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    #draw silk outline
    off = configuration['silk_fab_offset']
    x1 -= off
    y1 -= off
    x2 += off
    y2 += off
    x3 += off
    y3 -= off
    x4 -= off

    kicad_mod.append(PolygonLine(shape=[{ 'x':x1, 'y':y2 },
                                           {'x':x1,'y':y1},
                                           {'x':x3,'y':y1},
                                           {'x':x3,'y':y3},
                                           {'x':x4,'y':y3},
                                           {'x':x4,'y':y1},
                                           {'x':x2,'y':y1},
                                           {'x':x2,'y':y2},
                                           {'x':x1,'y':y2}],
                                 layer='F.SilkS', width=configuration['silk_line_width']))

    #add pin1 mark on silk
    px = x1 - 0.2
    m = 0.3

    marker = [{'x': px,'y': 0},{'x': px-2*m,'y': m},{'x': px-2*m,'y': -m},{'x': px,'y': 0}]

    kicad_mod.append(PolygonLine(shape=marker, layer="F.SilkS", width=configuration['silk_line_width']))

    #generate tht pads (1.65mm drill with 2.35x3mm oval pads)
    pad_size = [pitch - pad_to_pad_clearance, drill + 2*pad_copper_y_solder_length]
    if pad_size[0] - drill < 2*min_annular_ring:
        pad_size[0] = drill + 2*min_annular_ring
    if pad_size[0] - drill > 2*pad_copper_y_solder_length:
        pad_size[0] = drill + 2*pad_copper_y_solder_length

    shape=Pad.SHAPE_OVAL
    if pad_size[1] == pad_size[0]:
        shape=Pad.SHAPE_CIRCLE

    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(PadArray(
        pincount=pins, x_spacing=pitch,
        type=Pad.TYPE_THT, shape=shape,
        size=pad_size, drill=drill, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler,
        **optional_pad_params))

    #generate mounting post
    post = Pad(at=mh_at, type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=mh_drill, drill=mh_drill, layers=Pad.LAYERS_NPTH)
    kicad_mod.append(post)

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position=2.5)

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
