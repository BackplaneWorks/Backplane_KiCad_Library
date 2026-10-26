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
# * Copyright (c) 2015                                                       *
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
__author__ = (
    "scripts: maurice, hyOzd, Stefan; models: see cq_model files; update: jmwright"
)
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from generators.tools.model import export_tools

from .dip_packages import make_case, make_pins_smd, make_pins_tht

CASE_THT_TYPE = "tht"
CASE_SMD_TYPE = "smd"
CASE_THTSMD_TYPE = "thtsmd"

CORNER_CHAMFER_TYPE = "chamfer"
CORNER_FILLET_TYPE = "fillet"

from generators.tools.spec.legacy_model_spec import LegacyModelSpec


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Make the parts of the model
    body = make_case(spec.spec)

    if spec.spec["type"] == CASE_THT_TYPE:
        pins = make_pins_tht(spec.spec)

    if spec.spec["type"] == CASE_SMD_TYPE:
        pins = make_pins_smd(spec.spec)

    # Put the parts in the correct position relative to the pads on the board
    mvY = spec.spec["npins"] * spec.spec["e"] / 4 - spec.spec["e"] / 2.0
    mvX = (spec.spec["E"] - 0.254) / 2.0

    parts = export_tools.AssemblyParts(
        [
            (body, spec.spec["body_color_key"]),
            (pins, spec.spec["pin_color_key"]),
        ]
    )
    parts.rotate(spec.spec["rotation"])
    parts.translate((mvX, -mvY, 0))

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.spec["model_name"],
        parts=parts,
    )
    return 1
