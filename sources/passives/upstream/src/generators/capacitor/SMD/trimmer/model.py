# -*- coding: utf-8 -*-
#!/usr/bin/python
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
## the script will generate STEP and VRML parametric models
## to be used with kicad StepUp script
#
# *                                                                          *
# * cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
# *   Copyright (c) 2015                                                     *
# * Maurice https://launchpad.net/~easyw                                     *
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
# *   This program is distribuited in the hope that it will be useful,        *
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

__title__ = "make Valve 3D models"
__author__ = "scripts: Stefan, based on Valve script; models: see cq_model files; update: jmwright"
__Comment__ = """Makes varistor 3D models exported to STEP and VRML."""

___ver___ = "2.0.0"


import logging

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from . import cq_murata, cq_sprague_goodman, cq_voltronics


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Generate the current model
    if spec.spec["model_class"] == "murata":
        cqm = cq_murata.cq_murata()
    elif spec.spec["model_class"] == "sprague_goodman":
        cqm = cq_sprague_goodman.cq_sprague_goodman()
    elif spec.spec["model_class"] == "voltronics":
        cqm = cq_voltronics.cq_voltronics()
    else:
        logging.error("No match found for the model_class")
        return 0

    # The CP Axial capacitors are a special case
    if spec.spec["model_class"] == "murata":
        if spec.spec["modelName"].endswith("Murata_TZB4-A"):
            body_top = cqm.make_top_Murata_TZB4_A(spec.spec)
            body = cqm.make_case_Murata_TZB4_A(spec.spec)
            pins = cqm.make_pin_Murata_TZB4_A(spec.spec)
        elif spec.spec["modelName"].endswith("Murata_TZB4-B"):
            body_top = cqm.make_top_Murata_TZB4_B(spec.spec)
            body = cqm.make_case_Murata_TZB4_B(spec.spec)
            pins = cqm.make_pin_Murata_TZB4_B(spec.spec)
        elif spec.spec["modelName"].endswith("Murata_TZC3"):
            body_top = cqm.make_top_Murata_TZC3(spec.spec)
            body = cqm.make_case_Murata_TZC3(spec.spec)
            pins = cqm.make_pin_Murata_TZC3(spec.spec)
        elif spec.spec["modelName"].endswith("Murata_TZR1"):
            body_top = cqm.make_top_Murata_TZR1(spec.spec)
            body = cqm.make_case_Murata_TZR1(spec.spec)
            pins = cqm.make_pin_Murata_TZR1(spec.spec)
        elif spec.spec["modelName"].endswith("Murata_TZW4"):
            body_top = cqm.make_top_Murata_TZW4(spec.spec)
            body = cqm.make_case_Murata_TZW4(spec.spec)
            pins = cqm.make_pin_Murata_TZW4(spec.spec)
        elif spec.spec["modelName"].endswith("Murata_TZY2"):
            body_top = cqm.make_top_Murata_TZY2(spec.spec)
            body = cqm.make_case_Murata_TZY2(spec.spec)
            pins = cqm.make_pin_Murata_TZY2(spec.spec)
        else:
            logging.error("No match found for the modelName.")
            return 0
    elif spec.spec["model_class"] == "sprague_goodman":
        body_top = cqm.make_top_Sprague_Goodman_SGC3(spec.spec)
        body = cqm.make_case_Sprague_Goodman_SGC3(spec.spec)
        pins = cqm.make_pin_Sprague_Goodman_SGC3(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.spec["model_class"] == "voltronics":
        if spec.spec["modelName"].endswith("Voltronics_JN"):
            body_top = cqm.make_top_Voltronics_JN(spec.spec)
            body = cqm.make_case_Voltronics_JN_JQ(spec.spec)
            pins = cqm.make_pin_Voltronics_JN_JQ(spec.spec)
        elif spec.spec["modelName"].endswith("Voltronics_JQ"):
            body_top = cqm.make_top_Voltronics_JQ(spec.spec)
            body = cqm.make_case_Voltronics_JN_JQ(spec.spec)
            pins = cqm.make_pin_Voltronics_JN_JQ(spec.spec)
        elif spec.spec["modelName"].endswith("Voltronics_JR"):
            body_top = cqm.make_top_Voltronics_JR(spec.spec)
            body = cqm.make_case_Voltronics_JR(spec.spec)
            pins = cqm.make_pin_Voltronics_JR(spec.spec)
        elif spec.spec["modelName"].endswith("Voltronics_JV"):
            body_top = cqm.make_top_Voltronics_JV(spec.spec)
            body = cqm.make_case_Voltronics_JV(spec.spec)
            pins = cqm.make_pin_Voltronics_JV(spec.spec)
        elif spec.spec["modelName"].endswith("Voltronics_JZ"):
            body_top = cqm.make_top_Voltronics_JZ(spec.spec)
            body = cqm.make_case_Voltronics_JZ(spec.spec)
            pins = cqm.make_pin_Voltronics_JZ(spec.spec)
        else:
            logging.error("No match found for the modelName.")
            return 0
    else:
        logging.error("No match for model_class.")
        return 0

    parts = export_tools.AssemblyParts(
        [
            (body_top, spec.spec["body_top_color_key"]),
            (body, spec.spec["body_color_key"]),
            (pins, spec.spec["pins_color_key"]),
        ]
    )

    # Handle NPTH pins
    if spec.spec["model_class"] == "sprague_goodman":
        parts.append(npth_pins, spec.spec["pins_color_key"])

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.id,
        parts=parts,
    )
    return 1
