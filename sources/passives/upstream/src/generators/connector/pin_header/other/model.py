#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating PDIP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
# This is a
# Dimensions are from Microchips Packaging Specification document:
# DS00000049BY. Body drawing is the same as QFP generator#
#
## Requirements
## CadQuery 2.1 commit e00ac83f98354b9d55e6c57b9bb471cdf73d0e96 or newer
## https://github.com/CadQuery/cadquery
#
## To run the script just do: ./generator.py --output_dir [output_directory]
## e.g. ./generator.py --output_dir /tmp
#
# * These are cadquery tools to export                                       *
# * generated models in STEP & VRML format.                                  *
# *                                                                          *
# * cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
# *   Copyright (c) 2015                                                     *
# *     Maurice https://launchpad.net/~easyw                                 *
# * Copyright (c) 2022                                                       *
# *     Update 2022                                                          *
# *     jmwright (https://github.com/jmwright)                               *
# *     Work sponsored by KiCAD Services Corporation                         *
# *          (https://www.kipro-pcb.com/)                                    *
# *                                                                          *
# * All trademarks within this guide belong to their legitimate owners.      *
# *                                                                          *
# *   This program is free software; you can redistribute it and/or modify   *
# *   it under the terms of the GNU General Public License (GPL)             *
# *   as published by the Free Software Foundation; either version 2 of      *
# *   the License, or (at your option) any later version.                    *
# *   for detail see the LICENCE text file.                                  *
# *                                                                          *
# *   This program is distributed in the hope that it will be useful,        *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
# *   GNU Library General Public License for more details.                   *
# *                                                                          *
# *   You should have received a copy of the GNU Library General Public      *
# *   License along with this program; if not, write to the Free Software    *
# *   Foundation, Inc.,                                                      *
# *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA           *
# *                                                                          *
# ****************************************************************************

__title__ = "main generator for capacitor tht model generators"
__author__ = "scripts: maurice and Shack; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_pinheader import (
    make_Horizontal_THT_base,
    make_Horizontal_THT_pins,
    make_Vertical_SMD_base,
    make_Vertical_SMD_pins,
    make_Vertical_THT_base,
    make_Vertical_THT_pins,
)


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    header_type = spec.spec["type"]
    pitch = spec.spec["pitch"]
    rows = spec.spec["rows"]
    base_width = spec.spec["base_width"]
    base_height = spec.spec["base_height"]
    base_chamfer = spec.spec["base_chamfer"]
    base_extra_length = (
        spec.spec["base_extra_length"] if "base_extra_length" in spec.spec else 0
    )
    base_wall_height = (
        spec.spec["base_wall_height"] if "base_wall_height" in spec.spec else 0
    )
    base_wall_internal_width = (
        spec.spec["base_wall_internal_width"]
        if "base_wall_internal_width" in spec.spec
        else 0
    )
    base_wall_internal_extra_length = (
        spec.spec["base_wall_internal_extra_length"]
        if "base_wall_internal_extra_length" in spec.spec
        else 0
    )
    notch_x_size = spec.spec["notch_x_size"] if "notch_x_size" in spec.spec else 0
    notch_y_size = spec.spec["notch_y_size"] if "notch_y_size" in spec.spec else 0
    notch_height = spec.spec["notch_height"] if "notch_height" in spec.spec else 0
    notch_position = (
        spec.spec["notch_position"] if "notch_position" in spec.spec else ""
    )
    pin_width = spec.spec["pin_width"]
    pin_length_above_base = spec.spec["pin_length_above_base"]

    pin_end_chamfer = spec.spec["pin_end_chamfer"]
    rotation = spec.spec["rotation"]

    # Collect the array of pin numbers so that we can handle the one config that has a custom set in a string
    if isinstance(spec.spec["pins"], str):
        pin_set = [int(x) for x in spec.spec["pins"].split(",")]
    else:
        pin_num_start = spec.spec["pins"]["from"]
        pin_num_end = spec.spec["pins"]["to"]
        pin_set = range(pin_num_start, pin_num_end + 1)

    if base_chamfer == "auto":
        base_chamfer = pitch / 10.0

    if pin_end_chamfer == "auto":
        pin_end_chamfer = pin_width / 4.0

    for num_pins in pin_set:
        if header_type == "Vertical_THT":
            pin_length_below_board = spec.spec["pin_length_below_board"]
            base = make_Vertical_THT_base(
                num_pins, pitch, rows, base_width, base_height, base_chamfer
            )
            pins = make_Vertical_THT_pins(
                num_pins,
                pitch,
                rows,
                pin_length_above_base,
                pin_length_below_board,
                base_height,
                pin_width,
                pin_end_chamfer,
            )
        elif header_type == "Horizontal_THT":
            pin_length_below_board = spec.spec["pin_length_below_board"]
            base_x_offset = spec.spec["base_x_offset"]
            base = make_Horizontal_THT_base(
                num_pins,
                pitch,
                rows,
                base_width,
                base_height,
                base_x_offset,
                base_chamfer,
            )
            pins = make_Horizontal_THT_pins(
                num_pins,
                pitch,
                rows,
                pin_length_above_base,
                pin_length_below_board,
                base_height,
                base_width,
                pin_width,
                pin_end_chamfer,
                base_x_offset,
            )
        elif header_type == "Vertical_SMD":
            pin_length_horizontal = spec.spec["pin_length_horizontal"]
            base_z_offset = spec.spec["base_z_offset"]
            if rows == 1:
                pin_1_start = spec.spec["pin_1_start"]
            else:
                pin_1_start = None
            pins = make_Vertical_SMD_pins(
                num_pins,
                pitch,
                rows,
                pin_length_above_base,
                pin_length_horizontal,
                base_height,
                base_width,
                pin_width,
                pin_end_chamfer,
                base_z_offset,
                pin_1_start,
            )
            base = make_Vertical_SMD_base(
                num_pins,
                pitch,
                base_width,
                base_height,
                base_chamfer,
                base_z_offset,
                base_extra_length,
                base_wall_height,
                base_wall_internal_width,
                base_wall_internal_extra_length,
                notch_position,
                notch_x_size,
                notch_y_size,
                notch_height,
            )

        else:
            print("Model {} is not recognized.".format(spec.id))
            continue

        # Create the file name based on the rows and pins
        if num_pins < 10:
            num_pins_str = "0" + str(num_pins)
        else:
            num_pins_str = str(num_pins)
        file_name = spec.id.replace("yy", num_pins_str)

        parts = export_tools.AssemblyParts(
            [
                (base, spec.spec["body_color_key"]),
                (pins, spec.spec["pin_color_key"]),
            ]
        )

        export_tools.export(
            generator_name=generator_name,
            lib_name=spec.spec["destination_dir"],
            model_name=file_name,
            parts=parts,
        )
    return len(pin_set)
