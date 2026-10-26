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
## the script will generate STEP and VRML parametric models
## to be used with kicad StepUp script

# * These are a FreeCAD & cadquery tools                                     *
# * to export generated models in STEP & VRML format.                        *
# *                                                                          *
# * cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
# *   Copyright (c) 2015                                                     *
# * Maurice https://launchpad.net/~easyw                                     *
# * Copyright (c) 2021                                                       *
# *     Update 2021                                                          *
# *     jmwright (https://github.com/jmwright)                               *
# *     Work sponsored by KiCAD Services Corporation                         *
# *          (https://www.kipro-pcb.com/)                                    *
# * Copyright (c) 2024                                                       *
# *     Martin Sotirov <martin@libtec.org>                                   *
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

__title__ = "make Valve 3D models"
__author__ = "Stefan, based on DIP script"
__Comment__ = (
    "make varistor 3D models exported to STEP and VRML for Kicad StepUP script"
)

___ver___ = "2.0.0"

import logging

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from . import cq_parameters_smd_generic_rectangular
from .cq_parameters_CUI_CST_931RP_A import cq_parameters_CUI_CST_931RP_A
from .cq_parameters_EMB84Q_RO_SMT_0825_S_4_R import (
    cq_parameters_EMB84Q_RO_SMT_0825_S_4_R,
)
from .cq_parameters_kingstate_KCG0601 import cq_parameters_kingstate_KCG0601
from .cq_parameters_murata_PKMCS0909E4000 import cq_parameters_murata_PKMCS0909E4000
from .cq_parameters_ProjectsUnlimited_AI_4228_TWT_R import (
    cq_parameters_ProjectsUnlimited_AI_4228_TWT_R,
)
from .cq_parameters_ProSignal_ABI_XXX_RC import cq_parameters_ProSignal_ABI_XXX_RC
from .cq_parameters_PUI_AI_1440_TWT_24V_2_R import cq_parameters_PUI_AI_1440_TWT_24V_2_R
from .cq_parameters_StarMicronics_HMB_06_HMB_12 import (
    cq_parameters_StarMicronics_HMB_06_HMB_12,
)
from .cq_parameters_TDK_PS1240P02BT import cq_parameters_TDK_PS1240P02BT
from .cq_parameters_tht_generic_round import cq_parameters_tht_generic_round


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    BODY_PINS = ("cq_parameters_smd_generic_rectangular",)
    CASETOP_PINS = (
        "cq_parameters_murata_PKMCS0909E4000",
        "cq_parameters_CUI_CST_931RP_A",
        "cq_parameters_EMB84Q_RO_SMT_0825_S_4_R",
        "cq_parameters_ProSignal_ABI_XXX_RC",
        "cq_parameters_StarMicronics_HMB_06_HMB_12",
    )
    CASETOP_BODY_PINS = (
        "cq_parameters_kingstate_KCG0601",
        "cq_parameters_ProjectsUnlimited_AI_4228_TWT_R",
        "cq_parameters_TDK_PS1240P02BT",
        "cq_parameters_PUI_AI_1440_TWT_24V_2_R",
    )
    CASETOP_BODY_PINS_NTHPIN = ("cq_parameters_tht_generic_round",)

    model_class_name = spec.spec["model_class"]

    parts = export_tools.AssemblyParts()

    if model_class_name in BODY_PINS:
        cqm = globals()[model_class_name]
        body = cqm.make_body(spec.spec)
        pins = cqm.make_pins(spec.spec)

        parts.append(body, spec.spec["body_color_key"])
        parts.append(pins, spec.spec["pins_color_key"])

    elif model_class_name in CASETOP_PINS:
        cqm = globals()[model_class_name]()
        case_top = cqm.make_case(spec.spec)
        pins = cqm.make_pins(spec.spec)

        parts.append(case_top, spec.spec["case_top_color_key"])
        parts.append(pins, spec.spec["pins_color_key"])

    elif model_class_name in CASETOP_BODY_PINS:
        cqm = globals()[model_class_name]()
        case_top = cqm.make_top(spec.spec)
        case = cqm.make_case(spec.spec)
        pins = cqm.make_pins(spec.spec)

        parts.append(case_top, spec.spec["case_top_color_key"])
        parts.append(case, spec.spec["body_color_key"])
        parts.append(pins, spec.spec["pins_color_key"])

    elif model_class_name in CASETOP_BODY_PINS_NTHPIN:
        cqm = globals()[model_class_name]()
        case_top = cqm.make_top(spec.spec)
        case = cqm.make_case(spec.spec)
        pins = cqm.make_pins(spec.spec)
        npth_pins = cqm.make_npth_pins(spec.spec)

        parts.append(case_top, spec.spec["case_top_color_key"])
        parts.append(case, spec.spec["body_color_key"])
        parts.append(pins, spec.spec["pins_color_key"])
        parts.append(npth_pins, spec.spec.get("npth_pin_color_key", None))

    else:
        logging.error("No match found for the model_class")
        return 0

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=spec.id,
        parts=parts,
    )
    return 1
