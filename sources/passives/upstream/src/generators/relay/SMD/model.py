#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This was originally derived from a cadquery script for generating PDIP models in X3D format
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
# * Copyright (c) 2024                                                       *
# *     Martin Sotirov <martin@libtec.org>                                   *
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

from generators.tools.model import export_tools

from .cq_model_relay_smd import make_case, make_marker, make_pins

__title__ = "main generator for Relay_SMD model generators"
__author__ = (
    "scripts: hyOzd, Maurice, jmwright, Martin Sotirov; models: see cq_model files;"
)
__Comment__ = """Generates Relay SMD models for KiCad libraries"""

___ver___ = "2.0.0"


from generators.tools.spec.legacy_model_spec import LegacyModelSpec


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    has_marker = (
        "marker_pos" in spec.spec
        and "marker_dim" in spec.spec
        and "marker_color_key" in spec.spec
    )

    body = make_case(spec.spec, has_marker)

    marker = None
    if has_marker:
        marker = make_marker(spec.spec)

    pins = make_pins(spec.spec)

    parts = export_tools.AssemblyParts(
        [
            (body, spec.spec["body_color_key"]),
            (pins, spec.spec["pin_color_key"]),
            (marker, spec.spec["marker_color_key"]),
        ]
    )
    parts.translate(spec.spec["translation"])
    parts.rotate(spec.spec["rotation"])

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.spec["model_name"],
        parts=parts,
    )
    return 1
