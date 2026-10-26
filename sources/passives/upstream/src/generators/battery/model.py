#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating Converter_DCDC 3D
# format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
# This is a
# Dimensions are from Microchips Packaging Specification document:
# DS00000049BY. Body drawing is the same as QFP generator#
#
# Thanks to Frank Severinsen (Shack) for including the orignal vrml
# materials.
#
## Requirements
## CadQuery 2.1 commit e00ac83f98354b9d55e6c57b9bb471cdf73d0e96 or newer
## https://github.com/CadQuery/cadquery
#
## To run the script just do: ./generator.py --output_dir [output_directory]
## e.g. ./generator.py --output_dir /tmp
#
## These are CadQuery scripts that will generate STEP and VRML parametric
## models.
#
# *                                                                          *
# * CadQuery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
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
# *   it under the terms of the GNU Lesser General Public License (LGPL)     *
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

__title__ = "make various battery 3D models"
__author__ = "Stefan, jmwright"
__Comment__ = "make battery 3D models exported to STEP and VRML"

___ver___ = "2.0.0"

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

# import .battery_casebutton
from .cq_model.battery_casebutton import *

# import .battery_caseBX0036
from .cq_model.battery_caseBX0036 import *

# import .battery_casecylinder
from .cq_model.battery_casecylinder import *

# import .battery_common
from .cq_model.battery_common import *

# import .battery_contact
from .cq_model.battery_contact import *

# import .battery_pins
from .cq_model.battery_pins import *

# import .cq_Keystone_2993
from .cq_model.cq_Keystone_2993 import *

# import .cq_Seiko_MSXXXX
from .cq_model.cq_Seiko_MSXXXX import *


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Handle each model type
    if spec.id == "BatteryHolder_Seiko_MS621F":
        case = make_case_Seiko_MS621F(spec.spec)
        pins = make_pins_Seiko_MS621F(spec.spec)
    elif spec.id == "BatteryHolder_Keystone_2993":
        case = make_case_Keystone_2993(spec.spec)
        pins = make_pins_Keystone_2993(spec.spec)
    elif spec.spec["modeltype"] == "BX0036":
        case = make_case_BX0036(spec.spec)
        pins = make_pins(spec.spec)
    elif spec.spec["modeltype"] == "Button1":
        case = make_case_Button1(spec.spec)
        pins = make_pins(spec.spec)
    elif spec.spec["modeltype"] == "Button2":
        case = make_case_Button2(spec.spec)
        pins = make_pins(spec.spec)
    elif spec.spec["modeltype"] == "Button3":
        case = make_case_Button3(spec.spec)
        pins = make_pins(spec.spec)
    elif spec.spec["modeltype"] == "Button4":
        case = make_case_Button4(spec.spec)
        pins = make_pins(spec.spec)
    elif spec.spec["modeltype"] == "Cylinder1":
        case = make_case_Cylinder1(spec.spec)
        pins = make_pins(spec.spec)

    parts = export_tools.AssemblyParts(
        [
            (case, spec.spec["body_color_key"]),
            (pins, spec.spec["pins_color_key"]),
        ]
    )

    export_tools.export(
        generator_name=generator_name,
        lib_name="Battery",
        model_name=spec.id,
        parts=parts,
    )
    return 1
