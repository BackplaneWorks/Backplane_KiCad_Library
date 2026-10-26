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

draw_inner_details = False

series = "Mini-Fit_Jr"
series_long = 'Mini-Fit Jr. Power Connectors'
manufacturer = 'Molex'
orientation = 'V'
number_of_rows = 2


#pins_per_row_per_row per row
pins_per_row_range = range(1,13)

#Molex part number
#n = number of circuits per row
variant_params = {
    'peg':{
        'mount_pins': 'plastic_peg',
        'descriptive_name': 'Snap-in Plastic Peg PCB Lock',
        'datasheet': 'http://www.molex.com/pdm_docs/sd/039289068_sd.pdf',
        'part_code': {'mpn':"39-28-9{n:02d}x",'eng_num':"5566-{n:02}A2"},
        },
    'no-peg':{
        'mount_pins': '',
        'descriptive_name': '',
        'datasheet': 'http://www.molex.com/pdm_docs/sd/039281043_sd.pdf',
        'part_code': {'mpn':"39-28-x{n:02d}x",'eng_num':"5566-{n:02}A"},
        }
}

pitch = 4.2
drill = 1.4
start_pos_x = 0 # Where should pin 1 be located.
pad_to_pad_clearance = 1.5
max_annular_ring = 0.95
min_annular_ring = 0.15


row = 5.5

pad_size = [pitch - pad_to_pad_clearance, row - pad_to_pad_clearance]
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


