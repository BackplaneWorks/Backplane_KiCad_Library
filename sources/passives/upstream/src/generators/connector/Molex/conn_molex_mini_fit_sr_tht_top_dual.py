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

series = "Mini-Fit_Sr"
series_long = 'Mini-Fit Sr. Power Connectors'
manufacturer = 'Molex'
orientation = 'V'
number_of_rows = 2
datasheet = 'http://www.molex.com/pdm_docs/sd/439151404_sd.pdf'

#pins_per_row per row
pins_per_row_range = [3, 4, 5, 6, 7]

#Molex part number
#n = number of circuits per row
part_code = "43915-xx{n:02}"

pitch = 10
drill = 2.8

offset_second_pad = 4.4
pitch_row = offset_second_pad + 8.06

pad_to_pad_clearance = 3
max_annular_ring = 1
min_annular_ring = 0.15

#locating pins
x_loc = 8.43
r_loc = 3.0



pad_size = [offset_second_pad + 0.1, pitch - pad_to_pad_clearance]
if pad_size[1] - drill < 2*min_annular_ring:
    pad_size[1] = drill + 2*min_annular_ring
if pad_size[1] - drill > 2*max_annular_ring:
    pad_size[1] = drill + 2*max_annular_ring

version_params = {
    'with_thermals':{
        'description': ', With thermal vias in pads',
        'fp_name_suffix': '_ThermalVias',
        'thermals': True
    },
    'only_pads':{
        'description': '',
        'fp_name_suffix': '',
        'thermals': False
    }
}

