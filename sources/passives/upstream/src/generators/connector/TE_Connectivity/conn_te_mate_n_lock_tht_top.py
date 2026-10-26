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
from math import sqrt, asin, degrees

from KicadModTree import *
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


draw_inner_details = False

series = "MATE-N-LOK"
series_long = 'Mini-Universal MATE-N-LOK'
man_lib = 'TE-Connectivity'
man_short_fp_name = 'TE'
orientation = 'V'
datasheet = "http://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=82181_SOFTSHELL_HIGH_DENSITY&DocType=CS&DocLang=EN"

#Molex part number
#n = number of circuits per row
variant_params = {
    'in_line':{
        'pins_per_row_range': [2,3],
        'number_of_rows': 1,
        'style': 'in_line',
        'number_pegs': 1,
        'width': 5.58,
        'part_code': {
                2: '1-770866-x',
                3: '1-770870-x'
            }
        },
    'dual1':{
        'pins_per_row_range': range(2,7),
        'number_of_rows': 2,
        'style': 'dual_row',
        'number_pegs': 1,
        'width': 9.83,
        'part_code': {
                4: '1-770874-x',
                6: '1-770875-x',
                8: '1-794073-x',
                10: '1-770858-x',
                12: '1-770621-x'
            }
        },
    'dual2':{
        'pins_per_row_range': range(7,13),
        'number_of_rows': 2,
        'style': 'dual_row',
        'number_pegs': 2,
        'width': 9.83,
        'part_code': {
                14: '1-794067-x',
                16: '1-794068-x',
                18: '1-794069-x',
                20: '1-794070-x',
                22: '1-794071-x',
                24: '1-794072-x'
            }
        },
    'matrix':{
        'pins_per_row_range': [3,4,5],
        'number_of_rows': 3,
        'style': 'matrix',
        'number_pegs': 1,
        'width': 13.97,
        'part_code': {
                9: '1-770182-x',
                12: '1-770186-x',
                15: '1-770190-x'
            }
        },
}

pitch = 4.14
drill = 1.4
pad_to_pad_clearance = 1.5
max_annular_ring = 0.95
min_annular_ring = 0.15
row = 4.14

peg_drill = 3.18
peg_to_nearest_pin = 4.44


