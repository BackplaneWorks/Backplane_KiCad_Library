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

series = "PH"
manufacturer = 'JST'
orientation = 'H'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/ePH.pdf'

silk_pin1_marker_type = 2
fab_pin1_marker_type = 3


pitch = 2.00
#pad_size=[1.2, 1.7]
drill_size = 0.75 #Datasheet: 0.7 +0.1/-0.0 => It might be better to assume 0.75 +/-0.05mm
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5 #How much copper should be in y direction?
min_annular_ring = 0.15

# Connector Parameters
x_min = -1.95
y_max = 6.25
y_min = y_max-6-1.6
y_main_min = y_max - 6

body_back_protrusion_width=0.7

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pincount, configuration):
    silk_x_min = x_min - configuration['silk_fab_offset']
    silk_y_min = y_min - configuration['silk_fab_offset']
    silk_y_main_min = y_main_min - configuration['silk_fab_offset']
    silk_y_max = y_max + configuration['silk_fab_offset']

    x_mid = (pincount-1)*pitch/2.0
    x_max = (pincount-1)*pitch + 1.95
    silk_x_max = x_max + configuration['silk_fab_offset']

    pad_size = [pitch - pad_to_pad_clearance, drill_size + 2*pad_copper_y_solder_length]
    if pad_size[0] - drill_size < 2*min_annular_ring:
        pad_size[0] = drill_size + 2*min_annular_ring

    # Through-hole type shrouded header, Side entry type
    mpn = "S{n}B-PH-K".format(n=pincount) #JST part number format string

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

    # create Silkscreen
    tmp_x1=x_min+body_back_protrusion_width+configuration['silk_fab_offset']
    tmp_x2=x_max-body_back_protrusion_width-configuration['silk_fab_offset']
    pad_silk_offset = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    poly_silk_outline= [
                    {'x':-pad_size[0]/2.0-pad_silk_offset, 'y':silk_y_main_min},
                    {'x':tmp_x1, 'y':silk_y_main_min},
                    {'x':tmp_x1, 'y':silk_y_min},
                    {'x':silk_x_min, 'y':silk_y_min},
                    {'x':silk_x_min, 'y':silk_y_max},
                    {'x':silk_x_max, 'y':silk_y_max},
                    {'x':silk_x_max, 'y':silk_y_min},
                    {'x':tmp_x2, 'y':silk_y_min},
                    {'x':tmp_x2, 'y':silk_y_main_min},
                    {'x':(pincount-1)*pitch+pad_size[0]/2.0+pad_silk_offset, 'y':silk_y_main_min}
    ]
    kicad_mod.append(PolygonLine(shape=poly_silk_outline, layer='F.SilkS', width=configuration['silk_line_width']))

    if configuration['allow_silk_below_part'] == 'tht' or configuration['allow_silk_below_part'] == 'both':
        poly_big_cutout=[{'x':0.5, 'y':silk_y_max}
                                  ,{'x':0.5, 'y':2}
                                  ,{'x':x_max-2.45, 'y':2}
                                  ,{'x':x_max-2.45, 'y':silk_y_max}]
        kicad_mod.append(PolygonLine(shape=poly_big_cutout, layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Line(start=[silk_x_min, silk_y_main_min], end=[tmp_x1, silk_y_main_min], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[silk_x_max, silk_y_main_min], end=[tmp_x2, silk_y_main_min], layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Rectangle(start=[-1.3, 2.5], end=[-0.3, 4.1],
            layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Rectangle(start=[(pincount-1)*pitch+1.3, 2.5], end=[(pincount-1)*pitch+0.3, 4.1],
            layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Line(start=[-0.3, 4.1], end=[-0.3, silk_y_max],
            layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[-0.8, 4.1], end=[-0.8, silk_y_max],
            layer='F.SilkS', width=configuration['silk_line_width']))

    ########################### CrtYd ################################
    part_x_min = x_min
    part_x_max = x_max
    part_y_min = y_min
    part_y_max = y_max

    cx1 = round_to_grid(part_x_min-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(part_y_min-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(part_x_max+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(part_y_max+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ########################### Fab Outline ################################
    tmp_x1=x_min+body_back_protrusion_width
    tmp_x2=x_max-body_back_protrusion_width
    poly_fab_outline= [
                    {'x':tmp_x1, 'y':y_main_min},
                    {'x':tmp_x1, 'y':y_min},
                    {'x':x_min, 'y':y_min},
                    {'x':x_min, 'y':y_max},
                    {'x':x_max, 'y':y_max},
                    {'x':x_max, 'y':y_min},
                    {'x':tmp_x2, 'y':y_min},
                    {'x':tmp_x2, 'y':y_main_min},
                    {'x':tmp_x1, 'y':y_main_min}
    ]
    kicad_mod.append(PolygonLine(shape=poly_fab_outline, layer='F.Fab', width=configuration['fab_line_width']))

    ############################# Pads ##################################
    # kicad_mod.append(Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
    #                     at=[0, 0], size=pad_size,
    #                     drill=drill_size, layers=Pad.LAYERS_THT))

    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(PadArray(initial=1, start=[0, 0],
        x_spacing=pitch, pincount=pincount,
        size=pad_size, drill=drill_size,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
        round_radius_handler=global_config.roundrect_radius_handler,
        **optional_pad_params))


    ########################### Pin 1 marker ################################
    poly_pin1_marker = [
        {'x':0, 'y':-1.2},
        {'x':-0.4, 'y':-1.6},
        {'x':0.4, 'y':-1.6},
        {'x':0, 'y':-1.2}
    ]
    if silk_pin1_marker_type == 1:
        kicad_mod.append(PolygonLine(shape=poly_pin1_marker, layer='F.SilkS', width=configuration['silk_line_width']))
    if silk_pin1_marker_type == 2:
        silk_pin1_marker_t2_x = -pad_size[0]/2.0-pad_silk_offset

        kicad_mod.append(Line(start=[silk_pin1_marker_t2_x, silk_y_main_min],
            end=[silk_pin1_marker_t2_x, -pad_size[1]/2.0-configuration['silk_pad_clearance']],layer='F.SilkS', width=configuration['silk_line_width']))

    if fab_pin1_marker_type == 1:
        kicad_mod.append(PolygonLine(shape=poly_pin1_marker, layer='F.Fab', width=configuration['fab_line_width']))

    if fab_pin1_marker_type == 2:
        poly_pin1_marker_type2 = [
            {'x':-0.75, 'y':y_main_min},
            {'x':0, 'y':y_main_min+0.75},
            {'x':0.75, 'y':y_main_min}
        ]
        kicad_mod.append(PolygonLine(shape=poly_pin1_marker_type2, layer='F.Fab', width=configuration['fab_line_width']))

    if fab_pin1_marker_type == 3:
        fab_pin1_marker_t3_y = pad_size[1]/2.0
        poly_pin1_marker_type2 = [
            {'x':0, 'y':fab_pin1_marker_t3_y},
            {'x':-0.5, 'y':fab_pin1_marker_t3_y+0.5},
            {'x':0.5, 'y':fab_pin1_marker_t3_y+0.5},
            {'x':0, 'y':fab_pin1_marker_t3_y}
        ]
        kicad_mod.append(PolygonLine(shape=poly_pin1_marker_type2, layer='F.Fab', width=configuration['fab_line_width']))

    ######################### Text Fields ###############################
    text_center_y = 2.5
    body_edge={'left':part_x_min, 'right':part_x_max, 'top':part_y_min, 'bottom':part_y_max}
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
    for pincount in range(2,17):
        generate_one_footprint(generator_name, global_config, pincount, configuration)
        num_fps_generated += 1
    return num_fps_generated
