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
# *   Maurice https://launchpad.net/~easyw                                   *
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
__author__ = "scripts: maurice and hyOzd; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_audio_jack_cui import cq_audio_jack_cui
from .cq_audio_jack_ledino import cq_audio_jack_ledino
from .cq_audio_jack_neutrik import cq_audio_jack_neutrik
from .cq_audio_jack_qingpu import cq_audio_jack_qingpu


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Generate the correct model
    if "CUI" in spec.spec["model_name"]:
        cqm = cq_audio_jack_cui()
        body_top = cqm.make_top_Jack_3_5mm_CUI(spec.spec)
        body = cqm.make_case_Jack_3_5mm_CUI(spec.spec)
        pins = cqm.make_pin(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif "Ledino" in spec.spec["model_name"]:
        cqm = cq_audio_jack_ledino()
        body_top = cqm.make_top_Jack_3_5mm_Ledino(spec.spec)
        body = cqm.make_case_Jack_3_5mm_Ledino(spec.spec)
        pins = cqm.make_pin(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    elif "Neutrik" in spec.spec["model_name"]:
        cqm = cq_audio_jack_neutrik()
        body_top = cqm.make_top_Jack_3_5mm_Neutrik(spec.spec)
        body = cqm.make_case_Jack_3_5mm_Neutrik(spec.spec)
        pins = cqm.make_pin(spec.spec)
        npth_pins = cqm.make_npth_pins_dummy(spec.spec)
    else:
        cqm = cq_audio_jack_qingpu()
        body_top = cqm.make_top_type(spec.spec)
        body = cqm.make_case_type(spec.spec)
        pins = cqm.make_pin(spec.spec)
        npth_pins = cqm.make_npthpin_type(spec.spec)

    parts = export_tools.AssemblyParts(
        [
            (body_top, spec.spec["body_top_color_key"]),
            (body, spec.spec["body_color_key"]),
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
