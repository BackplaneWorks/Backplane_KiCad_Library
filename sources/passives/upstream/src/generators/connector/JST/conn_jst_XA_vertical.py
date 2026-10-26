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
from generators.tools.footprint.drawing_tools import round_to_grid
from generators.tools.footprint.footprint_text_fields import addTextFields
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC

series = "XA"
manufacturer = "JST"
orientation = "V"
number_of_rows = 1
datasheet = "https://www.jst.com/wp-content/uploads/2021/01/eXA1.pdf"

# Note : this script should cover both standard and "N type" variants. Apparently the N type only uses a different platic:
# https://jsttac.blogspot.com/2011/08/what-is-difference-in-xa-series-header.html

fab_pin1_marker_type = 1
pin1_marker_offset = 0.3
pin1_marker_linelen = 1.25

drill_size = 0.95  # Datasheet: 0.9 +0.1/-0
mh_drill = 1.25  # for boss, ds: 1.2 +0.1/-0
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5  # How much copper should be in y direction?
min_annular_ring = 0.15


pitch = 2.5

# as of 2020 : available in 2- to 15-pin, 18 and 20-pin variants.
# Note : availability of 18/20-pin depends on type of plastic resin i.e. regular part # vs "N type" !
# e.g. B18B-XASK-1N exists, but not B18B-XASK-1.
# e.g. B20B-XASK-1 exists, but not B20B-XASK-1N.
pincounts = [*range(2, 15 + 1), 18, 20]

variant_parameters = {
    "1-A": {
        "boss": True,
        "pin_range": [count for count in pincounts if count != 18],
        "descr_str": ", with boss",
    },
    "1": {"boss": False, "pin_range": pincounts, "descr_str": ""},
}


