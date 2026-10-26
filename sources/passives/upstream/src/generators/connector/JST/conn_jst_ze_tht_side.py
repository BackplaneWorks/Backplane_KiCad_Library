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
from math import floor, ceil

from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


series = "ZE"
manufacturer = 'JST'
orientation = 'H'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/eZE.pdf'

pitch = 1.5
y_spacing = 3.70

drill = 0.75 # 0.7 +0.1/-0.1 -> 0.75 +/-0.05
pad_size = [1.4, 1.75] # Using same pad size as top entry

mh_drill = 1.15

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pincount, configuration):
    mpn = "S{pincount:02}B-ZESK-2D".format(pincount=pincount)
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pincount, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("JST {:s} series connector, {:s} ({:s})".format(series, mpn, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    #dimensions
    A = (pincount - 1) * 1.5
    B = A + 4.5

    #outline
    x1 = -1.55 - 0.7
    x2 = x1 + B

    xMid = x1 + B/2

    y2 = 3.7 + 3.65
    y1 = y2 - 7.8
    body_edge={'left':x1, 'right':x2, 'top':y1, 'bottom':y2}

    #add outline to F.Fab
    kicad_mod.append(Rectangle(
        start={'x': x1, 'y': y1},
        end={'x': x2, 'y': y2},
        layer='F.Fab', width=configuration['fab_line_width']
        ))

    ########################### CrtYd #################################
    cx1 = round_to_grid(x1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    if y1 < -pad_size[1]/2:
        cy1 = round_to_grid(y1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    else:
        cy1 = round_to_grid(-pad_size[1]/2-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(x2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(y2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    #expand the outline a little bit
    out = configuration['silk_fab_offset']
    x1 -= out
    x2 += out
    y1 -= out
    y2 += out

    silk_pad_offset = configuration['silk_line_width']/2 + configuration['silk_pad_clearance']
    if y1 < -(pad_size[1]/2 + silk_pad_offset):
        kicad_mod.append(Rectangle(start={'x':x1,'y':y1}, end={'x':x2,'y':y2},
            width=configuration['silk_line_width'], layer="F.SilkS"))
    else:
        num_odd_pins = ceil(pincount/2)
        pos_last_odd_pad = (num_odd_pins-1) * 2*pitch
        poly_silk = [
            {'x': -(pad_size[0]/2 + silk_pad_offset), 'y': y1},
            {'x': x1, 'y': y1},
            {'x': x1, 'y': y2},
            {'x': x2, 'y': y2},
            {'x': x2, 'y': y1},
            {'x': pos_last_odd_pad + (pad_size[0]/2 + silk_pad_offset), 'y': y1},
        ]
        kicad_mod.append(PolygonLine(shape=poly_silk,
                                     width=configuration['silk_line_width'], layer="F.SilkS"))
        for i in range(num_odd_pins-1):
            kicad_mod.append(Line(start=[i * 2*pitch + (pad_size[0]/2 + silk_pad_offset), y1],
                end=[(i+1) * 2*pitch - (pad_size[0]/2 + silk_pad_offset), y1],
                width=configuration['silk_line_width'], layer="F.SilkS"))


    # create odd numbered pads
    #createNumberedPadsTHT(kicad_mod, ceil(pincount/2), pitch * 2, drill, pad_size,  increment=2)
    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    for row_idx in range(2):
        kicad_mod.append(PadArray(
            initial=row_idx+1, start=[row_idx*pitch, row_idx*y_spacing],
            x_spacing=pitch*2,
            pincount=ceil(pincount/2) if row_idx == 0 else floor(pincount/2),
            size=pad_size, drill=drill, increment=2,
            type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL,  layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params))
    #create even numbered pads
    #createNumberedPadsTHT(kicad_mod, floor(pincount/2), pitch * 2, drill, pad_size, starting=2, increment=2, y_off=y_spacing, x_off=pitch)



    #add mounting holes
    # kicad_mod.append(MountingHole(
    #     {'x': -1.55, 'y': 1.85},
    #     1.1
    # ))
    #
    # kicad_mod.append(MountingHole(
    #     {'x': A+1.55    , 'y': 1.85},
    #     1.1
    # )
    kicad_mod.append(Pad(at={'x': -1.55, 'y': 1.85}, type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH,
        drill=mh_drill, size=mh_drill))
    kicad_mod.append(Pad(at={'x': A+1.55, 'y': 1.85}, type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH,
        drill=mh_drill, size=mh_drill))

    #draw the line at the bottom

    xa = xMid - A/2 + out
    xb = xMid + A/2 - out
    y3 = y2 - 1
    kicad_mod.append(PolygonLine(shape=[
        {'x':xa,'y':y2},
        {'x':xa,'y':y3},
        {'x':xb,'y':y3},
        {'x':xb,'y':y2}
    ], width=configuration['silk_line_width'], layer="F.SilkS"))

    # add pin-1 marker
    D = 0.3
    L = 1.5
    pin_1 = [
        {'x': x1-D,'y': y1-D+L},
        {'x': x1-D,'y':  y1-D},
        {'x': x1-D + L,'y':  y1-D},
    ]

    kicad_mod.append(PolygonLine(shape=pin_1, width=configuration['silk_line_width'], layer="F.SilkS"))
    kicad_mod.append(PolygonLine(shape=pin_1, layer='F.Fab', width=configuration['fab_line_width']))

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
    for pincount in range(2, 17):
        generate_one_footprint(generator_name, global_config, pincount, configuration)
        num_fps_generated += 1
    return num_fps_generated
