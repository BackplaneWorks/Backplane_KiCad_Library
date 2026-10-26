#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# * These are cadquery tools to export                                       *
# * generated models in STEP & VRML format.                                  *
# *                                                                          *
# * cadquery script for generating coil models in STEP AP214                 *
# * Copyright (c) 2025 KiCad Library Team                                    *
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

__title__ = "make opto device 3D models exported to STEP and VRML"
__author__ = "scripts: aris-kimi"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .vishay_cny70 import make_Vishay_CNY70
from .vishay_tcrt5000 import make_Vishay_TCRT5000


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    modelName = spec.spec["model_name"]
    # Make the parts of the model
    if modelName == "Vishay_CNY70":
        (body, em, dt, text, pin) = make_Vishay_CNY70(spec.spec)
    elif modelName == "Vishay_TCRT5000":
        (body, em, dt, text, pin) = make_Vishay_TCRT5000(spec.spec)

    parts = export_tools.AssemblyParts(
        [
            (body, spec.spec["body_color_key"]),
            (em, spec.spec["emitter_color_key"]),
            (dt, spec.spec["detector_color_key"]),
            (text, spec.spec["text_color_key"]),
            (pin, spec.spec["pin_color_key"]),
        ]
    )
    parts.rotate(spec.spec.get("rotation", 0))

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.spec["model_name"],
        parts=parts,
    )
    return 1
