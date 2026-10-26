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

from kilibs.geom import Direction, CornerSelection
from KicadModTree import *
from KicadModTree import ChamferedRectangle
from generators.tools.footprint.footprint_text_fields import addTextFields
from kilibs.config import global_config as GC
from generators.tools.footprint.drawing_tools_silk import draw_silk_triangle_for_pad, SilkArrowSize
from generators.tools.footprint.save_footprint import write_footprint


def roundToBase(value, base):
    if base == 0:
        return value
    return round(value/base) * base

def gen_fab_pins(origx, origy, kicad_mod, global_config: GC.GlobalConfig):
    poly_f_back = [
        {'x': origx+3.8, 'y': origy-0.64/2},
        {'x': origx-0.9, 'y': origy-0.64/2},
        {'x': origx-0.9, 'y': origy+0.64/2},
        {'x': origx+3.8, 'y': origy+0.64/2},
    ]
    poly_f_front = [
        {'x': origx+6.3, 'y': origy-0.64/2},
        {'x': origx+12.3, 'y': origy-0.64/2},
        {'x': origx+12.3, 'y': origy+0.64/2},
        {'x': origx+6.3, 'y': origy+0.64/2},
    ]
    kicad_mod.append(PolygonLine(shape=poly_f_back,
                                 width=global_config.fab_line_width, layer="F.Fab"))
    kicad_mod.append(PolygonLine(shape=poly_f_front,
                                 width=global_config.fab_line_width, layer="F.Fab"))

def gen_silk_pins(origx, origy, kicad_mod, global_config: GC.GlobalConfig, fill: bool):

    poly_s_back1 = [
        {'x': origx+2.5/2+global_config.silk_pad_clearance+global_config.silk_line_width, 'y': origy-0.64/2-global_config.silk_line_width},
        {'x': origx+3.8-global_config.silk_line_width, 'y': origy-0.64/2-global_config.silk_line_width},
    ]
    poly_s_back2 = [
        {'x': origx+2.5/2+global_config.silk_pad_clearance+global_config.silk_line_width, 'y': origy+0.64/2+global_config.silk_line_width},
        {'x': origx+3.8-global_config.silk_line_width, 'y': origy+0.64/2+global_config.silk_line_width},
    ]
    poly_s_front = [
        {'x': origx+6.3+global_config.silk_line_width, 'y': origy-0.64/2-global_config.silk_line_width},
        {'x': origx+12.3+global_config.silk_line_width, 'y': origy-0.64/2-global_config.silk_line_width},
        {'x': origx+12.3+global_config.silk_line_width, 'y': origy+0.64/2+global_config.silk_line_width},
        {'x': origx+6.3+global_config.silk_line_width, 'y': origy+0.64/2+global_config.silk_line_width},
    ]
    kicad_mod.append(PolygonLine(shape=poly_s_back1,
                                 width=global_config.silk_line_width, layer="F.SilkS"))
    kicad_mod.append(PolygonLine(shape=poly_s_back2,
                                 width=global_config.silk_line_width, layer="F.SilkS"))

    if not fill:
        kicad_mod.append(
            PolygonLine(
                shape=poly_s_front,
                width=global_config.silk_line_width,
                layer="F.SilkS",
            )
        )
    else:
        rect_c = Vector2D(origx+global_config.silk_line_width+(6.3+12.3)/2, origy)
        rect_size = Vector2D(6, 0.64+global_config.silk_line_width  *2 )
        kicad_mod.append(
            Rectangle(
                start=rect_c - rect_size / 2,
                end=rect_c + rect_size / 2,
                layer="F.SilkS",
                width=global_config.silk_line_width,
                fill=True,
            )
        )

