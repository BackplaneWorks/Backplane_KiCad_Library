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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

from math import sqrt
from typing import Any

from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


series = ""
series_long = '734 Male header (for PCBs); Angled solder pin 1 x 1 mm'
manufacturer = 'Wago'
orientation = 'H'
number_of_rows = 1
datasheet = 'http://www.farnell.com/datasheets/2157639.pdf'

pinrange= [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 24]


# Connector voltage ratings:
# Rated voltage  (III / 3) [V]           160 V
# Rated impulse voltage (III / 3) [kV]   2.5 kV

# Rated voltage (III/2) [V]              160 V
# Rated impulse voltage (III / 2) [kV]   2.5 kV

# Rated voltage (II / 2) [V]             320 V
# Rated impulse voltage (II / 2) [kV]    2.5 kV

# VDE 0110-1/4.97 2.5kV -> 1.5mm clearance
pad_to_pad_clearance = 1.5

pitch = 3.5
drill = 1.6 # square pins:1mm -> touching circle: √(2)mm ~ 1.4mm -> minimum drill accourding to KLC: 1.6mm

start_pos_x = 0
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

mpn_format = '734-1{n_plus_60:02d}'

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pincount, configuration):

    pad_silk_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    mpn = mpn_format.format(n_plus_60=pincount+60)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pincount, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    footprint_name = footprint_name.replace("__", '_')

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    descr_format_str = "Molex {:s}, {:s} , {:d} Pins ({:s})"
    kicad_mod.setDescription(descr_format_str.format(series_long, mpn, pincount, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    # calculate working values
    end_pos_x = (pincount-1) * pitch
    centre_x = (end_pos_x - start_pos_x) / 2.0
    nudge = configuration['silk_fab_offset']
    silk_w = configuration['silk_line_width']
    fab_w = configuration['fab_line_width']


    body_edge={
        'left':start_pos_x - 2.8,
        'right':end_pos_x + 3.1,
        'bottom':9.3
        }
    body_edge['top'] = body_edge['bottom']-10.3

    # create pads
    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(PadArray(initial=1, start=[start_pos_x, 0],
        x_spacing=pitch, pincount=pincount,
        size=pad_size, drill=drill,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler,
        **optional_pad_params))

    # create fab outline
    kicad_mod.append(Rectangle(start=[body_edge['left'], body_edge['top']],
        end=[body_edge['right'], body_edge['bottom']], layer='F.Fab', width=fab_w))

    # create silkscreen
    x1 = start_pos_x -pad_size[0]/2 - pad_silk_off
    xn = end_pos_x + pad_size[0]/2 + pad_silk_off
    kicad_mod.append(PolygonLine(
        shape=[
            {'x': x1, 'y': body_edge['top']-nudge},
            {'x': body_edge['left']-nudge, 'y': body_edge['top']-nudge},
            {'x': body_edge['left']-nudge, 'y': body_edge['bottom']+nudge},
            {'x': body_edge['right']+nudge, 'y': body_edge['bottom']+nudge},
            {'x': body_edge['right']+nudge, 'y': body_edge['top']-nudge},
            {'x': xn, 'y': body_edge['top']-nudge}
        ], layer='F.SilkS', width=silk_w))

    for i in range(pincount-1):
        xl = start_pos_x + i*pitch + pad_size[0]/2 + pad_silk_off
        xr = start_pos_x + (i+1)*pitch - pad_size[0]/2 - pad_silk_off
        kicad_mod.append(Line(
            start=[xl, body_edge['top']-nudge],
            end=[xr, body_edge['top']-nudge],
            layer='F.SilkS', width=silk_w))


    p1s_off = configuration['silk_fab_offset'] + 0.3
    p1s_L = 2
    # pin 1 markers
    kicad_mod.append(PolygonLine(
        shape=[
            {'x': body_edge['left'] - p1s_off, 'y': body_edge['top'] + p1s_L},
            {'x': body_edge['left'] - p1s_off, 'y': body_edge['top'] - p1s_off},
            {'x': x1, 'y': body_edge['top'] - p1s_off}
        ],
        layer='F.SilkS', width=silk_w))

    sl = 1
    poly_pin1_marker = [
        {'y': body_edge['top'], 'x': -sl/2},
        {'y': body_edge['top'] + sl/sqrt(2), 'x': 0},
        {'y': body_edge['top'], 'x': sl/2}
    ]
    kicad_mod.append(PolygonLine(shape=poly_pin1_marker, layer='F.Fab', width=fab_w))

    ########################### CrtYd #################################
    cx1 = round_to_grid(body_edge['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(body_edge['top']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(body_edge['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(body_edge['bottom']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

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
    for pincount in pinrange:
        generate_one_footprint(generator_name, global_config, pincount, configuration)
    return len(pinrange)
