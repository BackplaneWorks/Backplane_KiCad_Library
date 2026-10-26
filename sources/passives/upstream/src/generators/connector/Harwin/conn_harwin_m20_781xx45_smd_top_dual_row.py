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
from generators.tools.footprint.footprint_text_fields import addTextFields
from kilibs.config import global_config as GC
from generators.tools.footprint.drawing_tools import getStandardSilkArrowSize, SilkArrowSize
from generators.tools.footprint.nodes import pin1_arrow
from generators.tools.footprint.save_footprint import write_footprint


def generate_footprint(generator_name: str, global_config: GC.GlobalConfig, pins, configuration):
    series = 'M20'
    series_long = 'Female Vertical Surface Mount Double Row 2.54mm (0.1 inch) Pitch PCB Connector'
    manufacturer = 'Harwin'
    datasheet = 'https://cdn.harwin.com/pdfs/M20-781.pdf'
    # https://cdn.harwin.com/pdfs/Harwin_Product_Catalog_page_225.pdf
    pn = 'M20-781{n:02}45'
    number_of_rows = 2
    orientation = 'V'

    pitch = 2.54
    peg_drill_tht = 1.02
    mount_drill = 1.8
    pad_size = [1.78, 1.02]

    mpn = pn.format(n=pins)
    pins_per_row = pins

    # handle arguments
    orientation_str = configuration['orientation_options'][orientation]
    footprint_name = configuration['fp_name_format_string'].format(man=manufacturer,
        series="",
        mpn=mpn, num_rows=number_of_rows, pins_per_row=pins_per_row, mounting_pad = "",
        pitch=pitch, orientation=orientation_str)
    footprint_name = footprint_name.replace("__", "_")

    kicad_mod = Footprint(footprint_name, FootprintType.SMD)
    kicad_mod.setDescription("Harwin {:s}, {:s}, {:d} Pins per row ({:s})".format(series_long, mpn, pins_per_row, datasheet))
    kicad_mod.setTags(configuration['keyword_fp_string'].format(series=series,
        orientation=orientation_str, man=manufacturer,
        entry=configuration['entry_direction'][orientation]))

    ########################## Dimensions ##############################

    A = 2.54 * pins
    B = 2.54 * (pins-1)
    C = B - 2.54

    body_edge={
        'left': -2.54,
        'right': 2.54,
        'top': -A/2,
        'bottom': A/2
    }

    ############################# Pads ##################################
    #
    # Mount Pegs
    #
    if pins == 2:
        kicad_mod.append(Pad(at=[0, 0], number="",
            type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=mount_drill,
            drill=mount_drill, layers=Pad.LAYERS_NPTH))
    else:
        kicad_mod.append(Pad(at=[0, -C/2], number="",
            type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=mount_drill,
            drill=mount_drill, layers=Pad.LAYERS_NPTH))
        kicad_mod.append(Pad(at=[0, C/2], number="",
            type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE, size=mount_drill,
            drill=mount_drill, layers=Pad.LAYERS_NPTH))

    for pin in range(pins):
        for x_pitch in [1.27, -1.27]:
            kicad_mod.append(Pad(at=[x_pitch, -B/2 + pin*pitch], number="",
                type=Pad.TYPE_NPTH, shape=Pad.SHAPE_CIRCLE,
                size=peg_drill_tht, drill=peg_drill_tht, layers=Pad.LAYERS_NPTH))

    #
    # Add pads
    #
    left_pads = PadArray(start=[-2.91, -B/2], initial=1,
        pincount=pins, increment=1,  y_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT, layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler)
    right_pads = PadArray(start=[2.91, -B/2], initial=pins+1,
        pincount=pins, increment=1,  y_spacing=pitch, size=pad_size,
        type=Pad.TYPE_SMT, shape=Pad.SHAPE_ROUNDRECT, layers=Pad.LAYERS_SMT,
        round_radius_handler=global_config.roundrect_radius_handler)

    kicad_mod.append(left_pads)
    kicad_mod.append(right_pads)

    ######################## Fabrication Layer ###########################
    main_body_poly= [
        {'x': body_edge['left'], 'y': body_edge['top']},
        {'x': body_edge['right'], 'y': body_edge['top']},
        {'x': body_edge['right'], 'y': body_edge['bottom']},
        {'x': body_edge['left'], 'y': body_edge['bottom']},
        {'x': body_edge['left'], 'y': body_edge['top']}
    ]
    kicad_mod.append(PolygonLine(shape=main_body_poly,
                                 width=configuration['fab_line_width'], layer="F.Fab"))

    main_arrow_poly= [
        {'x': -2.54, 'y': body_edge['top'] + 1.27 - .4},
        {'x': -1.9, 'y': body_edge['top'] + 1.27},
        {'x': -2.54, 'y': body_edge['top'] + 1.27 + .4},
    ]
    kicad_mod.append(PolygonLine(shape=main_arrow_poly,
                                 width=configuration['fab_line_width'], layer="F.Fab"))

    ######################## SilkS Layer ###########################
    poly_s_top= [
        {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['top'] - configuration['silk_fab_offset'] + .7},
        {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['top'] - configuration['silk_fab_offset']},
        {'x': body_edge['right'] + configuration['silk_fab_offset'], 'y': body_edge['top'] - configuration['silk_fab_offset']},
        {'x': body_edge['right'] + configuration['silk_fab_offset'], 'y': body_edge['top'] - configuration['silk_fab_offset'] + .7},
    ]
    kicad_mod.append(PolygonLine(shape=poly_s_top,
                                 width=configuration['silk_line_width'], layer="F.SilkS"))

    poly_s_bot= [
        {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset'] - .7},
        {'x': body_edge['left'] - configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset']},
        {'x': body_edge['right'] + configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset']},
        {'x': body_edge['right'] + configuration['silk_fab_offset'], 'y': body_edge['bottom'] + configuration['silk_fab_offset'] - .7},
    ]
    kicad_mod.append(PolygonLine(shape=poly_s_bot,
                                 width=configuration['silk_line_width'], layer="F.SilkS"))


    silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
        SilkArrowSize.LARGE, global_config.silk_line_width
    )
    apex_pos = Vector2D(
        body_edge['left'] - global_config.silk_fab_offset - silk_arrow_size,
        left_pads.get_pad_with_name(1).at[1] - pad_size[1] / 2 - global_config.silk_pad_offset
    )

    arrow = pin1_arrow.Pin1SilkscreenArrow(
        apex_position=apex_pos,
        angle=pin1_arrow.Direction.SOUTH,
        size=silk_arrow_size,
        length=silk_arrow_length,
        layer="F.SilkS",
        line_width_mm=global_config.silk_line_width,
    )
    kicad_mod.append(arrow)

    ######################## CrtYd Layer ###########################
    CrtYd_offset = configuration['courtyard_offset']['connector']
    CrtYd_grid = configuration['courtyard_grid']

    poly_yd = [
        {'x': -3.8 - CrtYd_offset, 'y': body_edge['top'] - CrtYd_offset},
        {'x': 3.8 + CrtYd_offset, 'y': body_edge['top'] - CrtYd_offset},
        {'x': 3.8 + CrtYd_offset, 'y': body_edge['bottom'] + CrtYd_offset},
        {'x': -3.8 - CrtYd_offset, 'y': body_edge['bottom'] + CrtYd_offset},
        {'x': -3.8 - CrtYd_offset, 'y': body_edge['top'] - CrtYd_offset}
    ]

    kicad_mod.append(PolygonLine(shape=poly_yd,
                                 layer='F.CrtYd', width=configuration['courtyard_line_width']))

    ######################### Text Fields ###############################
    cy1 = body_edge['top'] - configuration['courtyard_offset']['connector']
    cy2 = body_edge['bottom'] + configuration['courtyard_offset']['connector'] + 0.2

    addTextFields(kicad_mod=kicad_mod, configuration=configuration, body_edges=body_edge,
        courtyard={'top':cy1, 'bottom':cy2}, fp_name=footprint_name, text_y_inside_position='center',
        allow_rotation=True)

    ##################### Write to File and 3D ############################
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
    pincount_range = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20]
    for pincount in pincount_range:
        generate_footprint(generator_name, global_config, pincount, configuration)
        num_fps_generated += 1
    return num_fps_generated