def gen_footprint(generator_name: str, global_config: GC.GlobalConfig, pinnum, manpart, configuration):

    series = 'M20-890'
    series_long = 'Male Horizontal Surface Mount Single Row 2.54mm (0.1 inch) Pitch PCB Connector'
    manufacturer = 'Harwin'
    pitch = 2.54
    datasheet = 'https://cdn.harwin.com/pdfs/M20-890.pdf'
    padsize = [2.5, 1]

    orientation_str = configuration['orientation_options']['H']
    footprint_name = configuration['fp_name_format_string'].format(
        man=manufacturer,
        series='',
        mpn=manpart,
        num_rows=1,
        pins_per_row=pinnum,
        mounting_pad="",
        pitch=pitch,
        orientation=orientation_str)
    
    footprint_name = footprint_name.replace('__','_')

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription("{manufacturer} {series}, {mpn}{alt_mpn}, {pins_per_row} Pins per row ({datasheet})".format(
        manufacturer = manufacturer,
        series = series_long,
        mpn = manpart,
        alt_mpn = '',
        pins_per_row = pinnum,
        datasheet = datasheet))

    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry='horizontal'))

    # Pads
    pads = PadArray(start=[-6.775+padsize[0]/2, -(pitch*(pinnum-1))/2], initial=1,
        pincount=pinnum, increment=1,  y_spacing=pitch, size=padsize,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT, layers=Pad.LAYERS_SMT, drill=None,
        round_radius_handler=global_config.roundrect_radius_handler)
    kicad_mod.append(pads)

    # Fab
    for y in range(0, pinnum):
        gen_fab_pins(-6.775+padsize[0]/2, -(pitch*(pinnum-1))/2+pitch+(y-1)*2.54, kicad_mod, global_config)

    body_c = Vector2D(-6.775 + padsize[0] / 2 + (3.8 + 6.3) / 2, 0)
    body_size = Vector2D(6.3 - 3.8, pitch * (pinnum - 1) + 2.54)

    body_rect = ChamferedRectangle(
        center=body_c,
        size=body_size,
        layer="F.Fab",
        width=global_config.fab_line_width,
        chamfer=global_config.fab_bevel,
        corners=CornerSelection(
            {CornerSelection.TOP_LEFT: True}
        ),
        fill=False,
    )
    kicad_mod.append(body_rect)

    # SilkS
    silkslw = global_config.silk_line_width
    s_body = [
        {'x': -6.775+padsize[0]/2+3.8-silkslw, 'y': -(pitch*(pinnum-1))/2-pitch-2.54/2-silkslw+2.54},
        {'x': -6.775+padsize[0]/2+6.3+silkslw, 'y': -(pitch*(pinnum-1))/2-pitch-2.54/2-silkslw+2.54},
        {'x': -6.775+padsize[0]/2+6.3+silkslw, 'y': -(pitch*(pinnum-1))/2-pitch-2.54/2+2.54*pinnum+silkslw+2.54},
        {'x': -6.775+padsize[0]/2+3.8-silkslw, 'y': -(pitch*(pinnum-1))/2-pitch-2.54/2+2.54*pinnum+silkslw+2.54},
        {'x': -6.775+padsize[0]/2+3.8-silkslw, 'y': -(pitch*(pinnum-1))/2-pitch-2.54/2-silkslw+2.54},
    ]
    kicad_mod.append(PolygonLine(shape=s_body,
                                 width=global_config.silk_line_width, layer="F.SilkS"))
    for y in range(0, pinnum):
        gen_silk_pins(-6.775+padsize[0]/2, -(pitch*(pinnum-1))/2+pitch+(y-1)*2.54, kicad_mod, global_config, y==0)

    pin1_arrow = draw_silk_triangle_for_pad(
        arrow_direction=Direction.SOUTH,
        pad=pads.get_pad_with_name(1),
        stroke_width=global_config.silk_line_width,
        pad_silk_offset=global_config.silk_pad_offset,
        arrow_size=SilkArrowSize.LARGE,
    )
    kicad_mod.append(pin1_arrow)

    # CrtYd
    cy_offset = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)
    cy_grid = global_config.courtyard_grid
    bounding_box={
        'left': -6.775+padsize[0]/2-2.5/2,
        'right': -6.775+padsize[0]/2+12.3,
        'top': -(pitch*(pinnum-1))/2-pitch-2.54/2+2.54,
        'bottom': -(pitch*(pinnum-1))/2-pitch-2.54/2+2.54*pinnum+2.54,
    }
    cy_top = roundToBase(bounding_box['top'] - cy_offset, cy_grid)
    cy_bottom = roundToBase(bounding_box['bottom'] + cy_offset, cy_grid)
    cy_left = roundToBase(bounding_box['left'] - cy_offset, cy_grid)
    cy_right = roundToBase(bounding_box['right'] + cy_offset, cy_grid)
    poly_cy = [
        {'x': cy_left, 'y': cy_top},
        {'x': cy_right, 'y': cy_top},
        {'x': cy_right, 'y': cy_bottom},
        {'x': cy_left, 'y': cy_bottom},
        {'x': cy_left, 'y': cy_top},
    ]
    kicad_mod.append(PolygonLine(shape=poly_cy,
                                 layer='F.CrtYd', width=global_config.courtyard_line_width))

    # Text Fields
    body_edge={
        'left': -6.775+padsize[0]/2+3.8,
        'right': -6.775+padsize[0]/2+6.3,
        'top': -(pitch*(pinnum-1))/2-pitch-2.54/2-silkslw+2.54,
        'bottom': -(pitch*(pinnum-1))/2-pitch-2.54/2+2.54*pinnum+silkslw+2.54,
    }
    addTextFields(kicad_mod=kicad_mod, configuration=global_config, body_edges=body_edge,
        courtyard={'top':cy_top, 'bottom':cy_bottom}, fp_name=footprint_name,
        text_y_inside_position='center', allow_rotation=True)

    # 3D model
    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)
    model_name = '{model3d_path_prefix:s}{lib_name:s}.3dshapes/{fp_name:s}{model3d_path_suffix:s}'.format(
        model3d_path_prefix=global_config.model_3d_prefix, lib_name=lib_name, fp_name=footprint_name,
        model3d_path_suffix=global_config.model_3d_suffix)
    kicad_mod.append(Model(filename=model_name))

    # Output
    write_footprint(kicad_mod, lib_name, generator_name)


def gen_family(generator_name: str, global_config: GC.GlobalConfig, configuration) -> int:
    pin_min = 3
    pin_max = 20
    mpn = 'M20-890{pincount:02g}xx'
    num_fps_generated = 0
    for x in range(pin_min, pin_max+1):
        gen_footprint(generator_name, global_config, x, mpn.format(pincount=x), configuration)
        num_fps_generated += 1
    return num_fps_generated