def generate_one_footprint(
    generator_name: str, global_config: GC.GlobalConfig, pincount, variant, configuration
):
    mpn = "B{pincount:02}B-XASK-{suff}".format(pincount=pincount, suff=variant)
    boss = variant_parameters[variant]["boss"]

    A = (pincount - 1) * pitch
    B = A + 5
    x_min = (A - B) / 2
    y_max = 3.2
    y_min = y_max - 6.4

    silk_x_min = x_min - global_config.silk_fab_offset
    silk_y_min = y_min - global_config.silk_fab_offset
    silk_y_max = y_max + global_config.silk_fab_offset

    x_mid = A / 2
    x_max = (A + B) / 2
    silk_x_max = x_max + global_config.silk_fab_offset

    # Through-hole type shrouded header, Top entry type
    orientation_str = configuration["orientation_options"][orientation]
    footprint_name = configuration["fp_name_format_string"].format(
        man=manufacturer,
        series=series,
        mpn=mpn,
        num_rows=number_of_rows,
        pins_per_row=pincount,
        mounting_pad="",
        pitch=pitch,
        orientation=orientation_str,
    )

    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(
        "JST {:s} series connector, {:s} ({:s})".format(
            series, mpn, datasheet
        )
    )
    tags = configuration["keyword_fp_string"].format(
        series=series,
        orientation=orientation_str,
        man=manufacturer,
        entry=configuration["entry_direction"][orientation],
    )
    if boss:
        tags += " boss"
    kicad_mod.setTags(tags)

    ########################### Silkscreen ###########################
    if pincount == 2:
        bump = 0.8
        recess = 3.2
    elif pincount == 3:
        bump = 1.6
        recess = 4.8
    else:
        bump = 1.6
        recess = 5.4

    silk_ext_outline = [
        {"x": silk_x_min, "y": silk_y_min},
        {"x": silk_x_min, "y": silk_y_max},
        {"x": silk_x_max, "y": silk_y_max},
        {"x": silk_x_max, "y": silk_y_min},
        {"x": x_mid + recess / 2, "y": silk_y_min},
        {"x": x_mid + recess / 2, "y": silk_y_min + 1},
        {"x": x_mid + bump / 2, "y": silk_y_min + 1},
        {"x": x_mid + bump / 2, "y": silk_y_min + 0.4},
        {"x": x_mid - bump / 2, "y": silk_y_min + 0.4},
        {"x": x_mid - bump / 2, "y": silk_y_min + 1},
        {"x": x_mid - recess / 2, "y": silk_y_min + 1},
        {"x": x_mid - recess / 2, "y": silk_y_min},
        {"x": silk_x_min, "y": silk_y_min},
    ]

    if pincount >= 6:
        side = 2.3
        mid = 2.1
        silk_ext_outline[4:4] = [
            {"x": silk_x_max - side, "y": silk_y_min},
            {"x": silk_x_max - side, "y": silk_y_min + 1},
            {"x": x_mid + recess / 2 + mid, "y": silk_y_min + 1},
            {"x": x_mid + recess / 2 + mid, "y": silk_y_min},
        ]
        silk_ext_outline[-1:-1] = [
            {"x": x_mid - recess / 2 - mid, "y": silk_y_min},
            {"x": x_mid - recess / 2 - mid, "y": silk_y_min + 1},
            {"x": silk_x_min + side, "y": silk_y_min + 1},
            {"x": silk_x_min + side, "y": silk_y_min},
        ]

    kicad_mod.append(
        PolygonLine(
            shape=silk_ext_outline,
            layer="F.SilkS",
            width=global_config.silk_line_width,
        )
    )

    silk_inner_left = (A - B) / 2 + 0.9  # 0.9 = shroud thickness
    silk_inner_right = (A + B) / 2 - 0.9

    if (
        configuration["allow_silk_below_part"] == "tht"
        or configuration["allow_silk_below_part"] == "both"
    ):
        if boss:
            poly_silk_inner_outline = [
                {"x": silk_inner_left, "y": 0.6},
                {"x": silk_inner_left, "y": -1.7},
                {"x": silk_inner_right, "y": -1.7},
                {"x": silk_inner_right, "y": 2.6},
                {"x": silk_inner_left, "y": 2.6},
            ]
            kicad_mod.append(
                PolygonLine(
                    shape=poly_silk_inner_outline,
                    layer="F.SilkS",
                    width=global_config.silk_line_width,
                )
            )
        else:
            poly_silk_inner_outline = [
                {"x": silk_inner_left, "y": -1.7},
                {"x": silk_inner_left, "y": 2.6},
                {"x": silk_inner_right, "y": 2.6},
                {"x": silk_inner_right, "y": -1.7},
                {"x": silk_inner_left, "y": -1.7},
            ]
            kicad_mod.append(
                PolygonLine(
                    shape=poly_silk_inner_outline,
                    layer="F.SilkS",
                    width=global_config.silk_line_width,
                )
            )

        # cut in short sides
        kicad_mod.append(
            Line(
                start=[silk_x_min, y_max - 3.2],
                end=[silk_inner_left, y_max - 3.2],
                layer="F.SilkS",
                width=global_config.silk_line_width,
            )
        )
        kicad_mod.append(
            Line(
                start=[silk_x_max, y_max - 3.2],
                end=[silk_inner_right, y_max - 3.2],
                layer="F.SilkS",
                width=global_config.silk_line_width,
            )
        )

    ########################### Pin 1 marker ################################
    poly_pin1_marker = [
        {
            "x": silk_x_min - pin1_marker_offset + pin1_marker_linelen,
            "y": silk_y_min - pin1_marker_offset,
        },
        {"x": silk_x_min - pin1_marker_offset, "y": silk_y_min - pin1_marker_offset},
        {
            "x": silk_x_min - pin1_marker_offset,
            "y": silk_y_min - pin1_marker_offset + pin1_marker_linelen,
        },
    ]
    kicad_mod.append(
        PolygonLine(
            shape=poly_pin1_marker,
            layer="F.SilkS",
            width=global_config.silk_line_width,
        )
    )
    if fab_pin1_marker_type == 1:
        kicad_mod.append(
            PolygonLine(
                shape=poly_pin1_marker,
                layer="F.Fab",
                width=global_config.fab_line_width,
            )
        )

    if fab_pin1_marker_type == 2:
        poly_pin1_marker_type2 = [
            {"x": -1, "y": y_min},
            {"x": 0, "y": y_min + 1},
            {"x": 1, "y": y_min},
        ]
        kicad_mod.append(
            PolygonLine(
                shape=poly_pin1_marker_type2,
                layer="F.Fab",
                width=global_config.fab_line_width,
            )
        )

    ########################## Fab Outline ###############################
    kicad_mod.append(
        Rectangle(
            start=[x_min, y_min],
            end=[x_max, y_max],
            layer="F.Fab",
            width=global_config.fab_line_width,
        )
    )
    ############################# CrtYd ##################################
    part_x_min = x_min
    part_x_max = x_max
    part_y_min = y_min
    part_y_max = y_max

    cx1 = round_to_grid(
        part_x_min
        - global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR),
        global_config.courtyard_grid,
    )
    cy1 = round_to_grid(
        part_y_min
        - global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR),
        global_config.courtyard_grid,
    )

    cx2 = round_to_grid(
        part_x_max
        + global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR),
        global_config.courtyard_grid,
    )
    cy2 = round_to_grid(
        part_y_max
        + global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR),
        global_config.courtyard_grid,
    )

    kicad_mod.append(
        Rectangle(
            start=[cx1, cy1],
            end=[cx2, cy2],
            layer="F.CrtYd",
            width=global_config.courtyard_line_width,
        )
    )

    ############################# Pads ##################################
    pad_size = [
        pitch - pad_to_pad_clearance,
        drill_size + 2 * pad_copper_y_solder_length,
    ]
    if pad_size[0] - drill_size < 2 * min_annular_ring:
        pad_size[0] = drill_size + 2 * min_annular_ring

    optional_pad_params = {}
    optional_pad_params["tht_pad1_shape"] = Pad.SHAPE_ROUNDRECT

    kicad_mod.append(
        PadArray(
            initial=1,
            start=[0, 0],
            x_spacing=pitch,
            pincount=pincount,
            size=pad_size,
            drill=drill_size,
            type=Pad.TYPE_THT,
            shape=Pad.SHAPE_OVAL,
            layers=Pad.LAYERS_THT,
            round_radius_handler=global_config.roundrect_radius_handler,
            **optional_pad_params,
        )
    )

    # add NPTH for boss
    if boss:
        kicad_mod.append(
            Pad(
                at={"x": -1.6, "y": 1.6},
                type=Pad.TYPE_NPTH,
                shape=Pad.SHAPE_CIRCLE,
                layers=Pad.LAYERS_NPTH,
                drill=mh_drill,
                size=mh_drill,
            )
        )

    ######################### Text Fields ###############################
    text_center_y = 1.5
    body_edge = {
        "left": part_x_min,
        "right": part_x_max,
        "top": part_y_min,
        "bottom": part_y_max,
    }
    addTextFields(
        kicad_mod=kicad_mod,
        configuration=configuration,
        body_edges=body_edge,
        courtyard={"top": cy1, "bottom": cy2},
        fp_name=footprint_name,
        text_y_inside_position=text_center_y,
    )

    model3d_path_prefix = configuration.get(
        "3d_model_prefix", global_config.model_3d_prefix
    )
    model3d_path_suffix = configuration.get(
        "3d_model_suffix", global_config.model_3d_suffix
    )

    lib_name = configuration["lib_name_format_string"].format(
        series=series, man=manufacturer
    )
    model_name = f"{model3d_path_prefix}{lib_name}.3dshapes/{footprint_name}{model3d_path_suffix}"
    kicad_mod.append(Model(filename=model_name))

    write_footprint(kicad_mod, lib_name, generator_name)


def generate_all(generator_name: str, global_config: GC.GlobalConfig, configuration: dict[str, Any]) -> int:
    num_fps_generated = 0
    for variant in variant_parameters:
        for pincount in variant_parameters[variant]["pin_range"]:
            generate_one_footprint(generator_name, global_config, pincount, variant, configuration)
            num_fps_generated += 1
    return num_fps_generated
