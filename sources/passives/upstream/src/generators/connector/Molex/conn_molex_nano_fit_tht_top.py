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
from kilibs.geom import CornerSelection
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


series = "Nano-Fit"
series_long = 'Nano-Fit Power Connectors'
manufacturer = 'Molex'
orientation = 'V'

#pins_per_row per row
pins_per_row_range = range(2,9)

#Molex part number
#n = number of circuits per row


pitch = 2.5
drill = 1.2

pitch_row = 2.5

pad_to_pad_clearance = 0.8
max_annular_ring = 0.5
min_annular_ring = 0.15

version_params = {
    'dual':{
        'number_of_rows': 2,
        'datasheet': "http://www.molex.com/pdm_docs/sd/1053101208_sd.pdf",
        'mpn': "105310-xx{n:02}"
    },
    'single':{
        'number_of_rows': 1,
        'datasheet': 'http://www.molex.com/pdm_docs/sd/1053091203_sd.pdf',
        'mpn': "105309-xx{n:02}"
    }
}


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, params, configuration):
    pad_silk_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2
    mpn = params['mpn'].format(n=pins*params['number_of_rows'])

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=params['number_of_rows'], pins_per_row=pins, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    desc_format_str = "Molex {:s}, {:s}, {:d} Pins per row ({:s})"
    kicad_mod.setDescription(desc_format_str.format(series_long, mpn, pins, params['datasheet']))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    if params['number_of_rows'] == 2:
        pad_size = [pitch_row - pad_to_pad_clearance, pitch - pad_to_pad_clearance]
    else:
        pad_size = [drill + 2*max_annular_ring, pitch - pad_to_pad_clearance]

    if pad_size[1] - drill < 2*min_annular_ring:
        pad_size[1] = drill + 2*min_annular_ring
    if pad_size[1] - drill > 2*max_annular_ring:
        pad_size[1] = drill + 2*max_annular_ring

    if pad_size[0] - drill < 2*min_annular_ring:
        pad_size[0] = drill + 2*min_annular_ring
    if pad_size[0] - drill > 2*max_annular_ring:
        pad_size[0] = drill + 2*max_annular_ring

    pad_shape=Pad.SHAPE_OVAL
    if pad_size[0] == pad_size[1]:
        pad_shape=Pad.SHAPE_CIRCLE

    #A = connector length
    A = pins * pitch + 0.94

    #B = pin center distance
    B = (pins - 1) * pitch

    #W = thickness of plastic base
    W = params['number_of_rows'] * pitch_row + 0.98

    #locating pin position
    if pins in [3,5,7]:
        C = B/2 - 1.25
    else:
        C = B/2

    #corner positions for plastic housing outline
    y1 = -(A-B)/2
    y2 = y1 + A

    x2 = (params['number_of_rows'] - 1)* pitch_row+1.74
    x1 = x2 - W

    TL = 5.2
    TW = 2.86

    off = configuration['silk_fab_offset']
    pad_silk_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = body_edge.copy()

    bounding_box['left'] = body_edge['left']-TW

    pad_silk_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    # generate the pads

    if pins <= 3:
        kicad_mod.append(ChamferedPad(number=1, at=[0, 0],
            size=pad_size, drill=drill,
            type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
            chamfer_size=0.4,
            round_radius_handler=global_config.roundrect_radius_handler,
            corner_selection=CornerSelection({CornerSelection.BOTTOM_LEFT:True})
        ))

    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    for r in range(params['number_of_rows']):
        pincount = pins
        initial = r*pins+1
        start=[r*pitch_row, 0]
        if r == 0 and pins <= 3:
            pincount = pins -1
            initial = 2
            start=[0, pitch]

        kicad_mod.append(PadArray(
            pincount=pincount, initial=initial, start=start,
            y_spacing=pitch, type=Pad.TYPE_THT, shape=pad_shape,
            size=pad_size, drill=drill, layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params))

    #add the locating pin
    kicad_mod.append(Pad(at=[-1.34, C], size=1.3, drill=1.3,
        type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH))

    #add outline to F.Fab
    #kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2],layer='F.Fab'))

    #and to the silkscreen
    #and draw the tab

    def outline(off = 0, grid = 0):
        out = [
        {'y': round_to_grid(B/2, grid),
        'x': round_to_grid(x2+off, grid)},
        {'y': round_to_grid(y1-off, grid),
        'x': round_to_grid(x2+off, grid)},
        {'y': round_to_grid(y1-off, grid),
        'x': round_to_grid(x1-off, grid)},
        {'y': round_to_grid(B/2-TL/2-off, grid),
        'x': round_to_grid(x1-off, grid)},
        {'y': round_to_grid(B/2-TL/2-off, grid),
        'x': round_to_grid(x1-TW-off, grid)},
        {'y': round_to_grid(B/2, grid),
        'x': round_to_grid(x1-TW-off, grid)}
        ]

        return out

    kicad_mod.append(PolygonLine(shape=outline(), layer='F.Fab', width=configuration['fab_line_width']))
    kicad_mod.append(PolygonLine(shape=outline(), layer='F.Fab', width=configuration['fab_line_width'], y_mirror=B / 2))

    kicad_mod.append(PolygonLine(shape=outline(off = off), layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=outline(off = off), layer='F.SilkS', width=configuration['silk_line_width'], y_mirror=B / 2))

    CrtYd_off = configuration['courtyard_offset']['connector']
    kicad_mod.append(PolygonLine(
        shape=outline(off = CrtYd_off, grid=configuration['courtyard_grid']),
        layer='F.CrtYd', width=configuration['courtyard_line_width']))
    kicad_mod.append(PolygonLine(
        shape=outline(off = CrtYd_off, grid=configuration['courtyard_grid']),
        layer='F.CrtYd', width=configuration['courtyard_line_width'], y_mirror=B/2))

    # draw the tab
    kicad_mod.append(Rectangle(start=[x1+2*off, B/2-TL/2],end=[x1-TW, B/2+TL/2],
        offset=-0.5, width=configuration['fab_line_width'], layer='F.Fab'))

    #draw the pins!
    # o = 0.475 * pitch
    # for i in range(pins):
    #     for j in range(params['number_of_rows']):
    #         y = i * pitch
    #         x = j * pitch
    #
    #         kicad_mod.append(Rectangle(start=[x-o,y-o],end=[x+o,y+o], layer='F.Fab', width=configuration['fab_line_width']))

    #pin-1 marker
    p1m_off = configuration['silk_fab_offset'] + 0.3
    p1m_b = B/2-TL/2 - off
    if p1m_b > 0:
        p1m_b = 0

    pin = [
    {'x': 0,'y': body_edge['top'] - p1m_off},
    {'x': body_edge['left'] - p1m_off,'y': body_edge['top'] - p1m_off},
    {'x': body_edge['left'] - p1m_off,'y': p1m_b}
    ]

    kicad_mod.append(PolygonLine(shape=pin, layer='F.SilkS', width=configuration['silk_line_width']))

    sl=1
    pin = [
        {'y': body_edge['top'], 'x': -sl/2},
        {'y': body_edge['top'] + sl/sqrt(2), 'x': 0},
        {'y': body_edge['top'], 'x': sl/2}
    ]
    kicad_mod.append(PolygonLine(shape=pin,
                                 width=configuration['fab_line_width'], layer='F.Fab'))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':bounding_box['top'] - CrtYd_off, 'bottom':bounding_box['bottom'] + CrtYd_off}, fp_name=footprint_name, text_y_inside_position='right')

    ##################### Output and 3d model ############################
    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=global_config.model_3d_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=global_config.model_3d_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    for version in version_params:
        for pins_per_row in pins_per_row_range:
            generate_one_footprint(
                generator_name, global_config, pins_per_row, version_params[version], configuration
            )
            num_fps_generated += 1
    return num_fps_generated
