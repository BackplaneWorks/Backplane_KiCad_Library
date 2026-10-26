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
    "scripts: Stefan, based on DIP script; models: see cq_model files; update: jmwright"
)
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_parameters_Resonator_AT310 import *
from .cq_parameters_Resonator_C26_LF import *
from .cq_parameters_Resonator_C38_LF import *
from .cq_parameters_Resonator_peterman_smd import *
from .cq_parameters_Resonator_SMD_muRata_CSTx import *
from .cq_parameters_Resonator_smd_type_2 import *


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Make the parts of the model
    if spec.id.startswith("AT310"):
        cqm = cq_parameters_Resonator_AT310()
    elif spec.id.startswith("C26-LF"):
        cqm = cq_parameters_Resonator_C26_LF()
    elif spec.id.startswith("C38-LF"):
        cqm = cq_parameters_Resonator_C38_LF()
    elif spec.id.startswith("SMD"):
        cqm = cq_parameters_Resonator_peterman_smd()
    elif spec.id.startswith("Murata"):
        cqm = cq_parameters_Resonator_SMD_muRata_CSTx()
    elif spec.id.startswith("MicroCrystal"):
        cqm = cq_parameters_Resonator_smd_type_2()
    else:
        print("Model type {} not recognized.".format(spec.id))

    body_top = cqm.make_top(spec.spec)
    body = cqm.make_case(spec.spec)
    # The Murata code tries to mutate the body model which does not work anymore, so we have to work around it
    if spec.id.startswith("Murata"):
        pins, body = cqm.make_pins(body, spec.spec)
    else:
        pins = cqm.make_pins(body, spec.spec)

    parts = export_tools.AssemblyParts(
        [
            (body, spec.spec["body_color_key"]),
            (body_top, spec.spec["body_top_color_key"]),
            (pins, spec.spec["pin_color_key"]),
        ]
    )

    # Handle the case of the SMD models that have a bottom as well as the other parts
    if spec.id.startswith("SMD") or spec.id.startswith("MicroCrystal"):
        bottom = cqm.make_bottom(body, spec.spec)
        parts.append(bottom, spec.spec["bottom_color_key"])

    parts.rotate(spec.spec.get("rotation", 0))

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.spec["file_name"],
        parts=parts,
    )
    return 1
