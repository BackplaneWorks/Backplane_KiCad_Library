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
from kilibs.geom import Direction, Vector2D
from KicadModTree import (
    Arc,
    Model,
    Pad,
    PadArray,
    Footprint,
    FootprintType,
    PolygonLine,
    Stadium,
    Line,
)
from kilibs.config import global_config as GC
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.drawing_tools_fab import draw_pin1_chevron_on_hline
from generators.tools.footprint.drawing_tools_silk import (
    draw_silk_triangle45_clear_of_fab_hline_and_pad,
    SilkArrowSize,
)
from generators.tools.footprint.save_footprint import write_footprint


def roundToBase(value, base):
    if base == 0:
        return value
    return round(value/base) * base

def generate_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, configuration):
    series = 'Gecko'
    series_long = 'Male Vertical Surface Mount Double Row 1.25mm (0.049 inch) Pitch PCB Connector'
    manufacturer = 'Harwin'
    datasheet = 'https://cdn.harwin.com/pdfs/G125-MS1XX05M2P.pdf'
    pn = 'G125-MS1{n:02}05M2P'
    number_of_rows = 2
    orientation = 'V'

    pitch = 1.25
    mount_drill = 2.25
    mount_pad = 4.4
    pad_size = Vector2D(0.7,2.5)
    
    mpn = pn.format(n=pins)
    pins_per_row = int(pins / 2)

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series=series,
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.description = "Harwin {:s}, {:s}, {:d} Pins per row ({:s})".format(
        series_long, mpn, pins_per_row, datasheet
    )
    kicad_mod.tags = configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation])

    ########################## Dimensions ##############################

    x_body = pitch * (pins_per_row - 1) + 12.7
    x_pins = pitch * (pins_per_row - 1)
    y_body = 4.9
    y_max_pin_extent = 5.8
    mount_spacing = pitch * (pins_per_row - 1) + 7.8

    body_edge={
        'top': -y_body / 2,
        'bottom': y_body / 2,
        'left': -x_body / 2,
        'right': x_body / 2
    }

    ############################# Pads ##################################
    #
    # Mounting holes
    #
    mounting_pad_name = global_config.get_pad_name(GC.PadName.MECHANICAL)

    kicad_mod.append(Pad(at=[-mount_spacing/2, 0], number=mounting_pad_name,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=mount_pad,
        drill=mount_drill, layers=Pad.LAYERS_THT))
    kicad_mod.append(Pad(at=[mount_spacing/2, 0], number=mounting_pad_name,
        type=Pad.TYPE_THT, shape=Pad.SHAPE_CIRCLE, size=mount_pad,
        drill=mount_drill, layers=Pad.LAYERS_THT))

    #
    # Add pads
    #
    odd_pads = PadArray(start=[-x_pins/2, 1.85], initial=1,
        pincount=pins_per_row, increment=1,  x_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT, layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler)
    even_pads = PadArray(start=[-x_pins/2, -1.85], initial=pins_per_row+1,
        pincount=pins_per_row, increment=1,  x_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT, layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler)

    kicad_mod.append(odd_pads)
    kicad_mod.append(even_pads)

    ######################## Fabrication Layer ###########################

    fab_body = Stadium(
        center_1=Vector2D(-mount_spacing / 2, 0),
        center_2=Vector2D(mount_spacing / 2, 0),
        radius=y_body / 2,
        width=global_config.fab_line_width,
        layer="F.Fab",
    )
    kicad_mod.append(fab_body)

    kicad_mod.append(
        draw_pin1_chevron_on_hline(
            line_y=y_body / 2,
            apex_x=-x_pins / 2,
            global_config=global_config,
            direction=Direction.NORTH,
        )
    )

    ######################## SilkS Layer ###########################

    # Endcaps
    silk_rad = y_body / 2 + global_config.silk_fab_offset
    kicad_mod.append(
        Arc(
            start=Vector2D(-mount_spacing / 2, silk_rad),
            end=Vector2D(-mount_spacing / 2, -silk_rad),
            mid=Vector2D(-mount_spacing / 2 - silk_rad, 0),
            width=global_config.silk_line_width,
            layer="F.SilkS",
        )
    )

    kicad_mod.append(
        Arc(
            start=Vector2D(mount_spacing / 2, silk_rad),
            end=Vector2D(mount_spacing / 2, -silk_rad),
            mid=Vector2D(mount_spacing / 2 + silk_rad, 0),
            width=global_config.silk_line_width,
            layer="F.SilkS",
        )
    )

    for y in [-1, 1]:
        for x in [-1, 1]:

            inner_x = x * (x_pins / 2 + pad_size.x / 2 + global_config.silk_pad_offset)

            if y == 1 and x == -1:
                inner_x -= 1.3

            kicad_mod.append(
                Line(
                    start=(
                        inner_x,
                        y * (y_body / 2) + global_config.silk_fab_offset * y,
                    ),
                    end=(
                        x * mount_spacing / 2,
                        y * (y_body / 2) + global_config.silk_fab_offset * y,
                    ),
                    width=global_config.silk_line_width,
                    layer="F.SilkS",
                )
            )

    kicad_mod.append(
        draw_silk_triangle45_clear_of_fab_hline_and_pad(
            global_config=global_config,
            pad=odd_pads.get_pad_with_name(1),
            arrow_direction=Direction.NORTHEAST,
            line_y=y_body / 2,
            line_clearance_y=global_config.silk_fab_offset,
            arrow_size=SilkArrowSize.LARGE,
        )
    )

    ######################## CrtYd Layer ###########################
    CrtYd_offset = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)
    CrtYd_grid = global_config.courtyard_grid

    poly_yd = [
        {'y': roundToBase(-(y_max_pin_extent/2) - CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid)},
        {'y': roundToBase((y_max_pin_extent/2) + CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid)},
        {'y': roundToBase((y_max_pin_extent/2) + CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['right'] + CrtYd_offset, CrtYd_grid)},
        {'y': roundToBase(-(y_max_pin_extent/2) - CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['right'] + CrtYd_offset, CrtYd_grid)},
        {'y': roundToBase(-(y_max_pin_extent/2) - CrtYd_offset, CrtYd_grid), 'x': roundToBase(body_edge['left'] - CrtYd_offset, CrtYd_grid)}
    ]

    kicad_mod.append(PolygonLine(shape=poly_yd,
        layer='F.CrtYd', width=global_config.courtyard_line_width))

    ######################### Text Fields ###############################
    cy1 = body_edge['top'] - CrtYd_offset - 0.4
    cy2 = body_edge['bottom'] + CrtYd_offset + 0.4

    addTextFields(kicad_mod=kicad_mod, configuration=global_config, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center')

    ##################### Write to File ############################

    lib_name = configuration['lib_name_format_string'].format(series=series, man=manufacturer)

    kicad_mod.append(Model(filename=f"{global_config.model_3d_prefix}{lib_name}.3dshapes/{footprint_name}{global_config.model_3d_suffix}"))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    pincount_range = [6, 10, 12, 16, 20, 26, 34, 50]
    num_fps_generated = 0
    for pincount in pincount_range:
        generate_footprint(generator_name, global_config, pincount, configuration)
        num_fps_generated += 1
    return num_fps_generated
