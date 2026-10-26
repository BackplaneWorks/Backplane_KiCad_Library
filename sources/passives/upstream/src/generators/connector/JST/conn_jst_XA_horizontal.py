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
from KicadModTree.util.courtyard_builder import CourtyardBuilder

series = "XA"
manufacturer = "JST"
orientation = "H"
number_of_rows = 1
datasheet = "https://www.jst.com/wp-content/uploads/2021/01/eXA1.pdf"


silk_pin1_marker_type = 1
fab_pin1_marker_type = 3


pitch = 2.5
drill_size = 0.95  # Datasheet: 0.9 +0.1/-0
pad_to_pad_clearance = 0.8
pad_copper_y_solder_length = 0.5  # How much copper should be in y direction?
min_annular_ring = 0.15

hook_size = [2.8, 2]  # oval hole

# Connector Parameters
y_max = 9.2
y_min = y_max - 12.6
y_main_min = y_max - 9.7  # plastic body extent behind row of pins

body_back_protrusion_width = 1

variant_parameters = {
    "1": {"hook": True, "descr_str": ", with hook"},
    "1N-BN": {"hook": False, "descr_str": ""},
}


def generate_one_footprint(
    generator_name: str, global_config: GC.GlobalConfig, pincount, variant, configuration
):
    A = (pincount - 1) * pitch
    B = A + 5
    x_min = (A - B) / 2
    x_mid = A / 2
    x_max = x_min + B

    silk_x_min = x_min - global_config.silk_fab_offset
    silk_y_min = y_min - global_config.silk_fab_offset
    silk_y_main_min = y_main_min - global_config.silk_fab_offset
    silk_y_max = y_max + global_config.silk_fab_offset
    silk_x_max = x_max + global_config.silk_fab_offset

    pad_size = [
        pitch - pad_to_pad_clearance,
        drill_size + 2 * pad_copper_y_solder_length,
    ]
    if pad_size[0] - drill_size < 2 * min_annular_ring:
        pad_size[0] = drill_size + 2 * min_annular_ring

    # Through-hole type shrouded header, Side entry type
    mpn = "S{n:02}B-XASK-{suff}".format(n=pincount, suff=variant)
    hook = variant_parameters[variant]["hook"]

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
    if hook:
        tags += " hook"
    kicad_mod.setTags(tags)

    ########################### Silkscreen ################################
    tmp_x1 = x_min + body_back_protrusion_width + global_config.silk_fab_offset
    tmp_x2 = x_max - body_back_protrusion_width - global_config.silk_fab_offset
    pad_silk_offset = (
        global_config.silk_pad_clearance + global_config.silk_line_width / 2
    )
    poly_silk_outline = [
        {"x": -pad_size[0] / 2.0 - pad_silk_offset, "y": silk_y_main_min},
        {"x": tmp_x1, "y": silk_y_main_min},
        {"x": tmp_x1, "y": silk_y_min},
        {"x": silk_x_min, "y": silk_y_min},
        {"x": silk_x_min, "y": silk_y_max},
        {"x": silk_x_max, "y": silk_y_max},
        {"x": silk_x_max, "y": silk_y_min},
        {"x": tmp_x2, "y": silk_y_min},
        {"x": tmp_x2, "y": silk_y_main_min},
        {
            "x": (pincount - 1) * pitch + pad_size[0] / 2.0 + pad_silk_offset,
            "y": silk_y_main_min,
        },
    ]
    kicad_mod.append(
        PolygonLine(
            shape=poly_silk_outline,
            layer="F.SilkS",
            width=global_config.silk_line_width,
        )
    )

    if (
        configuration["allow_silk_below_part"] == "tht"
        or configuration["allow_silk_below_part"] == "both"
    ):
        if hook:
            poly_big_cutout = [
                {"x": x_min + 1, "y": silk_y_max},
                {"x": x_min + 1, "y": silk_y_max - 2.3},
                {"x": (x_mid) - 1.6, "y": silk_y_max - 2.3},
            ]
            kicad_mod.append(
                PolygonLine(
                    shape=poly_big_cutout,
                    layer="F.SilkS",
                    width=global_config.silk_line_width,
                )
            )
            poly_big_cutout = [
                {"x": (x_mid) + 1.6, "y": silk_y_max - 2.3},
                {"x": x_max - 1, "y": silk_y_max - 2.3},
                {"x": x_max - 1, "y": silk_y_max},
            ]
        else:
            poly_big_cutout = [
                {"x": x_min + 1, "y": silk_y_max},
                {"x": x_min + 1, "y": silk_y_max - 2.3},
                {"x": x_max - 1, "y": silk_y_max - 2.3},
                {"x": x_max - 1, "y": silk_y_max},
            ]
        kicad_mod.append(
            PolygonLine(
                shape=poly_big_cutout,
                layer="F.SilkS",
                width=global_config.silk_line_width,
            )
        )

        # locking "dimple", centered
        if pincount == 2:
            dimple_w = 0.8
        else:
            dimple_w = 1.6
        dimple_h = 1.8
        dimple_y = y_max - 4.9  # middle of the dimple
        kicad_mod.append(
            Rectangle(
                start=[(A - dimple_w) / 2, dimple_y + dimple_h / 2],
                end=[(A + dimple_w) / 2, dimple_y - dimple_h / 2],
                layer="F.SilkS",
                width=global_config.silk_line_width,
            )
        )

        # top
        if pincount == 2:
            recess = 3.2
        elif pincount == 3:
            recess = 4.8
        else:
            recess = 5.4
        mid = 2.1
        cutout = 1.1
        wall = (mid - cutout) / 2
        polygons = [
            [
                {"x": x_mid + recess / 2, "y": silk_y_max - 2.3},
                {"x": x_mid + recess / 2, "y": 2},
                {"x": x_mid + recess / 2 + wall, "y": 2},
                {"x": x_mid + recess / 2 + wall, "y": silk_y_max - 3.9},
                {"x": x_mid + recess / 2 + wall + cutout, "y": silk_y_max - 3.9},
                {"x": x_mid + recess / 2 + wall + cutout, "y": 2},
                {"x": silk_x_max, "y": 2},
            ],
            [
                {"x": x_mid - recess / 2, "y": silk_y_max - 2.3},
                {"x": x_mid - recess / 2, "y": 2},
                {"x": x_mid - recess / 2 - wall, "y": 2},
                {"x": x_mid - recess / 2 - wall, "y": silk_y_max - 3.9},
                {"x": x_mid - recess / 2 - wall - cutout, "y": silk_y_max - 3.9},
                {"x": x_mid - recess / 2 - wall - cutout, "y": 2},
                {"x": silk_x_min, "y": 2},
            ],
        ]
        if pincount >= 6:
            side = 2.3
            polygons[0][-1:] = [
                {"x": x_mid + recess / 2 + mid, "y": 2},
                {"x": x_mid + recess / 2 + mid, "y": silk_y_max - 2.3},
            ]
            polygons[1][-1:] = [
                {"x": x_mid - recess / 2 - mid, "y": 2},
                {"x": x_mid - recess / 2 - mid, "y": silk_y_max - 2.3},
            ]
            polygons.append(
                [
                    {"x": x_max - side, "y": silk_y_max - 2.3},
                    {"x": x_max - side, "y": 2},
                    {"x": silk_x_max, "y": 2},
                ]
            )
            polygons.append(
                [
                    {"x": x_min + side, "y": silk_y_max - 2.3},
                    {"x": x_min + side, "y": 2},
                    {"x": silk_x_min, "y": 2},
                ]
            )
        for poly in polygons:
            kicad_mod.append(
                PolygonLine(
                    shape=poly,
                    layer="F.SilkS",
                    width=global_config.silk_line_width,
                )
            )

    ########################### Fab Outline ################################
    tmp_x1 = x_min + body_back_protrusion_width
    tmp_x2 = x_max - body_back_protrusion_width
    poly_fab_outline = [
        {"x": tmp_x1, "y": y_main_min},
        {"x": tmp_x1, "y": y_min},
        {"x": x_min, "y": y_min},
        {"x": x_min, "y": y_max},
        {"x": x_max, "y": y_max},
        {"x": x_max, "y": y_min},
        {"x": tmp_x2, "y": y_min},
        {"x": tmp_x2, "y": y_main_min},
        {"x": tmp_x1, "y": y_main_min},
    ]
    kicad_mod.append(
        PolygonLine(
            shape=poly_fab_outline,
            layer="F.Fab",
            width=global_config.fab_line_width,
        )
    )

    ############################# Pads ##################################
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

    # add mounting hole for hook
    if hook:
        kicad_mod.append(
            Pad(
                at={"x": x_mid, "y": (9.2 - 2.7)},
                type=Pad.TYPE_NPTH,
                shape=Pad.SHAPE_OVAL,
                layers=Pad.LAYERS_NPTH,
                drill=hook_size,
                size=hook_size,
            )
        )

    ########################### CrtYd ################################
    crt_offset = global_config.get_courtyard_offset(GC.GlobalConfig.CourtyardType.CONNECTOR)
    cb = CourtyardBuilder.from_node(
        node=kicad_mod,
        global_config=global_config,
        offset_fab=crt_offset
        )
    kicad_mod += cb.node

    ########################### Pin 1 marker ################################
    poly_pin1_marker = [
        {"x": 0, "y": -1.2},
        {"x": -0.4, "y": -1.6},
        {"x": 0.4, "y": -1.6},
        {"x": 0, "y": -1.2},
    ]
    if silk_pin1_marker_type == 1:
        kicad_mod.append(
            PolygonLine(
                shape=poly_pin1_marker,
                layer="F.SilkS",
                width=global_config.silk_line_width,
            )
        )
    if silk_pin1_marker_type == 2:
        silk_pin1_marker_t2_x = -pad_size[0] / 2.0 - pad_silk_offset

        kicad_mod.append(
            Line(
                start=[silk_pin1_marker_t2_x, silk_y_main_min],
                end=[
                    silk_pin1_marker_t2_x,
                    -pad_size[1] / 2.0 - global_config.silk_pad_clearance,
                ],
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
            {"x": -0.75, "y": y_main_min},
            {"x": 0, "y": y_main_min + 0.75},
            {"x": 0.75, "y": y_main_min},
        ]
        kicad_mod.append(
            PolygonLine(
                shape=poly_pin1_marker_type2,
                layer="F.Fab",
                width=global_config.fab_line_width,
            )
        )

    if fab_pin1_marker_type == 3:
        fab_pin1_marker_t3_y = pad_size[1] / 2.0
        poly_pin1_marker_type2 = [
            {"x": 0, "y": fab_pin1_marker_t3_y},
            {"x": -0.5, "y": fab_pin1_marker_t3_y + 0.5},
            {"x": 0.5, "y": fab_pin1_marker_t3_y + 0.5},
            {"x": 0, "y": fab_pin1_marker_t3_y},
        ]
        kicad_mod.append(
            PolygonLine(
                shape=poly_pin1_marker_type2,
                layer="F.Fab",
                width=global_config.fab_line_width,
            )
        )

    ######################### Text Fields ###############################
    text_center_y = 2.5
    body_edge = {
        "left": x_min,
        "right": x_max,
        "top": y_min,
        "bottom": y_max,
    }
    addTextFields(
        kicad_mod=kicad_mod,
        configuration=configuration,
        body_edges=body_edge,
        courtyard=cb.bbox,
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
        for pincount in range(2, 14 + 1):
            generate_one_footprint(generator_name, global_config, pincount, variant, configuration)
            num_fps_generated += 1
    return num_fps_generated
