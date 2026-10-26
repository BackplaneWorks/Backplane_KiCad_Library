#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating PDIP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
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
# * cadquery script for generating JST-XH models in STEP AP214               *
# * Copyright (c) 2016                                                       *
# *     Rene Poeschl https://github.com/poeschlr                             *
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

__title__ = "main generator for molex connector 3D models exported to STEP and VRML"
__author__ = "scripts: maurice and hyOzd; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_models import (
    conn_jst_eh_models,
    conn_jst_gh_models,
    conn_jst_ph_models,
    conn_jst_sh_models,
    conn_jst_xh_models,
)


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Create a model for each number of pins
    for pin_num in spec.spec["pin_range"]:
        spec.spec["num_pins"] = pin_num
        spec.spec["body_length"] = spec.spec["body_start_length"] + (
            spec.spec["pin_pitch"] * (pin_num - 1)
        )

        # Figure out which code to execute to create the models
        if spec.spec["series"] == "EH":
            cqm = conn_jst_eh_models
        elif spec.spec["series"] == "GH":
            cqm = conn_jst_gh_models
        elif spec.spec["series"] == "PH":
            cqm = conn_jst_ph_models
        elif spec.spec["series"] == "SH":
            cqm = conn_jst_sh_models
        elif spec.spec["series"] == "XH" or spec.spec["series"] == "XHVS":
            cqm = conn_jst_xh_models
        else:
            print("Model not recognized: {}".format(spec.spec["series"]))

        # Make the parts of the model
        body = cqm.generate_body(spec.spec)
        pins = cqm.generate_pins(spec.spec)
        body = body.rotateAboutCenter((0, 0, 1), spec.spec["rotation"])
        pins = pins.rotateAboutCenter((0, 0, 1), spec.spec["rotation"])
        body = body.translate(spec.spec["translation"])
        pins = pins.translate(spec.spec["translation"])

        # Assemble the filename
        pad_pins = "0" + str(pin_num) if pin_num < 10 else str(pin_num)
        file_name = spec.spec["file_name"].format(
            num_pins=pin_num, padded_pins=pad_pins
        )

        parts = export_tools.AssemblyParts(
            [
                (body, spec.spec["body_color_key"]),
                (pins, spec.spec["pin_color_key"]),
            ]
        )

        export_tools.export(
            generator_name=generator_name,
            lib_name=spec.spec["destination_dir"],
            model_name=file_name,
            parts=parts,
        )
    return len(spec.spec["pin_range"])
