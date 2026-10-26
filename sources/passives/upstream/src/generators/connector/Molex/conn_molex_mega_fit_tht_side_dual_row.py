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


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins_per_row, configuration):

    series = "Mega-Fit"
    series_long = 'Mega-Fit Power Connectors'
    manufacturer = 'Molex'
    orientation = 'H'
    number_of_rows = 2
    datasheet = 'http://www.molex.com/pdm_docs/sd/1720640002_sd.pdf'

    #Molex part number
    #n = number of circuits per row
    part_code = "76825-00{n:02d}"

    alternative_codes = [
    "172064-00{n:02d}",
    "172064-10{n:02d}"
    ]

    pitch = 5.7
    drill = 1.8
    start_pos_x = 0 # Where should pin 1 be located.
    pad_to_pad_clearance = 1.75
    max_annular_ring = 0.95 #How much copper should be in y direction?
    min_annular_ring = 0.15


    row = 5.5

    size = row - pad_to_pad_clearance
    if size - drill < 2*min_annular_ring:
        size = drill + 2*min_annular_ring
    if size - drill > max_annular_ring:
        size = drill + 2*max_annular_ring



    mpn = part_code.format(n=pins_per_row*2)
    alt_mpn = [code.format(n=pins_per_row*2) for code in alternative_codes]

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("Molex {:s}, {:s} (compatible alternatives: {:s}), {:d} Pins per row ({:s})".format(series_long, mpn, ', '.join(alt_mpn), pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    #calculate fp dimensions
    #http://www.molex.com/pdm_docs/sd/768250010_sd.pdf

    #connector length
    if pins_per_row == 1:
        A = 8.35
    else:
        A = pins_per_row * pitch + 0.65

    if pins_per_row == 1 or pins_per_row == 2:
        B = 0
    else:
        B = A - 6.35

    #pin centers
    P = (pins_per_row - 1) * pitch

    #corner positions for plastic housing outline

    x1 = -(A-P)/2
    x2 = x1 + A

    y2 = -1.1
    y1 = y2 - 14.8

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }

    #generate the pads
    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    for row_idx in range(2):
        kicad_mod.append(PadArray(
            pincount=pins_per_row, initial=row_idx*pins_per_row+1,
            start=[0, row_idx*row], x_spacing=pitch, type=Pad.TYPE_THT,
            shape=Pad.SHAPE_CIRCLE, size=size, drill=drill, layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params))

    off = configuration['silk_fab_offset']
    silk_pad_off = configuration['silk_pad_clearance'] + configuration['silk_line_width']/2

    #add PCB locators
    r_loc = 3.00
    y_loc = -7.3

    #two locators
    if pins_per_row > 2:
        lx1 = P/2 - B/2
        lx2 = P/2 + B/2

        kicad_mod.append(Pad(at=[lx1, y_loc],type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=r_loc,drill=r_loc, layers=Pad.LAYERS_NPTH))
        kicad_mod.append(Pad(at=[lx2, y_loc],type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=r_loc,drill=r_loc, layers=Pad.LAYERS_NPTH))

        kicad_mod.append(Circle(center=[lx1, y_loc],radius=r_loc/2+silk_pad_off, layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Circle(center=[lx2, y_loc],radius=r_loc/2+silk_pad_off, layer='F.SilkS', width=configuration['silk_line_width']))
    else:
        #one locator
        kicad_mod.append(Pad(at=[P/2,y_loc],type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=r_loc, drill=r_loc, layers=Pad.LAYERS_NPTH))

        kicad_mod.append(Circle(center=[P/2,y_loc], radius=r_loc/2+silk_pad_off, layer='F.SilkS', width=configuration['silk_line_width']))

    #draw the outline of the shape
    kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2], layer='F.Fab', width=configuration['fab_line_width']))

    outline = [
    {'x': P/2,'y': y1-off},
    {'x': x1-off,'y': y1-off},
    {'x': x1-off,'y': y2+off},
    {'x': -size/2 - silk_pad_off,'y': y2+off},
    ]

    kicad_mod.append(PolygonLine(shape=outline, layer='F.SilkS', width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=outline, x_mirror=P / 2 if P != 0 else 0.00000001, layer='F.SilkS', width=configuration['silk_line_width']))

    #draw lines between each pin
    for i in range(pins_per_row-1):
        xa = i * pitch + size / 2 + silk_pad_off
        xb = (i+1) * pitch - size / 2 - silk_pad_off

        kicad_mod.append(Line(start=[xa,y2+off],end=[xb,y2+off], layer='F.SilkS', width=configuration['silk_line_width']))

    #draw the pins!

    o = size/2 + silk_pad_off
    w = 0.3
    for i in range(pins_per_row):
        x = i * pitch
        ya = o
        yb = row - o
        kicad_mod.append(Line(start=[x-w,ya],end=[x-w,yb], layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[x+w,ya],end=[x+w,yb], layer='F.SilkS', width=configuration['silk_line_width']))

    #pin-1 marker
    x =  -2.5
    m = 0.3

    pin = [
    {'x': x,'y': 0},
    {'x': x-2*m,'y': +m},
    {'x': x-2*m,'y': -m},
    {'x': x,'y': 0},
    ]

    kicad_mod.append(PolygonLine(shape=pin, layer='F.SilkS', width=configuration['silk_line_width']))

    sl = 2
    pin = [
        {'x': -sl/2, 'y': body_edge['bottom']},
        {'x': 0, 'y': body_edge['bottom']-sl/sqrt(2)},
        {'x': sl/2, 'y': body_edge['bottom']},
    ]
    kicad_mod.append(PolygonLine(shape=pin, width=configuration['fab_line_width'], layer='F.Fab'))

    ########################### CrtYd #################################
    cx1 = round_to_grid(body_edge['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy1 = round_to_grid(body_edge['top']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    cx2 = round_to_grid(body_edge['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
    cy2 = round_to_grid(row + size/2 + configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

    kicad_mod.append(Rectangle(
        start=[cx1, cy1], end=[cx2, cy2],
        layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='top')

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
    pins_per_row_range = [1, 2, 3, 4, 5, 6]
    for pins_per_row in pins_per_row_range:
        generate_one_footprint(generator_name, global_config, pins_per_row, configuration)
        num_fps_generated += 1
    return num_fps_generated
