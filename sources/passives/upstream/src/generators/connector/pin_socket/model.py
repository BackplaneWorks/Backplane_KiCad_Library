#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This was originaly derived from a cadquery script for generating PDIP models in X3D format
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#
# Adapted by easyw for step and vrlm export
# See https://github.com/easyw/kicad-3d-models-in-freecad
#
## Requirements
## CadQuery 2.1 commit e00ac83f98354b9d55e6c57b9bb471cdf73d0e96 or newer
## https://github.com/CadQuery/cadquery
#
## To run the script just do: ./generator.py --output_dir [output_directory]
## e.g. ./generator.py --output_dir /tmp
#
## the script will generate STEP and VRML parametric models
## to be used with kicad StepUp script
#
# * These are cadquery tools to export                                       *
# * generated models in STEP & VRML format.                                  *
# *                                                                          *
# * cadquery script for generating Molex models in STEP AP214                *
# *   Copyright (c) 2016                                                     *
# * Rene Poeschl https://github.com/poeschlr                                 *
# * Copyright (c) 2021                                                       *
# *     Update 2021                                                          *
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
__author__ = "scripts: maurice and hyOzd; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import logging

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_socket_strips import angled_socket_strip, smd_socket_strip, socket_strip


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Create a model for each number of pins
    pin_range = range(spec.spec["pins_min"], spec.spec["pins_max"] + 1)
    for pin_num in pin_range:
        if spec.spec["num_pin_rows"] == 1:
            spec.spec["num_pins"] = pin_num
        else:
            spec.spec["num_pins"] = pin_num * 2

        # Generate the current model
        if spec.spec["model_class"].startswith("SMD"):
            cqm = smd_socket_strip(spec.spec)
        elif spec.spec["model_class"].endswith("Vertical"):
            cqm = socket_strip(spec.spec)
        elif spec.spec["model_class"].endswith("Horizontal"):
            cqm = angled_socket_strip(spec.spec)
        else:
            logging.error("No match found for model_class.")

        # Make the translation correct
        translation = (0.0, 0.0)
        if spec.spec["model_class"] == "THT-1x1.00mm_Vertical":
            translation = (
                spec.spec["pin_pitch"]
                * (pin_num / 2.0 / spec.spec["num_pin_rows"] - 0.5),
                spec.spec["pin_width"] / 1.5 + spec.spec["pin_thickness"] - 0.01,
                0.0,
            )  # 1 = num_pin_rows, second pin_pitch = pin_rows_distance
        elif spec.spec["model_class"] == "THT-1x1.27mm_Vertical":
            translation = (
                spec.spec["pin_pitch"]
                * (pin_num / 2.0 / spec.spec["num_pin_rows"] - 0.5),
                spec.spec["pin_width"] / 2.0 - spec.spec["pin_thickness"] - 0.05,
                0.0,
            )  # 1 = num_pin_rows, second pin_pitch = pin_rows_distance
        elif spec.spec["model_class"] == "THT-1x2.00mm_Vertical":
            translation = (
                spec.spec["pin_pitch"]
                * (pin_num / 2.0 / spec.spec["num_pin_rows"] - 0.5),
                spec.spec["pin_width"] / 2.0 - spec.spec["pin_thickness"] - 0.1,
                0.0,
            )  # 1 = num_pin_rows, second pin_pitch = pin_rows_distance
        elif spec.spec["model_class"] == "THT-1x2.54mm_Vertical":
            translation = (
                spec.spec["pin_pitch"]
                * (pin_num / 2.0 / spec.spec["num_pin_rows"] - 0.5),
                spec.spec["pin_width"] / 2.0 - spec.spec["pin_thickness"] - 0.1,
                0.0,
            )  # 1 = num_pin_rows, second pin_pitch = pin_rows_distance
        elif spec.spec["model_class"].startswith("THT-1") and spec.spec[
            "model_class"
        ].endswith("Horizontal"):
            translation = (
                spec.spec["pin_pitch"] * (pin_num - 1) / 2.0,
                spec.spec["pin_pitch"] / 2.0 - spec.spec["pin_pitch"] / 2.0,
                0.0,
            )  # spec.spec['pin_pitch'] / 2.0)
        elif spec.spec["model_class"].startswith("THT-2") and spec.spec[
            "model_class"
        ].endswith("Horizontal"):
            translation = (
                spec.spec["pin_pitch"] * (pin_num - 1) / 2.0,
                spec.spec["pin_pitch"] / 2.0
                - spec.spec["pin_width"] / 2.0
                + spec.spec["pin_thickness"]
                + 0.1,
                0.0,
            )  # spec.spec['pin_pitch'] / 2.0)
        elif spec.spec["model_class"].startswith("SMD"):
            translation = (0.0, 0.0, spec.spec["pin_width"] / 2.0)
        else:
            translation = (
                spec.spec["pin_pitch"] * (pin_num - 1) / 2.0,
                spec.spec["pin_pitch"] / 2.0,
                0.0,
            )

        # Generate the current strip
        body = cqm._make_body()
        pins = cqm._make_pins()

        # Make sure the pin name is zero padded
        if pin_num < 10:
            pin_num_str = "0" + str(pin_num)
        else:
            pin_num_str = str(pin_num)

        # Create the file name based on the rows and pins
        file_name = spec.spec["model_name"].format(
            spec.spec["num_pin_rows"], pin_num_str
        )

        parts = export_tools.AssemblyParts(
            [
                (body, spec.spec["body_color_key"]),
                (pins, spec.spec["pins_color_key"]),
            ]
        )
        parts.translate((-translation[0], translation[1], translation[2]))
        parts.rotate(spec.spec["rotation"])

        export_tools.export(
            generator_name=generator_name,
            lib_name=spec.spec["destination_dir"],
            model_name=file_name,
            parts=parts,
        )
    return len(pin_range)
