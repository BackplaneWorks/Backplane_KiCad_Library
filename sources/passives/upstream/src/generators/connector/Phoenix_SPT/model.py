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
# * Copyright (c) 2016                                                       *
# *     Joel https://github.com/myfreescalewebpage                           *
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
__author__ = "scripts: maurice and Joel; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .phoenixcontact_terminal_block_spt_tht_model import generate_body, generate_pins


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Generate a model for each pin set
    for part in spec.spec["parts"]:
        # Generate the correct parts of the model
        body = generate_body(spec.spec, spec.spec["parts"][part])
        pins = generate_pins(spec.spec, spec.spec["parts"][part])

        # Create the file name based on the component attributes
        file_name = spec.spec["file_name_template"].format(
            series_prefix=spec.spec["series_prefix"]
            .replace(" ", "_")
            .replace("/", "_"),
            pins=spec.spec["parts"][part]["pins"],
            orientation_short=spec.spec["orientation"][:1],
            pitch=spec.spec["pitch"]["x"],
            series_sufix=spec.spec["series_sufix"],
            orientation=spec.spec["orientation"],
            rows=spec.spec["parts"][part]["rows"],
            mpn=str(part),
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
    return len(spec.spec["parts"])
