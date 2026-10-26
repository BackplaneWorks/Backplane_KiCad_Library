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
# * cadquery script for generating DIP socket models in STEP AP214           *
# * Copyright (c) 2017                                                       *
#      Terje Io https://github.com/terjeio                                  *
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
__author__ = "scripts: maurice, hyOzd, Stefan, Terje; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_model_piano_switch import dip_switch_piano, dip_switch_piano_cts
from .cq_model_pin_switch import dip_switch, dip_switch_low_profile
from .cq_model_smd_switch import (
    dip_smd_switch,
    dip_smd_switch_lowprofile,
    dip_smd_switch_lowprofile_jpin,
)
from .cq_model_smd_switch_copal import (
    dip_switch_copal_CHS_A,
    dip_switch_copal_CHS_B,
    dip_switch_copal_CVS,
)
from .cq_model_smd_switch_kingtek import (
    dip_switch_kingtek_dshp04tj,
    dip_switch_kingtek_dshp06ts,
)
from .cq_model_smd_switch_omron import dip_switch_omron_a6h, dip_switch_omron_a6s
from .cq_model_socket_turned_pin import dip_socket_turned_pin


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Make a model for each type of DIP part
    pin_range = range(spec.spec["pin_range_min"], spec.spec["pin_range_max"])
    for i in pin_range:
        # Choose the right module/method
        if i == 0:
            cqm = dip_switch_piano(spec.spec)
            offsets = (
                cqm.pin_rows_distance / 2.0,
                -(cqm.body_length / 2.0) + 1.40 + cqm.pin_width,
                cqm.body_board_distance,
            )
        elif i == 1:
            cqm = dip_switch_piano_cts(spec.spec)
            offsets = (
                cqm.pin_rows_distance / 2.0,
                -(cqm.body_length / 2.0) + 1.85 + cqm.pin_width,
                cqm.body_board_distance,
            )
        elif i == 2:
            cqm = dip_socket_turned_pin(spec.spec)
            offsets = cqm.offsets
        elif i == 3:
            cqm = dip_switch(spec.spec)
            offsets = (
                cqm.pin_rows_distance / 2.0,
                -(cqm.body_length / 2.0) + 1.80 + cqm.pin_width,
                cqm.body_board_distance,
            )
        elif i == 4:
            cqm = dip_switch_low_profile(spec.spec)
            offsets = (
                cqm.pin_rows_distance / 2.0,
                -(cqm.body_length / 2.0) + 1.50 + cqm.pin_width,
                cqm.body_board_distance,
            )
        elif i == 5:
            cqm = dip_smd_switch(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 6:
            cqm = dip_smd_switch_lowprofile(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 7:
            cqm = dip_smd_switch_lowprofile_jpin(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 8:
            cqm = dip_switch_copal_CHS_A(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 9:
            cqm = dip_switch_copal_CHS_B(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 10:
            cqm = dip_switch_copal_CVS(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 11:
            cqm = dip_switch_omron_a6h(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 12:
            cqm = dip_switch_omron_a6s(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 13:
            cqm = dip_switch_kingtek_dshp04tj(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)
        elif i == 14:
            cqm = dip_switch_kingtek_dshp06ts(spec.spec)
            offsets = (0, 0, cqm.pin_thickness / 2.0)

        # Make the parts of the model
        body = cqm.make_body()
        pins = cqm.make_pins()
        buttons = None
        mark = None

        if i != 2:
            buttons = cqm.make_buttons()
            mark = cqm.make_pinmark(cqm.button_width + 0.2)

        # Put the parts in the correct position relative to the pads on the board
        if i != 2:
            rotation = 90
        else:
            rotation = -90

        parts = export_tools.AssemblyParts(
            [
                (body, spec.spec["body_color_key"]),
                (pins, spec.spec["pin_color_key"]),
                (buttons, spec.spec["button_color_key"]),
                (mark, spec.spec["mark_color_key"]),
            ]
        )
        parts.rotate(rotation)
        parts.translate(offsets)

        export_tools.export(
            generator_name=generator_name,
            lib_name=spec.spec["destination_dir"],
            model_name=cqm.makeModelName(spec.id),
            parts=parts,
        )
    return len(pin_range)
