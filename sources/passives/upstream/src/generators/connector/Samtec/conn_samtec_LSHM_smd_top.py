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

from math import sqrt
from typing import Any
from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from kilibs.config import global_config as GC
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint

series = ""
series_long = 'LSHM 0.50 mm Razor Beam High-Speed Hermaphroditic Terminal/Socket Strip'
manufacturer = 'Samtec'
orientation = 'V'
number_of_rows = 2
datasheet = 'http://suddendocs.samtec.com/prints/lshm-1xx-xx.x-x-dv-a-x-x-tr-footprint.pdf'

#pins_per_row per row
pins_per_row_range = [5,10,20,30,40,50]

#Samtec part number
#n = number of circuits per row
part_code = "LSHM-1{n:02d}-xx.x-x-DV-{shield:s}"

variant_params = {
    'shielded': {
        'mpn_option': 'S',
        'shield_pad': True,
    },
    'plain': {
        'mpn_option': 'N',
        'shield_pad': False,
    }
}

pitch = 0.5

pad_size = [0.3, 1.5]
boss_drill = 1.45

shield_pad_drill = 1
shield_pad_size = 1.5

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins_per_row, params, configuration):

    mpn = part_code.format(n=pins_per_row, shield=params['mpn_option'])

    off = global_config.silk_fab_offset
    pad_silk_off = global_config.silk_pad_offset
    body_edge = {}
    bounding_box = {}

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    if params['shield_pad']:
        footprint_name = configuration['fp_name_format_string_shielded'].format(man=manufacturer,
            series=series,
            mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row,
            pitch=pitch, orientation=orientation_str, shield_pins=1)
    else:
        footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
            series=series,
            mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
            pitch=pitch, orientation=orientation_str)

    footprint_name = footprint_name.replace('__','_')

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription("Samtec {:s}, {:s}, {:d} Pins per row ({:s})".format(series_long, mpn, pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    A = (pins_per_row-1)*pitch
    B = A + 2.5
    C = A + 5.45
    D = A + 6.75
    E = A + 5.2

    pad_to_pad_inside = 1.95+0.25
    pad_y = (pad_to_pad_inside + pad_size[1])/2

    boss_x = B/2
    boss_y = -pad_y + pad_size[1]/2 + 0.25

    shield_pad_x = C/2
    shield_pad_y = boss_y + 2

    body_chamfer = 0.3


    body_edge['left'] = -D/2 if params['shield_pad'] else -E/2
    body_edge['right'] = -body_edge['left']
    body_edge['top'] = -4.98/2
    body_edge['bottom'] = -body_edge['top']

    bounding_box['left'] = (-shield_pad_x - shield_pad_size/2) if params['shield_pad'] else body_edge['left']
    bounding_box['right'] = -bounding_box['left']
    bounding_box['top'] = -pad_y - pad_size[1]/2
    bounding_box['bottom'] = -bounding_box['top']


    ################################ Pads #####################################

    kicad_mod.append(PadArray(initial=1, increment=2,
        center=[0, -pad_y], x_spacing=pitch, pincount=pins_per_row,
        size=pad_size, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT))
    kicad_mod.append(PadArray(initial=2, increment=2,
        center=[0, pad_y], x_spacing=pitch, pincount=pins_per_row,
        size=pad_size, type=Pad.TYPE_SMT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_SMT))

    kicad_mod.append(Pad(number ='', type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                        at=[boss_x, boss_y],
                        size=boss_drill, drill=boss_drill,
                        layers=Pad.LAYERS_NPTH))
    kicad_mod.append(Pad(number ='', type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                        at=[-boss_x, boss_y],
                        size=boss_drill, drill=boss_drill,
                        layers=Pad.LAYERS_NPTH))

    if params['shield_pad']:
        pin_number_shield = global_config.get_pad_name(GC.PadName.SHIELD)

        kicad_mod.append(Pad(number = pin_number_shield,
                            type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                            at=[shield_pad_x, shield_pad_y],
                            size=shield_pad_size, drill=shield_pad_drill,
                            layers=Pad.LAYERS_THT))
        kicad_mod.append(Pad(number = pin_number_shield,
                            type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
                            at=[-shield_pad_x, shield_pad_y],
                            size=shield_pad_size, drill=shield_pad_drill,
                            layers=Pad.LAYERS_THT))

    ########################### Outline ################################
    poly_fab = [
        {'x': 0, 'y': body_edge['top']},
        {'x': body_edge['left']+body_chamfer, 'y': body_edge['top']},
        {'x': body_edge['left'], 'y': body_edge['top']+body_chamfer},
        {'x': body_edge['left'], 'y': body_edge['bottom']-body_chamfer},
        {'x': body_edge['left']+body_chamfer, 'y': body_edge['bottom']},
        {'x': 0, 'y': body_edge['bottom']}
    ]
    kicad_mod.append(PolygonLine(shape=poly_fab,
                                 layer='F.Fab', width=global_config.fab_line_width))
    kicad_mod.append(PolygonLine(shape=poly_fab, x_mirror=0,
                                 layer='F.Fab', width=global_config.fab_line_width))

    pad_x_outside_edge = A/2 + pad_size[0]/2 + pad_silk_off
    if not params['shield_pad']:
        poly_silk = [
            {'x': -pad_x_outside_edge, 'y': body_edge['top']-off},
            {'x': body_edge['left']+body_chamfer-off, 'y': body_edge['top']-off},
            {'x': body_edge['left']-off, 'y': body_edge['top']+body_chamfer-off},
            {'x': body_edge['left']-off, 'y': body_edge['bottom']-body_chamfer+off},
            {'x': body_edge['left']+body_chamfer-off, 'y': body_edge['bottom']+off},
            {'x': -pad_x_outside_edge, 'y': body_edge['bottom']+off}
        ]
        kicad_mod.append(PolygonLine(shape=poly_silk,
                                     layer='F.SilkS', width=global_config.silk_line_width))
        kicad_mod.append(PolygonLine(shape=poly_silk, x_mirror=0,
                                     layer='F.SilkS', width=global_config.silk_line_width))

    else:
        r = (shield_pad_size/2 + pad_silk_off)
        x = (D-C)/2
        dy = sqrt(r**2 - x**2)
        poly_silk_top = [
            {'x': -pad_x_outside_edge, 'y': body_edge['top']-off},
            {'x': body_edge['left']+body_chamfer-off, 'y': body_edge['top']-off},
            {'x': body_edge['left']-off, 'y': body_edge['top']+body_chamfer-off},
            {'x': body_edge['left']-off, 'y': shield_pad_y-dy},
        ]
        kicad_mod.append(PolygonLine(shape=poly_silk_top,
                                     layer='F.SilkS', width=global_config.silk_line_width))
        kicad_mod.append(PolygonLine(shape=poly_silk_top, x_mirror=0,
                                     layer='F.SilkS', width=global_config.silk_line_width))

        poly_silk_bottom = [
            {'x': body_edge['left']-off, 'y': shield_pad_y+dy},
            {'x': body_edge['left']-off, 'y': body_edge['bottom']-body_chamfer+off},
            {'x': body_edge['left']+body_chamfer-off, 'y': body_edge['bottom']+off},
            {'x': -pad_x_outside_edge, 'y': body_edge['bottom']+off}
        ]
        kicad_mod.append(PolygonLine(shape=poly_silk_bottom,
                                     layer='F.SilkS', width=global_config.silk_line_width))
        kicad_mod.append(PolygonLine(shape=poly_silk_bottom, x_mirror=0,
                                     layer='F.SilkS', width=global_config.silk_line_width))

    ########################### Pin 1 #################################
    p1s_sl = 0.4
    p1s_y = -pad_y - pad_size[1]/2 - pad_silk_off
    p1_x = -A/2
    p1s_poly = [
        {'x': p1_x, 'y':p1s_y},
        {'x': p1_x-p1s_sl/2, 'y':p1s_y-p1s_sl/sqrt(2)},
        {'x': p1_x+p1s_sl/2, 'y':p1s_y-p1s_sl/sqrt(2)},
        {'x': p1_x, 'y':p1s_y}
    ]
    kicad_mod.append(PolygonLine(shape=p1s_poly,
                                 layer='F.SilkS', width=global_config.silk_line_width))

    p1f_sl = 2*pitch
    p1f_poly = [
        {'x': p1_x-p1f_sl/2, 'y':body_edge['top']},
        {'x': p1_x, 'y':body_edge['top']+p1f_sl/sqrt(2)},
        {'x': p1_x+p1f_sl/2, 'y':body_edge['top']}
    ]
    kicad_mod.append(PolygonLine(shape=p1f_poly,
                                 layer='F.Fab', width=global_config.fab_line_width))

    ########################### CrtYd #################################

    courtyard_offset = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)
    courtyard_grid = global_config.courtyard_grid

    cx1 = round_to_grid(bounding_box['left'] - courtyard_offset, courtyard_grid)
    cy1 = round_to_grid(bounding_box['top'] - courtyard_offset, courtyard_grid)

    cx2 = round_to_grid(bounding_box['right'] + courtyard_offset, courtyard_grid)
    cy2 = round_to_grid(bounding_box['bottom'] + courtyard_offset, courtyard_grid)

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=global_config.courtyard_line_width))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=global_config, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2},
        fp_name=footprint_name, text_y_inside_position='center')

    ##################### Output and 3d model ############################

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=global_config.model_3d_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=global_config.model_3d_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    for variant in variant_params:
        for pins_per_row in pins_per_row_range:
            generate_one_footprint(generator_name, global_config, pins_per_row, variant_params[variant], configuration)
            num_fps_generated += 1
    return num_fps_generated
