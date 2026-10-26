#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating PDIP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#
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
# * cadquery script for generating Molex models in STEP AP214                *
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

__title__ = "make molex connector 3D models exported to STEP and VRML"
__author__ = "scripts: maurice and hyOzd; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import logging

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_models.conn_molex_502250 import generate_part as generate_part_502250
from .cq_models.conn_molex_kk_5273 import generate_part as generate_part_kk_5273
from .cq_models.conn_molex_kk_6410 import generate_part as generate_part_kk_6410
from .cq_models.conn_molex_kk_41791 import generate_part as generate_part_kk_41791
from .cq_models.conn_molex_kk_41792 import generate_part as generate_part_kk_41792
from .cq_models.conn_molex_picoblade_53261 import generate_part as generate_part_53261
from .cq_models.conn_molex_picoblade_53398 import generate_part as generate_part_53398
from .cq_models.conn_molex_picoflex_90325 import generate_part as generate_part_90325
from .cq_models.conn_molex_picoflex_90814 import generate_part as generate_part_90814
from .cq_models.conn_molex_SlimStack_54722 import generate_part as generate_part_54722
from .cq_models.conn_molex_SlimStack_55560 import generate_part as generate_part_55560


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    if spec.spec["model_name"] == "502250":
        generate_part = generate_part_502250
    elif spec.spec["model_name"] == "5273":
        generate_part = generate_part_kk_5273
    elif spec.spec["model_name"] == "6410":
        generate_part = generate_part_kk_6410
    elif spec.spec["model_name"] == "41791":
        generate_part = generate_part_kk_41791
    elif spec.spec["model_name"] == "41792":
        generate_part = generate_part_kk_41792
    elif spec.spec["model_name"] == "53261":
        generate_part = generate_part_53261
    elif spec.spec["model_name"] == "53398":
        generate_part = generate_part_53398
    elif spec.spec["model_name"] == "90325":
        generate_part = generate_part_90325
    elif spec.spec["model_name"] == "90814":
        generate_part = generate_part_90814
    elif spec.spec["model_name"] == "54722":
        generate_part = generate_part_54722
    elif spec.spec["model_name"] == "55560":
        generate_part = generate_part_55560
    else:
        logging.error(
            "Could not find a match for model name {}.".format(spec.spec["model_name"])
        )
        return 0

    # Generate a variant for each pin count
    for pin_count in spec.spec["pin_range"]:
        # Make the parts of the model
        (pins, body, latch) = generate_part(spec.spec, pin_count)

        # Assemble the filename
        padded_pin_count = "0" + str(pin_count) if pin_count < 10 else str(pin_count)
        file_name = spec.spec["fp_name_format_string"].format(
            man=spec.spec["manufacturer"],
            padpincount="00" + padded_pin_count,
            halfpadpincount=(
                "0" + str(int(pin_count / 2))
                if (pin_count / 2) < 10
                else str(int(pin_count / 2))
            ),
            pincount=padded_pin_count,
            num_rows=spec.spec["number_of_rows"],
            pitch=(
                str(spec.spec["pitch"]) + "0"
                if spec.spec["model_name"].startswith("KK_396")
                else str(spec.spec["pitch"])
            ),
            orientation=spec.spec["orientation"],
        )

        parts = export_tools.AssemblyParts(
            [
                (body, spec.spec["body_color_key"]),
                (pins, spec.spec["pin_color_key"]),
            ]
        )

        if latch != None and not isinstance(latch.val(), cq.Vector):
            parts.append(latch, spec.spec["latch_color_key"])

        export_tools.export(
            generator_name=generator_name,
            lib_name=spec.spec["destination_dir"],
            model_name=file_name,
            parts=parts,
        )
    return len(spec.spec["pin_range"])
