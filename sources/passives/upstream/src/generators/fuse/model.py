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

__title__ = "main generator for making Fuse 3D models exported to STEP and VRML"
__author__ = "scripts: Stefan; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import logging

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_belfuse import cq_belfuse
from .cq_bulgin import cq_bulgin
from .cq_keystone import cq_keystone
from .cq_littlefuse import cq_littlefuse
from .cq_schurter import cq_schurter
from .cq_tme import cq_tme


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Choose the right model file
    if spec.spec["type"] == "belfuse":
        cqm = cq_belfuse()
    elif spec.spec["type"] == "keystone":
        cqm = cq_keystone()
    elif spec.spec["type"] == "bulgin":
        cqm = cq_bulgin()
    elif spec.spec["type"] == "schurter":
        cqm = cq_schurter()
    elif spec.spec["type"] == "tme":
        cqm = cq_tme()
    elif spec.spec["type"] == "littlefuse":
        cqm = cq_littlefuse()
    else:
        logging.error("Model type {} does not exist".format(spec.spec["type"]))
        return 0

    # Set the rotation and translation of the models
    cqm.set_rotation(spec.spec)
    cqm.set_translate(spec.id)

    # Make the parts of the model
    if spec.id == "Bulgin_FX0456":
        body = cqm.make_body_Bulgin_FX0456(spec.spec, spec.id)
    elif spec.id == "Bulgin_FX0457":
        body = cqm.make_body_Bulgin_FX0457(spec.spec, spec.id)
    elif spec.id == "Schurter_0031-8002":
        body = cqm.make_body_Schurter_0031_8002(spec.spec, spec.id)
    elif spec.id == "Schurter_0031_8201":
        body = cqm.make_body_Schurter_0031_8201(spec.spec, spec.id)
    elif spec.id == "Schurter_FAB_0031_355x":
        body = cqm.make_body_Schurter_FAB_0031_355x(spec.spec, spec.id)
    else:
        body = cqm.make_body(spec.spec, spec.id)
    body_top = cqm.make_top(spec.spec, spec.id)
    if spec.id == "Schurter_0031-8002":
        pins = cqm.make_pin_Schurter_0031_8002(spec.spec, spec.id)
    elif spec.id == "Schurter_0031_8201":
        pins = cqm.make_pin_Schurter_0031_8201(spec.spec, spec.id)
    elif spec.id == "Schurter_FAB_0031_355x":
        pins = cqm.make_pin_Schurter_FAB_0031_355x(spec.spec, spec.id)
    else:
        pins = cqm.make_pin(spec.spec, spec.id)
    npth_pins = cqm.make_npth_pin(spec.spec, spec.id)

    parts = export_tools.AssemblyParts(
        [
            (body, spec.spec["body_color_key"]),
            (body_top, spec.spec["body_top_color_key"]),
            (pins, spec.spec["pin_color_key"]),
            (npth_pins, spec.spec["npth_pin_color_key"]),
        ]
    )

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.spec["model_name"],
        parts=parts,
    )
    return 1