def generate_one_footprint(generator_name: str, global_config: GC.GlobalConfig, pins_per_row, variant, configuration):
    peg = variant_params[variant]['mount_pins'] == 'plastic_peg'

    silk_pad_off = configuration['silk_pad_clearance']+configuration['silk_line_width']/2

    mpn = variant_params[variant]['part_code']['mpn'].format(n=pins_per_row*2)
    old_mpn = variant_params[variant]['part_code']['eng_num'].format(n=pins_per_row*2)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=old_mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    descr_format_str = "Molex {:s}, old mpn/engineering number: {:s}, example for new mpn: {:s}, {:d} Pins per row, Mounting: {:s} ({:s})"
    kicad_mod.setDescription(descr_format_str.format(
        series_long, old_mpn, mpn, pins_per_row,
        variant_params[variant]['descriptive_name'], variant_params[variant]['datasheet']))
    tags = configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation])
    tags += variant_params[variant]['mount_pins']
    kicad_mod.setTags(tags)


    #calculate fp dimensions

    #connector length
    A = pins_per_row * pitch + 1.2

    #pin centers
    B = (pins_per_row - 1) * pitch

    #plasic pin-lock
    C = A + 4

    #connector width
    W = 9.6

    #corner positions
    x1 = -(A-B)/2
    x2 = x1 + A

    y2 = row + 1.85
    y1 = y2 - W

    #tab length
    tab_l = 3.4
    #tab width
    tab_w = 1.4

    body_edge={
        'left':x1,
        'right':x2,
        'bottom':y2,
        'top': y1
        }
    bounding_box = body_edge.copy()
    bounding_box['bottom'] = body_edge['bottom'] + tab_w

    off = configuration['silk_fab_offset']

    #generate the pads
    optional_pad_params = {}
    optional_pad_params['tht_pad1_shape'] = Pad.SHAPE_ROUNDRECT

    for row_idx in range(2):
        kicad_mod.append(PadArray(
            pincount=pins_per_row, initial=row_idx*pins_per_row+1,
            start=[0, row_idx*row], x_spacing=pitch,
            type=Pad.TYPE_THT, shape=pad_shape,
            size=pad_size, drill=drill, layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params))

    #add PCB locators if needed
    pad_silk_offset = configuration['silk_pad_clearance']+configuration['silk_line_width']/2
    if peg:
        loc = 3.00
        mounting_pin_y = row - 0.46
        lx1 = B/2-C/2
        lx2 = B/2+C/2
        kicad_mod.append(Pad(at=[lx1, mounting_pin_y],type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=loc,drill=loc, layers=Pad.LAYERS_NPTH))
        kicad_mod.append(Pad(at=[lx2, mounting_pin_y],type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=loc,drill=loc, layers=Pad.LAYERS_NPTH))

        bounding_box['left'] = lx1-loc/2
        bounding_box['right'] = lx2+loc/2
        ######################## Fab ############################
        mount_pin_radius = loc/2

        kicad_mod.append(Arc(center=[lx1,mounting_pin_y],
            start=[lx1,mounting_pin_y+mount_pin_radius], angle=180,
            layer='F.Fab', width=configuration['fab_line_width']))

        kicad_mod.append(Line(start=[lx1,mounting_pin_y-mount_pin_radius],
            end=[x1,mounting_pin_y-mount_pin_radius],
            layer='F.Fab', width=configuration['fab_line_width']))
        kicad_mod.append(Line(start=[lx1,mounting_pin_y+mount_pin_radius],
            end=[x1,mounting_pin_y+mount_pin_radius],
            layer='F.Fab', width=configuration['fab_line_width']))


        kicad_mod.append(Arc(center=[lx2,mounting_pin_y],
            start=[lx2,mounting_pin_y-mount_pin_radius], angle=180,
            layer='F.Fab', width=configuration['fab_line_width']))

        kicad_mod.append(Line(start=[lx2,mounting_pin_y-mount_pin_radius],
            end=[x2,mounting_pin_y-mount_pin_radius],
            layer='F.Fab', width=configuration['fab_line_width']))
        kicad_mod.append(Line(start=[lx2,mounting_pin_y+mount_pin_radius],
            end=[x2,mounting_pin_y+mount_pin_radius],
            layer='F.Fab', width=configuration['fab_line_width']))

        ######################## Silk ############################
        mount_pin_radius = loc/2 + silk_pad_off
        kicad_mod.append(Arc(center=[lx1,mounting_pin_y],
            start=[lx1,mounting_pin_y+mount_pin_radius], angle=180,
            layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Line(start=[lx1,mounting_pin_y-mount_pin_radius],
            end=[x1-off,mounting_pin_y-mount_pin_radius],
            layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[lx1,mounting_pin_y+mount_pin_radius],
            end=[x1-off,mounting_pin_y+mount_pin_radius],
            layer='F.SilkS', width=configuration['silk_line_width']))


        kicad_mod.append(Arc(center=[lx2,mounting_pin_y],
            start=[lx2,mounting_pin_y-mount_pin_radius], angle=180,
            layer='F.SilkS', width=configuration['silk_line_width']))

        kicad_mod.append(Line(start=[lx2,mounting_pin_y-mount_pin_radius],
            end=[x2+off,mounting_pin_y-mount_pin_radius],
            layer='F.SilkS', width=configuration['silk_line_width']))
        kicad_mod.append(Line(start=[lx2,mounting_pin_y+mount_pin_radius],
            end=[x2+off,mounting_pin_y+mount_pin_radius],
            layer='F.SilkS', width=configuration['silk_line_width']))

    #draw the outline of the shape
    kicad_mod.append(Rectangle(start=[x1,y1],end=[x2,y2],layer='F.Fab',width=configuration['fab_line_width']))

    #draw the outline of the tab
    kicad_mod.append(PolygonLine(shape=[
        {'x': B/2 - tab_l/2,'y': y2},
        {'x': B/2 - tab_l/2,'y': y2 + tab_w},
        {'x': B/2 + tab_l/2,'y': y2 + tab_w},
        {'x': B/2 + tab_l/2,'y': y2},
    ], layer='F.Fab', width=configuration['fab_line_width']))

    #draw the outline of each pin slot (alternating shapes)
    #slot size
    S = 3.3

    def square_slot(x,y):
        kicad_mod.append(Rectangle(start=[x-S/2,y-S/2], end=[x+S/2,y+S/2],
            layer='F.Fab', width=configuration['fab_line_width']))

    def notch_slot(x,y):
        kicad_mod.append(PolygonLine(shape=[
        {'x': x-S/2, 'y': y+S/2},
        {'x': x-S/2, 'y': y-S/4},
        {'x': x-S/4, 'y': y-S/2},
        {'x': x+S/4, 'y': y-S/2},
        {'x': x+S/2, 'y': y-S/4},
        {'x': x+S/2, 'y': y+S/2},
        {'x': x-S/2, 'y': y+S/2},
        ], layer='F.Fab', width=configuration['fab_line_width']))

    q = 1
    notch = True
    for i in range(pins_per_row):
        if notch:
            y_square = row/2 - 4.2/2
            y_notch = row/2 + 4.2/2
        else:
            y_square = row/2 + 4.2/2
            y_notch = row/2 - 4.2/2

        square_slot(i * pitch, y_square)
        notch_slot(i*pitch, y_notch)

        q -= 1

        if (q == 0):
            q = 2
            notch = not notch


    #draw the outline of the connector on the silkscreen
    outline = [
    {'x': B/2,'y': y1-off},
    {'x': x1-off,'y': y1-off},
    {'x': x1-off,'y': y2+off},
    {'x': B/2 - tab_l/2 - off,'y': y2+off},
    {'x': B/2 - tab_l/2 - off,'y': y2 + off + tab_w},
    {'x': B/2, 'y': y2 + off + tab_w},
    ]

    kicad_mod.append(PolygonLine(shape=outline, layer="F.SilkS", width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=outline, x_mirror=B / 2, layer="F.SilkS", width=configuration['silk_line_width']))

    #pin-1 marker

    L = 2.5
    O = 0.35

    pin = [
        {'x': x1 + L,'y': y1 - O},
        {'x': x1 - O,'y': y1 - O},
        {'x': x1 - O,'y': y1 + L},
    ]

    kicad_mod.append(PolygonLine(shape=pin, layer="F.SilkS", width=configuration['silk_line_width']))
    kicad_mod.append(PolygonLine(shape=pin, width=configuration['fab_line_width'], layer='F.Fab'))

    ########################### CrtYd #################################
    CrtYd_offset = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']

    cx1 = round_to_grid(bounding_box['left'] - CrtYd_offset, CrtYd_grid)
    cy1 = round_to_grid(bounding_box['top'] - CrtYd_offset, CrtYd_grid)

    cx2 = round_to_grid(bounding_box['right'] + CrtYd_offset, CrtYd_grid)
    cy2 = round_to_grid(bounding_box['bottom'] + CrtYd_offset, CrtYd_grid)


    if peg:
        cx3 = round_to_grid(body_edge['left']-configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
        cx4 = round_to_grid(body_edge['right']+configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])
        mount_pin_radius = loc/2
        cy3=round_to_grid(mounting_pin_y - mount_pin_radius - configuration['courtyard_offset']['connector'], configuration['courtyard_grid'])

        poly_crtyd = [
            {'x': cx3, 'y': cy1},
            {'x': cx3, 'y': cy3},
            {'x': cx1, 'y': cy3},
            {'x': cx1, 'y': cy2},
            {'x': cx2, 'y': cy2},
            {'x': cx2, 'y': cy3},
            {'x': cx4, 'y': cy3},
            {'x': cx4, 'y': cy1},
            {'x': cx3, 'y': cy1}
        ]
        kicad_mod.append(PolygonLine(shape=poly_crtyd,
                                     layer='F.CrtYd', width=configuration['courtyard_line_width']))
    else:
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
    for variant in variant_params:
        for pins_per_row in pins_per_row_range:
            generate_one_footprint(generator_name, global_config, pins_per_row, variant, configuration)
            num_fps_generated += 1
    return num_fps_generated