def generate_one_footprint(
    generator_name: str, global_config: GC.GlobalConfig, pins_per_row, variant_param, configuration):
    silk_pad_off = configuration['silk_pad_clearance']+configuration['silk_line_width']/2
    off = configuration['silk_fab_offset']

    number_of_rows = variant_param['number_of_rows']

    pad_size = [row - pad_to_pad_clearance, pitch - pad_to_pad_clearance]
    if number_of_rows == 1:
        pad_size[0] = drill + 2*max_annular_ring

    if pad_size[0] - drill < 2*min_annular_ring:
        pad_size[0] = drill + 2*min_annular_ring
    if pad_size[0] - drill > 2*max_annular_ring:
        pad_size[0] = drill + 2*max_annular_ring

    if pad_size[1] - drill < 2*min_annular_ring:
        pad_size[1] = drill + 2*min_annular_ring
    if pad_size[1] - drill > 2*max_annular_ring:
        pad_size[1] = drill + 2*max_annular_ring

    pad_shape = Pad.SHAPE_OVAL
    if pad_size[0] == pad_size[1]:
        pad_shape = Pad.SHAPE_CIRCLE

    first_to_last_pad_y = (pins_per_row-1)*pitch
    first_to_last_pad_x = (number_of_rows-1)*row

    peg_pos = [[0, -peg_to_nearest_pin if variant_param['style'] != 'in_line' else (first_to_last_pad_y + peg_to_nearest_pin)]]
    if variant_param['number_pegs'] == 2:
        peg_pos.append([0, first_to_last_pad_y + peg_to_nearest_pin])

    mpn = variant_param['part_code'][pins_per_row*number_of_rows].format(n=pins_per_row*2)

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=man_short_fp_name,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    descr_format_str = "Molex {:s}, old mpn/engineering number: {:s}, {:d} Pins per row ({:s})"
    kicad_mod.setDescription(descr_format_str.format(
        series_long, mpn, pins_per_row, datasheet))
    tags = configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=man_short_fp_name,
        entry=configuration['entry_direction'][orientation])
    kicad_mod.setTags(tags)

    x1 = -(variant_param['width']-first_to_last_pad_x)/2
    x2 = x1 + variant_param['width']
    body_length = (9.83-pitch)+first_to_last_pad_y
    y1 = -(body_length - first_to_last_pad_y)/2
    y2 = y1 + body_length

    peg_predrusion = 2.591 # from 3d model
    peg_d = 3.94 # from 3d model, rounded
    peg_from_body = 0.66 # from 3d model
    peg_conn_w = 1.6 # from 3d model, rounded
    stabalizer_width = 2.54 # from 3d model
    stabalizer_len = 2.591 # from 3d model
    TW = 3 # from 3d model, rounded
    TL = 1.3 # from 3d model, rounded
    BW = 1.14 # from 3d model, rounded
    BL = 0.76 # from 3d model, rounded

    #calculate fp dimensions
    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = {}
    if variant_param['style'] != 'in_line':
        bounding_box['top'] = peg_pos[0][1]-peg_drill/2
        bounding_box['left'] = body_edge['left'] - TL
        bounding_box['right'] = body_edge['right'] + BL
        if variant_param['number_pegs'] == 2:
            bounding_box['bottom'] = peg_pos[1][1]+peg_drill/2
        else:
            bounding_box['bottom'] = body_edge['bottom'] + peg_predrusion
    else:
        bounding_box['bottom'] = peg_pos[0][1]+peg_drill/2
        bounding_box['top'] = body_edge['top'] - TL
        bounding_box['left'] = body_edge['left'] - BL
        bounding_box['right'] = body_edge['right']


    #generate the pads
    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    for row_idx in range(variant_param['number_of_rows']):
        initial = row_idx*pins_per_row + 1
        kicad_mod.append(PadArray(
            pincount=pins_per_row, initial=initial, start=[row_idx*row, 0],
            y_spacing=pitch, type=Pad.TYPE_THT, shape=pad_shape,
            size=pad_size, drill=drill, layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params))

    for peg in peg_pos:
        kicad_mod.append(Pad(at=peg, type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
            size=peg_drill, drill=peg_drill, layers=Pad.LAYERS_NPTH))


    #draw the outline of the shape
    kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2],
        layer='F.Fab',width=configuration['fab_line_width']))

    dy = peg_to_nearest_pin + body_edge['top'] - off
    if dy < (peg_drill/2 + silk_pad_off):
        dx = sqrt((peg_drill/2 + silk_pad_off)**2-dy**2)
    else:
        dx = 0

    sl_poly=[
        {'x': 0, 'y': body_edge['top']-off},
        {'x': body_edge['left']-off, 'y': body_edge['top']-off},
        {'x': body_edge['left']-off, 'y': body_edge['bottom']+off},
        {'x': 0, 'y': body_edge['bottom']+off},
    ]
    sr_poly=[
        {'x': 0, 'y': body_edge['top']-off},
        {'x': body_edge['right']+off, 'y': body_edge['top']-off},
        {'x': body_edge['right']+off, 'y': body_edge['bottom']+off},
        {'x': 0, 'y': body_edge['bottom']+off},
    ]
    if variant_param['style'] == 'in_line' or variant_param['number_pegs'] == 2:
        sl_poly[3]['x']=-dx
        sr_poly[3]['x']=dx
    if variant_param['style'] != 'in_line':
        sl_poly[0]['x']=-dx
        sr_poly[0]['x']=dx

    kicad_mod.append(PolygonLine(shape=sl_poly,
                                 layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=sr_poly,
                                 layer='F.SilkS', width=configuration['silk_line_width']))

    def peg_outline(kicad_mod, center_y):
        edge = body_edge['top'] if center_y < 0 else body_edge['bottom']
        dir = -1 if center_y < 0 else 1
        sy=edge + dir*peg_from_body
        y3 = edge +dir*peg_predrusion
        kicad_mod.append(Line(
            start=[peg_conn_w/2, edge],
            end=[peg_conn_w/2, sy],
            layer='F.Fab',width=configuration['fab_line_width']
        ))
        kicad_mod.append(Line(
            start=[-peg_conn_w/2, edge],
            end=[-peg_conn_w/2, sy],
            layer='F.Fab',width=configuration['fab_line_width']
        ))
        dy = center_y - sy
        sx = sqrt((peg_d/2)**2-dy**2)
        dy2 = y3 - center_y
        ex = sqrt((peg_d/2)**2-dy2**2)
        a1 = degrees(asin(abs(dy2)/(peg_d/2)))
        a2 = degrees(asin(abs(dy)/(peg_d/2)))
        a = a1+a2
        kicad_mod.append(Line(
            start=[sx, sy], end=[-sx, sy],
            layer='F.Fab',width=configuration['fab_line_width']
        ))
        kicad_mod.append(Line(
            start=[ex, y3], end=[-ex, y3],
            layer='F.Fab',width=configuration['fab_line_width']
        ))
        kicad_mod.append(Arc(center=[0,center_y],
            start=[sx,sy], angle=dir*a,
            layer='F.Fab', width=configuration['fab_line_width']))
        kicad_mod.append(Arc(center=[0,center_y],
            start=[-sx,sy], angle=-a*dir,
            layer='F.Fab', width=configuration['fab_line_width']))
    #
    #draw the outline of the tab
    if variant_param['style'] == 'in_line':
        tab_poly = [
            {'x': -TW/2,'y': body_edge['top']},
            {'x': -TW/2,'y': body_edge['top']-TL},
            {'x': TW/2,'y': body_edge['top']-TL},
            {'x': TW/2,'y': body_edge['top']},
        ]
        kicad_mod.append(PolygonLine(shape=tab_poly,
                                     layer='F.Fab', width=configuration['fab_line_width']))
        tab_poly = [
            {'x': -TW/2-off,'y': body_edge['top']-off},
            {'x': -TW/2-off,'y': body_edge['top']-TL-off},
            {'x': TW/2+off,'y': body_edge['top']-TL-off},
            {'x': TW/2+off,'y': body_edge['top']-off},
        ]
        kicad_mod.append(PolygonLine(shape=tab_poly,
                                     layer='F.SilkS', width=configuration['silk_line_width']))
        b_poly = [
            {'x': body_edge['left'],'y': body_edge['top']},
            {'x': body_edge['left']-BL,'y': body_edge['top']},
            {'x': body_edge['left']-BL,'y': body_edge['top']+BW},
            {'x': body_edge['left'],'y': body_edge['top']+BW},
        ]
        kicad_mod.append(PolygonLine(shape=b_poly,
                                     layer='F.Fab', width=configuration['fab_line_width']))
        b_poly = [
            {'x': body_edge['left']-off,'y': body_edge['top']-off},
            {'x': body_edge['left']-BL-off,'y': body_edge['top']-off},
            {'x': body_edge['left']-BL-off,'y': body_edge['top']+BW+off},
            {'x': body_edge['left']-off,'y': body_edge['top']+BW+off},
        ]
        kicad_mod.append(PolygonLine(shape=b_poly,
                                     layer='F.SilkS', width=configuration['silk_line_width']))
        for i in range(pins_per_row):
            yc = i*pitch+pitch/2
            b_poly = [
                {'x': body_edge['left'],'y': yc - BW/2},
                {'x': body_edge['left']-BL,'y': yc - BW/2},
                {'x': body_edge['left']-BL,'y': yc + BW/2},
                {'x': body_edge['left'],'y': yc + BW/2},
            ]
            kicad_mod.append(PolygonLine(shape=b_poly,
                                         layer='F.Fab', width=configuration['fab_line_width']))
            b_poly = [
                {'x': body_edge['left']-off,'y': yc - BW/2-off},
                {'x': body_edge['left']-BL-off,'y': yc - BW/2-off},
                {'x': body_edge['left']-BL-off,'y': yc + BW/2+off},
                {'x': body_edge['left']-off,'y': yc + BW/2+off},
            ]
            kicad_mod.append(PolygonLine(shape=b_poly,
                                         layer='F.SilkS', width=configuration['silk_line_width']))
    else:
        cy = first_to_last_pad_y/2
        tab_poly = [
            {'x': body_edge['left'],'y': cy-TW/2},
            {'x': body_edge['left']-TL,'y': cy-TW/2},
            {'x': body_edge['left']-TL,'y': cy+TW/2},
            {'x': body_edge['left'],'y': cy+TW/2},
        ]
        kicad_mod.append(PolygonLine(shape=tab_poly,
                                     layer='F.Fab', width=configuration['fab_line_width']))

        tab_poly = [
            {'x': body_edge['left']-off,'y': cy-TW/2-off},
            {'x': body_edge['left']-TL-off,'y': cy-TW/2-off},
            {'x': body_edge['left']-TL-off,'y': cy+TW/2+off},
            {'x': body_edge['left']-off,'y': cy+TW/2+off},
        ]
        kicad_mod.append(PolygonLine(shape=tab_poly,
                                     layer='F.SilkS', width=configuration['silk_line_width']))

        b_poly = [
            {'x': body_edge['right'],'y': body_edge['top']},
            {'x': body_edge['right']+BL,'y': body_edge['top']},
            {'x': body_edge['right']+BL,'y': body_edge['top']+BW},
            {'x': body_edge['right'],'y': body_edge['top']+BW},
        ]
        kicad_mod.append(PolygonLine(shape=b_poly,
                                     layer='F.Fab', width=configuration['fab_line_width']))

        b_poly = [
            {'x': body_edge['right']+off,'y': body_edge['top']-off},
            {'x': body_edge['right']+BL+off,'y': body_edge['top']-off},
            {'x': body_edge['right']+BL+off,'y': body_edge['top']+BW+off},
            {'x': body_edge['right']+off,'y': body_edge['top']+BW+off},
        ]
        kicad_mod.append(PolygonLine(shape=b_poly,
                                     layer='F.SilkS', width=configuration['silk_line_width']))
        if len(peg_pos) == 1:
            center_stabalizer = (number_of_rows-1)*row
            stab_x1 = center_stabalizer - stabalizer_width/2
            stab_x2 = center_stabalizer + stabalizer_width/2
            stab_y1 = body_edge['bottom'] + stabalizer_len
            stab_poly = [
                {'x': stab_x1,'y': body_edge['bottom']},
                {'x': stab_x1,'y': stab_y1},
                {'x': stab_x2,'y': stab_y1},
                {'x': stab_x2,'y': body_edge['bottom']}
            ]
            kicad_mod.append(PolygonLine(shape=stab_poly,
                                         layer='F.Fab', width=configuration['fab_line_width']))
            stab_poly = [
                {'x': stab_x1-off,'y': body_edge['bottom']+off},
                {'x': stab_x1-off,'y': stab_y1+off},
                {'x': stab_x2+off,'y': stab_y1+off},
                {'x': stab_x2+off,'y': body_edge['bottom']+off}
            ]
            kicad_mod.append(PolygonLine(shape=stab_poly,
                                         layer='F.SilkS', width=configuration['silk_line_width']))

        for i in range(pins_per_row):
            yc = i*pitch+pitch/2
            b_poly = [
                {'x': body_edge['right'],'y': yc - BW/2},
                {'x': body_edge['right']+BL,'y': yc - BW/2},
                {'x': body_edge['right']+BL,'y': yc + BW/2},
                {'x': body_edge['right'],'y': yc + BW/2},
            ]
            kicad_mod.append(PolygonLine(shape=b_poly,
                                         layer='F.Fab', width=configuration['fab_line_width']))

            b_poly = [
                {'x': body_edge['right']+off,'y': yc - BW/2-off},
                {'x': body_edge['right']+BL+off,'y': yc - BW/2-off},
                {'x': body_edge['right']+BL+off,'y': yc + BW/2+off},
                {'x': body_edge['right']+off,'y': yc + BW/2+off},
            ]
            kicad_mod.append(PolygonLine(shape=b_poly,
                                         layer='F.SilkS', width=configuration['silk_line_width']))

    for peg in peg_pos:
        peg_outline(kicad_mod, peg[1])



    if variant_param['style'] != 'in_line':
        L = 2.5
        O = off + 0.3
        dy = peg_to_nearest_pin + body_edge['top'] - O
        if dy < (peg_drill/2 + silk_pad_off):
            dx = sqrt((peg_drill/2 + silk_pad_off)**2-dy**2)

        pin = [
            {'x': -dx,'y': body_edge['top'] - O},
            {'x': body_edge['left'] - O,'y': body_edge['top'] - O},
            {'x': body_edge['left'] - O,'y': body_edge['top'] + L}
        ]
    else:
        sl = 0.6
        xs = body_edge['left']-(off + 0.3)
        pin = [
            {'x': xs,'y': 0},
            {'x': xs - sl/sqrt(2),'y': sl/2},
            {'x': xs - sl/sqrt(2),'y': -sl/2},
            {'x': xs,'y': 0}
        ]


    kicad_mod.append(PolygonLine(shape=pin, layer="F.SilkS", width=configuration['silk_line_width']))

    sl = 2
    pin = [
        {'x': body_edge['left'],'y': -sl/2},
        {'x': body_edge['left'] +sl/sqrt(2),'y': 0},
        {'x': body_edge['left'],'y': sl/2}
    ]
    kicad_mod.append(PolygonLine(shape=pin, width=configuration['fab_line_width'], layer='F.Fab'))

    ########################### CrtYd #################################
    CrtYd_offset = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']

    cx1 = round_to_grid(bounding_box['left'] - CrtYd_offset, CrtYd_grid)
    cy1 = round_to_grid(bounding_box['top'] - CrtYd_offset, CrtYd_grid)

    cx2 = round_to_grid(bounding_box['right'] + CrtYd_offset, CrtYd_grid)
    cy2 = round_to_grid(bounding_box['bottom'] + CrtYd_offset, CrtYd_grid)

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='right')

    ##################### Output and 3d model ############################
    model3d_path_prefix = configuration.get('3d_model_prefix',global_config.model_3d_prefix)
    model3d_path_suffix = configuration.get('3d_model_suffix',global_config.model_3d_suffix)

    lib_name = configuration['lib_name_format_string'].format(series=series, man=man_lib)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=model3d_path_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=model3d_path_suffix)
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_generated_fps = 0
    for variant in variant_params:
        variant_param = variant_params[variant]
        for pins_per_row in variant_param['pins_per_row_range']:
            generate_one_footprint(generator_name, global_config, pins_per_row, variant_param, configuration)
            num_generated_fps += 1
    return num_generated_fps
