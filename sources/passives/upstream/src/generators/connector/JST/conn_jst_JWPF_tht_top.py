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

series = "JWPF"
manufacturer = 'JST'
orientation = 'V'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/eJWPF1.pdf'


part_base = "B{n:02}B-JWPF-SK-R" #JST part number format string

prefix = "JST_JWPF_"

pitch = 2.00
pad_to_pad_clearance = 0.8
pad_copper_x_solder_length = 0.5 #How much copper should be in y direction?
min_annular_ring = 0.15

# Connector Dimensions
tab_width = 7.0
row_spacing = 4.0
pad_drill = 1.0
mount_hole_size = 1.15
mount_hole_offset_x = 1.5

# Width of connector
jwpf_widths = {
    2 : 8.1,
    3 : 8.4,
    4 : 8.4,
    6 : 12.8,
    8 : 12.5
}

jwpf_lengths = {
    2 : 7,
    3 : 9,
    4 : 11,
    6 : 9.8,
    8 : 11.8
}

pin_range = [2, 3, 4, 6, 8]


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pincount, configuration):
    if pincount in [6, 8]:
        number_of_rows = 2
        pin_per_row = int(pincount / 2)
    else:
        number_of_rows = 1
        pin_per_row = pincount

    mpn = part_base.format(n=pincount)

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pin_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("JST {:s} series connector, {:s} ({:s})".format(series, mpn, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    conn_width = jwpf_widths[pincount]
    conn_length = jwpf_lengths[pincount]

    mount_hole_offset_y = 2.05 if number_of_rows == 1 else 2.45


    # Add texts
    x_mid = (number_of_rows-1) * row_spacing / 2
    y_mid = (pin_per_row - 1) * pitch / 2.0

    # Connector outline
    y1 = y_mid - conn_length / 2
    y2 = y_mid + conn_length / 2

    x1 = -5.4 # measured from 3D model alignment
    x2 = x1 + conn_width

    body_edge={'left':x1, 'right':x2, 'top':y1, 'bottom':y2}

    y_ref = -3 if number_of_rows == 1 else -4

    pad_size = [pad_drill + 2*pad_copper_x_solder_length, pitch - pad_to_pad_clearance]
    if number_of_rows > 1:
        if pad_size[0] - pad_drill > 2*pad_copper_x_solder_length:
            pad_size[0] = pad_drill + 2*pad_copper_x_solder_length
        if pad_size[0] - pad_drill < 2*min_annular_ring:
            pad_size[0] = pad_drill + 2*min_annular_ring
    if pad_size[1] - pad_drill < 2*min_annular_ring:
        pad_size[1] = pad_drill + 2*min_annular_ring

    if pad_size[0] == pad_size[1]:
        pad_shape = Pad.SHAPE_CIRCLE
    else:
        pad_shape = Pad.SHAPE_OVAL

    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    # Create pins
    for i in range(number_of_rows):
        kicad_mod.append(PadArray(
            initial=1+i*pin_per_row, start=[i*row_spacing, 0],
            pincount=pin_per_row, y_spacing=pitch,
            type=Pad.TYPE_THT, shape=pad_shape,
            size=pad_size, drill=pad_drill, layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params))

    # Add mounting hole
    mx = -mount_hole_offset_x
    my = (pin_per_row - 1) * pitch + mount_hole_offset_y
    kicad_mod.append(Pad(at=[mx, my], size=mount_hole_size, drill=mount_hole_size, shape=Pad.SHAPE_CIRCLE, type=Pad.TYPE_NPTH, layers=Pad.LAYERS_NPTH))

    # Tab dimensions
    tw = 7
    tt = 0.5

    ########################### CrtYd #################################
    cx1 = round_to_grid(x1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(y1-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(x2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(y2+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    def draw_outline(offset=0, layer='F.Fab', width=configuration['fab_line_width']):
        O = offset
        R = 1.0

        if pincount == 2:
            poly = [
                {'x': x2 + O - R, 'y': y1 - O},
                {'x': x1 - O, 'y': y1 - O},
                {'x': x1 - O, 'y': y2 + O},
                {'x': x2 + O - R, 'y': y2 + O},
            ]

            kicad_mod.append(PolygonLine(shape=poly, layer=layer, width=width))
        else:
            # top line
            kicad_mod.append(Line(start=[tt+x1-O+R, y1-O], end=[x2+O-R, y1-O], layer=layer, width=width))
            # bottom line
            kicad_mod.append(Line(start=[tt+x1-O+R, y2+O], end=[x2+O-R, y2+O], layer=layer, width=width))

            # left line (including tab)
            poly = [
                {'x': tt+x1-O, 'y': y1-O+R},
                {'x': tt+x1-O, 'y': y_mid - tw/2.0 - O},
                {'x': x1-O, 'y': y_mid - tw/2.0 - O},
                {'x': x1-O, 'y': y_mid + tw/2.0 + O},
                {'x': tt+x1-O, 'y': y_mid + tw/2.0 + O},
                {'x': tt+x1-O, 'y': y2+O-R}
            ]

            kicad_mod.append(PolygonLine(shape=poly, width=width, layer=layer))

            # top left
            kicad_mod.append(Arc(center=[tt+x1-O+R, y1-O+R], start=[tt+x1-O, y1-O+R], angle=90.0, layer=layer, width=width))
            # bottom left
            kicad_mod.append(Arc(center=[tt+x1-O+R, y2+O-R], start=[tt+x1-O+R, y2+O], angle=90.0, layer=layer, width=width))


        # right line
        kicad_mod.append(Line(start=[x2+O, y1-O+R], end=[x2+O, y2+O-R], layer=layer, width=width))

        # top right
        kicad_mod.append(Arc(center=[x2+O-R, y1-O+R], start=[x2+O-R, y1-O], angle=90.0, layer=layer, width=width))

        # bottom right
        kicad_mod.append(Arc(center=[x2+O-R, y2+O-R], start=[x2+O, y2+O-R], angle=90.0, layer=layer, width=width))


    draw_outline()
    draw_outline(offset=configuration['silk_fab_offset'], layer='F.SilkS', width=configuration['silk_line_width'])

    # Add pin-1 marker on F.SilkS
    Q = 0.35 # offset
    L = 1.5
    p1 = [
        {'x': x1 - Q, 'y': y1 - Q + L},
        {'x': x1 - Q, 'y': y1 - Q},
        {'x': x1 - Q + L, 'y': y1 - Q},
    ]

    kicad_mod.append(PolygonLine(shape=p1, layer='F.SilkS', width=configuration['silk_line_width']))

    # Add pin-1 marker on F.Fab
    D = -0.5 - pad_size[1] / 2
    M = 0.75
    p1 = [
        {'x': -M/2, 'y': D - M},
        {'x': M/2, 'y': D - M},
        {'x': 0, 'y': D},
        {'x': -M/2, 'y': D - M},
    ]

    kicad_mod.append(PolygonLine(shape=p1, layer='F.Fab', width=configuration['fab_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='left')

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
