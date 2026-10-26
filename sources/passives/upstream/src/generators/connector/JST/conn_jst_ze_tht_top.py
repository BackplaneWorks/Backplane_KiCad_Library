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
from kilibs.geom import CornerSelection
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC


series = "ZE"
manufacturer = 'JST'
orientation = 'V'
number_of_rows = 1
datasheet = 'http://www.jst-mfg.com/product/pdf/eng/eZE.pdf'

# ZE connector, top-entry THT, NO BOSS

pitch = 1.5
y_spacing = 2.0

drill = 0.75 # 0.7 +0.1/-0.0 -> 0.75 +/-0.05
mh_drill = 0.85

pad_size = [1.4, 1.75] # Measurements from freecad sketch (pad to pad clearance > 0.8 for a 45° trace.)

variant_parameters = {
    '1D': {
        'boss':True,
        'pin_range':range(2,17),
        'descr_str':', with boss'
        },
    'D': {
        'boss':False,
        'pin_range':range(3,17),
        'descr_str':''
        }
}
def generate_one_footprint(
    generator_name: str, global_config: GC.GlobalConfig, pincount, variant, configuration
):
    mpn = "B{pincount:02}B-ZESK-{suff}".format(pincount=pincount,suff=variant)
    boss = variant_parameters[variant]['boss']

    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pincount, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription("JST {:s} series connector, {:s}{:s} ({:s})"\
        .format(series, mpn, variant_parameters[variant]['descr_str'], datasheet))

    tags = configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation])
    if boss:
        tags += ' boss'
    kicad_mod.setTags(tags)

    #dimensions
    A = (pincount - 1) * 1.5
    B = A + 4.5

    #outline
    x1 = -1.55 - 0.7
    x2 = x1 + B

    xMid = x1 + B/2

    y2 = 0.65
    y1 = y2 - 5.75
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

    # create odd numbered pads
    # createNumberedPadsTHT(kicad_mod, ceil(pincount/2), pitch * 2, drill, {'x':dia, 'y':dia},  increment=2)
    # special treatment for pin 1 (rectangular pad alone would reduce the clearance too much)
    kicad_mod.append(ChamferedPad(number=1, at=[0, 0],
        size=pad_size, drill=drill,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT,
        chamfer_size=0.4,
        round_radius_handler=global_config.roundrect_radius_handler,
        corner_selection=CornerSelection({CornerSelection.TOP_RIGHT:True})
    ))

    if pincount > 2:
        kicad_mod.append(PadArray(initial=3, start=[2*pitch, 0],
            x_spacing=pitch*2, pincount=ceil(pincount/2)-1,
            size=pad_size, drill=drill, increment=2,
            type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT))

    #create even numbered pads
    # createNumberedPadsTHT(kicad_mod, floor(pincount/2), pitch * 2, drill, {'x':dia, 'y':dia}, starting=2, increment=2, y_off=y_spacing, x_off=pitch)
    kicad_mod.append(PadArray(initial=2, start=[pitch, -y_spacing],
        x_spacing=pitch*2, pincount=floor(pincount/2),
        size=pad_size, drill=drill, increment=2,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_OVAL, layers=Pad.LAYERS_THT))

    #expand the outline a little bit
    out = configuration['silk_fab_offset']
    x1 -= out
    x2 += out
    y1 -= out
    y2 += out

    silk_pad_offset = configuration['silk_line_width']/2 + configuration['silk_pad_clearance']
    if y2 > (pad_size[1]/2 + silk_pad_offset):
        kicad_mod.append(Rectangle(start={'x':x1,'y':y1}, end={'x':x2,'y':y2},
            width=configuration['silk_line_width'], layer="F.SilkS"))
    else:
        num_odd_pins = ceil(pincount/2)
        pos_last_odd_pad = (num_odd_pins-1) * 2*pitch
        poly_silk = [
            {'x': -(pad_size[0]/2 + silk_pad_offset), 'y': y2},
            {'x': x1, 'y': y2},
            {'x': x1, 'y': y1},
            {'x': x2, 'y': y1},
            {'x': x2, 'y': y2},
            {'x': pos_last_odd_pad + (pad_size[0]/2 + silk_pad_offset), 'y': y2},
        ]
        kicad_mod.append(PolygonLine(shape=poly_silk,
                                     width=configuration['silk_line_width'], layer="F.SilkS"))
        for i in range(num_odd_pins-1):
            kicad_mod.append(Line(start=[i * 2*pitch + (pad_size[0]/2 + silk_pad_offset), y2],
                end=[(i+1) * 2*pitch - (pad_size[0]/2 + silk_pad_offset), y2],
                width=configuration['silk_line_width'], layer="F.SilkS"))


    #add mounting hole (only for the -1D option which has the boss)
    if boss:
        #     kicad_mod.append(MountingHole(
        #     {'x': -1.65, 'y': -3.8},
        #     1.1
        # )
        kicad_mod.append(Pad(at={'x': -1.65, 'y': -3.8}, type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, layers=Pad.LAYERS_NPTH,
            drill=mh_drill, size=mh_drill))

    #thickness t of sidewalls
    t = 0.8
    xa = xMid - A/2 - 0.25 + out
    xb = xMid + A/2 + 0.25 - out
    y3 = y1 + 1.7

    q = 0.4 #inner rect offset

    #outer rect
    kicad_mod.append(Rectangle(
        start={'x': xa,'y': y1},
        end={'x': xb,'y': y3},
        width=configuration['silk_line_width'], layer="F.SilkS"
        ))

    #inner rect
    kicad_mod.append(Rectangle(
        start={'x': xa+q,'y': y1+q},
        end={'x': xb-q,'y': y3-q},
        width=configuration['silk_line_width'], layer="F.SilkS"
        ))

    #left side
    if not boss:
        kicad_mod.append(PolygonLine(shape=[
            {'x': xa,'y': y3},
            {'x': x1+t,'y':y3},
            {'x': x1+t,'y':y2-t},
            {'x': -1,'y':y2-t},
        ], width=configuration['silk_line_width'], layer="F.SilkS"))
    else: #boss were declared
        kicad_mod.append(Line(
            start={'x': xa,'y': y3},
            end={'x': -0.9,'y': y3},
            width=configuration['silk_line_width'], layer="F.SilkS"
            ))

        kicad_mod.append(PolygonLine(shape=[
            {'x': x1+t,'y': -3},
            {'x': x1+t,'y': y2-t},
            {'x': -1,'y': y2-t},
        ], width=configuration['silk_line_width'], layer="F.SilkS"))
    #right side

    if pincount %2 == 0: #even number of pins
        xEnd = (pincount / 2 - 1) * (2 * pitch) + 1
    else:
        xEnd = floor(pincount / 2) * (2 * pitch) + 1

    kicad_mod.append(PolygonLine(shape=[
        {'x': xb,'y': y3},
        {'x': x2-t,'y': y3},
        {'x': x2-t,'y': y2-t},
        {'x': xEnd,'y': y2-t},
    ], width=configuration['silk_line_width'], layer="F.SilkS"))

    #draw lines between pads
    for i in range(0, ceil(pincount/2) - 1):

        X1 = i * 2 * pitch + pad_size[1]/2 + silk_pad_offset
        X2 = (i + 1) * 2 * pitch - (pad_size[1]/2 + silk_pad_offset)
        kicad_mod.append(Line(
            start={'x': X1,'y': y2-t},
            end={'x': X2,'y': y2-t},
            width=configuration['silk_line_width'], layer='F.SilkS'))

    #draw the 'vertical' lines where the actual pinny bits go

    #width of each slot w
    w = 0.15
    #clearance distance d
    d = 0.3
    # for i in range(pincount):
    #
    #     x = i * pitch
    #
    #     Y1 = y3 + d
    #     Y2 = -pad_size[1]/2 - d
    #
    #     kicad_mod.append(Rectangle(start={'x':x-w, 'y': Y1},
    #     end={'x':x+w, 'y': Y2},
    #     width=configuration['fab_line_width'], layer='F.Fab'))

    # add pin-1 marking above the pin1

    d = 0.3
    l = 1.5
    xp1 = x1 - d
    xp2 = xp1 + l

    yp2 = y2 + d
    yp1 = yp2 - l

    pin1 = [
        {'x': xp1,'y': yp1},
        {'x': xp1,'y': yp2},
        {'x': xp2,'y': yp2},
    ]

    kicad_mod.append(PolygonLine(shape=pin1, width=configuration['silk_line_width'], layer='F.SilkS'))
    kicad_mod.append(PolygonLine(shape=pin1, layer='F.Fab', width=configuration['fab_line_width']))

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
    for variant in variant_parameters:
        for pincount in variant_parameters[variant]['pin_range']:
            generate_one_footprint(generator_name, global_config, pincount, variant, configuration)
            num_fps_generated += 1
    return num_fps_generated
