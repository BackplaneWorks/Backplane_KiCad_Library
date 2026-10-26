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
# * cadquery script for generating JST-XH models in STEP AP214               *
# * Copyright (c) 2015                                                       *
# *     Maurice https://launchpad.net/~easyw                                 *
# * Copyright (c) 2016                                                       *
# *     Rene Poeschl https://github.com/poeschlr                             *
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

__title__ = "generator for wuerth smt mounting hardware with inner through holes 3D models exported to STEP and VRML"
__author__ = "scripts: maurice and hyOzd; models: see poeschlr; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

from .cq_wuerth_smt_spacer import generate


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    for part in spec.spec["parts"]:
        # Make the parts of the model
        body = generate(spec.spec, part)

        # Assemble the filename
        if "id" in spec.spec["mechanical"]:
            size = str(spec.spec["mechanical"]["id"])
        elif "ext_thread" in spec.spec["mechanical"]:
            size = str(spec.spec["mechanical"]["ext_thread"]["od"])

        if "M" not in size:
            size = "{}mm".format(size)

        td = ""
        size_prefix = ""
        if "thread_depth" in spec.spec["parts"][part]:
            td = "_ThreadDepth{}mm".format(spec.spec["parts"][part]["thread_depth"])
        elif "ext_thread" in spec.spec["mechanical"]:
            size_prefix = "External"

        h = (
            spec.spec["parts"][part]["h"]
            if "h" in spec.spec["parts"][part]
            else spec.spec["parts"][part]["h1"]
        )

        suffix = ""
        if "suffix" in spec.spec:
            suffix = "_{}".format(spec.spec["suffix"])

        file_name = "Mounting_Wuerth_{series}-{size_prefix}{size}_H{h}mm{td}{suffix}_{mpn}".format(
            series=spec.spec["series_prefix"],
            size_prefix=size_prefix,
            size=size,
            h=h,
            td=td,
            suffix=suffix,
            mpn=part,
        )

        lib_name = "Mounting_Wuerth.3dshapes"

        parts = export_tools.AssemblyParts(
            [
                (body, "metal grey pins"),
            ]
        )

        export_tools.export(
            generator_name=generator_name,
            lib_name=lib_name,
            model_name=file_name,
            parts=parts,
        )

    return len(spec.spec["parts"])
