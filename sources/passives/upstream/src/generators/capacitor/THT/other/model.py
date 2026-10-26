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
# * These are FreeCAD & cadquery tools                                       *
# * to export generated models in STEP & VRML format.                        *
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

from .cq_models import c_axial_tht, c_disc_tht, c_rect_tht, cp_axial_tht


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Generate the current model
    if spec.spec["model_class"] == "c_axial_tht":
        cqm = c_axial_tht
    elif spec.spec["model_class"] == "c_disc_tht":
        cqm = c_disc_tht
    elif spec.spec["model_class"] == "c_rect_tht":
        cqm = c_rect_tht
    elif spec.spec["model_class"] == "cp_axial_tht":
        cqm = cp_axial_tht
    else:
        logging.error("No match found for the model_class.")
        return 0

    parts: export_tools.AssemblyParts

    # The CP Axial capacitors are a special case
    if spec.spec["model_class"] == "cp_axial_tht":

        body, mmb, bar, leads, top = cqm.generate_part(spec.spec)

        parts = export_tools.AssemblyParts(
            [
                (body, spec.spec["body_color_key"]),
                (leads, spec.spec["pins_color_key"]),
                (mmb, spec.spec["mark_vg_color_key"]),
                (bar, spec.spec["mark_bg_color_key"]),
                (top, spec.spec["endcaps_color_key"]),
            ]
        )
        parts.translate(
            (
                spec.spec["body_setback_distance"],
                0.0,
                spec.spec["body_board_distance"],
            )
        )

    else:
        body, leads = cqm.generate_part(spec.spec)

        body = body.translate(
            (
                spec.spec["body_setback_distance"],
                0.0,
                spec.spec["body_board_distance"],
            )
        )
        leads = leads.translate((spec.spec["body_setback_distance"], 0.0, 0.0))

        parts = export_tools.AssemblyParts(
            [
                (body, spec.spec["body_color_key"]),
                (leads, spec.spec["pins_color_key"]),
            ]
        )

    parts.rotate(spec.spec.get("rotation", 0))

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.id,
        parts=parts,
    )
    return 1
