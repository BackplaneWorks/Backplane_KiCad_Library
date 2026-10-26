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

__title__ = "make SMD inductors 3D models exported to STEP and VRML"
__author__ = "scripts: Stefan; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import logging

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_eSIP import cq_eSIP
from .cq_Sanyo_STK4xx import cq_Sanyo_STK4xx
from .cq_SIP_3 import cq_SIP_3


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    if spec.id == "PowerIntegrations_eSIP-7C":
        cqm = cq_eSIP()
        body_top = cqm.make_top_eSIP_7C(spec.spec)
        body = cqm.make_case_eSIP_7C(spec.spec)
        pins = cqm.make_pins_eSIP_7C(spec.spec)
        npth_pins = cqm.make_npth_pins(spec.spec)
    elif spec.id == "PowerIntegrations_eSIP-7F":
        cqm = cq_eSIP()
        body_top = cqm.make_top_eSIP_7F(spec.spec)
        body = cqm.make_case_eSIP_7F(spec.spec)
        pins = cqm.make_pins_eSIP_7F(spec.spec)
        npth_pins = cqm.make_npth_pins(spec.spec)
    elif spec.id == "Sanyo_STK4xx_59_2":
        cqm = cq_Sanyo_STK4xx()
        body_top = cqm.make_top_Sanyo_STK4xx_59_2(spec.spec)
        body = cqm.make_case_Sanyo_STK4xx_59_2(spec.spec)
        pins = cqm.make_pins_Sanyo_STK4xx_59_2(spec.spec)
        npth_pins = cqm.make_npth_pins(spec.spec)
    elif spec.id == "Sanyo_STK4xx_78_0":
        cqm = cq_Sanyo_STK4xx()
        body_top = cqm.make_top_Sanyo_STK4xx_78_0(spec.spec)
        body = cqm.make_case_Sanyo_STK4xx_78_0(spec.spec)
        pins = cqm.make_pins_Sanyo_STK4xx_78_0(spec.spec)
        npth_pins = cqm.make_npth_pins(spec.spec)
    elif spec.id == "SIP4_Sharp_Angled":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_SIP4_Sharp_Angled(spec.spec)
        pins = cqm.make_pins_SIP4_Sharp_Angled(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.id == "SIP4_Sharp_Straight":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_SIP4_Sharp_Straight(spec.spec)
        pins = cqm.make_pins_SIP4_Sharp_Straight(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.id == "SIP-3_P1.30mm":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_SIP_3_P1_30mm(spec.spec)
        pins = cqm.make_pins_SIP_3_P1_30mm(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.id == "SIP-3_P2.90mm":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_SIP_3_P2_90mm(spec.spec)
        pins = cqm.make_pins_SIP_3_P2_90mm(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.id == "SIP-8":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_SIP_8(spec.spec)
        pins = cqm.make_pins_SIP_8(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.id == "SIP-9":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_SIP_9(spec.spec)
        pins = cqm.make_pins_SIP_9(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.id == "SLA704XM":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_SLA704XM(spec.spec)
        pins = cqm.make_pins_SLA704XM(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.id == "STK672-040-E":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_STK672_040_E(spec.spec)
        pins = cqm.make_pins_STK672_040_E(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif spec.id == "STK672-080-E":
        cqm = cq_SIP_3()
        body_top = cqm.make_top_dummy(spec.spec)
        body = cqm.make_case_STK672_080_E(spec.spec)
        pins = cqm.make_pins_STK672_080_E(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    else:
        logging.error(
            "Match for model name {} not found.".format(spec.spec["model_name"])
        )
        return 0

    parts = export_tools.AssemblyParts(
        [
            (body, spec.spec["body_color_key"]),
            (pins, spec.spec["pin_color_key"]),
        ]
    )

    # Make sure we do not have a dummy top
    if not isinstance(body_top.val(), cq.Vector):
        parts.append(body_top, spec.spec["body_top_color_key"])
    # Make sure we do not have dummy NPTH pins
    if not isinstance(npth_pins.val(), cq.Vector):
        parts.append(npth_pins, spec.spec["npth_pin_color_key"])

    parts.rotate(spec.spec["rotation"])

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.spec["model_name"],
        parts=parts,
    )
    return 1