def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, params, configuration):
    pad_silk_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    mpn = part_code.format(n=pins*number_of_rows)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)
    footprint_name += params['fp_name_suffix']

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    desc_format_str = "Molex {:s}, {:s}{:s}, {:d} Pins per row ({:s})"
    kicad_mod.setDescription(desc_format_str.format(series_long, mpn, params['description'], pins, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    #calculate fp dimensions
    #ref: http://www.molex.com/pdm_docs/sd/439151404_sd.pdf
    #A = distance between mounting holes
    A = pins * pitch + 1.41

    #B = distance between end pin centers
    B = (pins - 1) * pitch

    #E = length of part
    E = pins * pitch + 0.9

    #connector width
    W = 19.16

    #corner positions
    y1 = -(E-B)/2
    y2 = y1 + E

    x1 = -1.15
    x2 = x1 + W

    TL = 5
    TW = 13

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = {
        'left': -pad_size[0]/2,
        'right': pitch_row + offset_second_pad + pad_size[0]/2
    }

    pad_silk_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    #generate the pads
    for row_idx in range(2):
        for pad_idx in range(2):
            kicad_mod.append(PadArray(
                pincount=pins, start=[row_idx*pitch_row + pad_idx*offset_second_pad, 0],
                initial=row_idx*pins+1, y_spacing=pitch, size=pad_size, drill=drill,
                type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT, layers=Pad.LAYERS_THT,
                tht_pad1_shape=Pad.SHAPE_RECT))

    #thermal vias

    d_small = 0.3
    s_small = d_small + 2*min_annular_ring
    thermal_to_pad_edge = s_small/2 + 0.15

    if params['thermals']:
        for yi in range(pins):
            for xi in range(number_of_rows):
                n = xi*pins + yi + 1
                pad_center_x = xi*pitch_row + offset_second_pad/2
                pad_center_y = yi*pitch
                pad_l = offset_second_pad + pad_size[0]
                dy = (pad_size[1] - 2*thermal_to_pad_edge)/2
                dx = (pad_l - 2*thermal_to_pad_edge)/4

                #draw rectangle on F.Fab layer

                # kicad_mod.append(Rectangle(
                #     start=[pad_center_x - pad_l/2, pad_center_y - pad_size[1]/2],
                #     end=[pad_center_x + pad_l/2, pad_center_y + pad_size[1]/2],
                #     layer='F.Fab', width=configuration['fab_line_width']))

                kicad_mod.append(PadArray(center=[pad_center_x, pad_center_y],
                    pincount=3, x_spacing=dx*2,
                    drill=d_small, size=s_small, initial=n, increment=0,
                    shape=Pad.SHAPE_CIRCLE, type=Pad.TYPE_THT, layers=Pad.LAYERS_THT,
                    round_radius_handler=global_config.roundrect_radius_handler))
                kicad_mod.append(PadArray(center=[pad_center_x, pad_center_y - dy],
                    pincount=5, x_spacing=dx,
                    drill=d_small, size=s_small, initial=n, increment=0,
                    type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT,
                    round_radius_handler=global_config.roundrect_radius_handler))
                kicad_mod.append(PadArray(center=[pad_center_x, pad_center_y + dy],
                    pincount=5, x_spacing=dx,
                    drill=d_small, size=s_small, initial=n, increment=0,
                    type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_THT,
                    round_radius_handler=global_config.roundrect_radius_handler))

    # locating pins
    kicad_mod.append(Pad(at=[x_loc, 5], type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
        size=r_loc, drill=r_loc, layers=Pad.LAYERS_NPTH))
    kicad_mod.append(Pad(at=[x_loc, B/2-A/2], type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
        size=r_loc+0.5, drill=r_loc, layers=Pad.LAYERS_THT))
    kicad_mod.append(Pad(at=[x_loc, B/2+A/2], type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE,
        size=r_loc+0.5, drill=r_loc, layers=Pad.LAYERS_THT))

    #mark pin-1 (bottom layer)
    kicad_mod.append(Rectangle(start=[-pad_size[0]/2, -pad_size[1]/2],
        end=[offset_second_pad + pad_size[0]/2,pad_size[1]/2],offset=pad_silk_off,
        width=configuration['silk_line_width'], layer='B.SilkS'))

    #draw connector outline (basic)
    kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2],
        width=configuration['fab_line_width'], layer='F.Fab'))

    #connector outline on F.SilkScreen
    off = configuration['silk_line_width']
    corner = [
        {'y': -pad_size[1]/2 - pad_silk_off, 'x': x1-off},
        {'y': y1 - off, 'x': x1-off},
        {'y': y1 - off, 'x': x_loc-r_loc/2-0.5},
    ]

    # kicad_mod.append(PolygonLine(shape=corner,
    #     width=configuration['silk_line_width'], layer='F.SilkS'))
    kicad_mod.append(Line(start=[x_loc-r_loc/2-0.5, y1 - off],
        end=[x_loc-TW/2-off, y1 - off],
        width=configuration['silk_line_width'], layer='F.SilkS'))

    kicad_mod.append(PolygonLine(shape=corner, y_mirror=B / 2,
                                 width=configuration['silk_line_width'], layer='F.SilkS'))
    kicad_mod.append(PolygonLine(shape=corner, x_mirror=x_loc,
                                 width=configuration['silk_line_width'], layer='F.SilkS'))
    kicad_mod.append(PolygonLine(shape=corner, y_mirror=B / 2, x_mirror=x_loc,
                                 width=configuration['silk_line_width'], layer='F.SilkS'))

    #silk-screen between each pad

    for i in range(pins-1):
        ya = i * pitch + pad_size[1]/2 + pad_silk_off
        yb = (i+1) * pitch - pad_size[1]/2 - pad_silk_off

        kicad_mod.append(Line(start=[x1-off, ya],end=[x1-off, yb],
            width=configuration['silk_line_width'], layer='F.SilkS'))
        kicad_mod.append(Line(start=[x2+off, ya],end=[x2+off, yb],
            width=configuration['silk_line_width'], layer='F.SilkS'))

    #draw the tabs at each end
    def offsetPoly(poly_points, o , center_x, center_y):
        new_points = []
        for point in poly_points:
            new_points.append(
                {
                'y': point['y'] + (o if point['y'] > center_y else -o),
                'x': point['x'] + (o if point['x'] > center_x else -o)
                }
            )
        return new_points

    tab = [
        {'y': y1,'x': x_loc-TW/2},
        {'y': y1-TL,'x': x_loc-TW/2},
        {'y': y1-TL,'x': x_loc+TW/2},
        {'y': y1,'x': x_loc+TW/2},
    ]

    kicad_mod.append(PolygonLine(shape=tab,
                                 width=configuration['fab_line_width'], layer='F.Fab'))
    kicad_mod.append(PolygonLine(shape=tab, y_mirror=B / 2,
                                 width=configuration['fab_line_width'], layer='F.Fab'))

    tap_off = offsetPoly(tab, off, x_loc, B/2)
    kicad_mod.append(PolygonLine(shape=tap_off,
                                 width=configuration['silk_line_width'], layer='F.SilkS'))
    kicad_mod.append(PolygonLine(shape=tap_off, y_mirror=B / 2,
                                 width=configuration['silk_line_width'], layer='F.SilkS'))

    bounding_box['top'] = y1 - TL
    bounding_box['bottom'] = y2 + TL

    #inner-tab
    T = 2
    tab = [
        {'y': y1-off,'x': x_loc-TW/2-off+T},
        {'y': y1-off-TL+T,'x': x_loc-TW/2-off+T},
        {'y': y1-off-TL+T,'x': x_loc+TW/2+off-T},
        {'y': y1-off,'x': x_loc+TW/2+off-T},
    ]

    kicad_mod.append(PolygonLine(shape=tab,
                                 width=configuration['silk_line_width'], layer='F.SilkS'))
    kicad_mod.append(PolygonLine(shape=tab, y_mirror=B / 2,
                                 width=configuration['silk_line_width'], layer='F.SilkS'))

    #pin-1 marker
    x = x1 - 1.5
    m = 0.4

    pin = [
    {'x': x,'y': 0},
    {'x': x-2*m,'y': -m},
    {'x': x-2*m,'y': +m},
    {'x': x,'y': 0},
    ]

    kicad_mod.append(PolygonLine(shape=pin,
                                 width=configuration['silk_line_width'], layer='F.SilkS'))

    sl=3
    pin = [
        {'x': body_edge['left'], 'y': -sl/2},
        {'x': body_edge['left'] + sl/sqrt(2), 'y': 0},
        {'x': body_edge['left'], 'y': sl/2}
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 width=configuration['fab_line_width'], layer='F.Fab'))

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
    for version in version_params:
        for pins_per_row in pins_per_row_range:
            generate_one_footprint(generator_name, global_config, pins_per_row, version_params[version], configuration)
            num_fps_generated += 1
    return num_fps_generated
