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
# * cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
# * Original script:                                                         *
# * Copyright (c) 2016 Hasan Yavuz Özderya https://bitbucket.org/hyOzd       *
# *                    Maurice https://github.com/easyw                      *
# *                    Rene Poeschl https://github.com/poeschlr              *
# * Refactored to be model-independent:                                      *
# * Copyright (c) 2017 Ray Benitez https://github.com/hackscribble           *
# * Updated:                                                                 *
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

__title__ = "export of 3D models exported to STEP and VRML"
__author__ = "scripts: hackscribble; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import logging

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_DPAK_factory import (
    ATPAK,
    HSOF8,
    SOT89,
    SOT669,
    SOT1235,
    TO252,
    TO263,
    TO268,
    Infineon_PG_TO_220_7Lead_TabPin8,
    Rohm_HRP7,
)


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Check the model name to see which class to load
    available_models = {
        "TO-252": TO252,
        "TO-263": TO263,
        "TO-268": TO268,
        "ATPAK": ATPAK,
        "HSOF8": HSOF8,
        "LFPAK56": SOT669,
        "LFPAK88": SOT1235,
        "SOT89": SOT89,
        "Infineon_PG_TO_220_7Lead_TabPin8": Infineon_PG_TO_220_7Lead_TabPin8,
        "Rohm_HRP7": Rohm_HRP7,
    }
    try:
        cqm = available_models[spec.id]()
    except KeyError:
        logging.error(
            f"Model not recognized '{spec.id}'. Please choose from the available models: {list(sorted(available_models.keys()))}."
        )
        return 0

    # Build all the variants
    for variant in spec.spec["variants"]:
        # Make the parts of the model
        body, tab, pins, file_name = cqm.build_series(
            spec.spec["base"], spec.spec["variants"][variant]
        )

        parts = export_tools.AssemblyParts(
            [
                (body, spec.spec["base"]["device"]["body"]["colour"]),
                (tab, spec.spec["base"]["device"]["tab"]["colour"]),
                (pins, spec.spec["base"]["device"]["pins"]["colour"]),
            ]
        )

        export_tools.export(
            generator_name=generator_name,
            lib_name=spec.spec["destination_dir"],
            model_name=file_name,
            parts=parts,
        )
    return len(spec.spec["variants"])
