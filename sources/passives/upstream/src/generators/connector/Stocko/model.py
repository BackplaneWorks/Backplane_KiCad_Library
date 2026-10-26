#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
# * CadQuery script for generating Stocko models in STEP AP214               *
# *   Copyright (c) 2016                                                     *
# * Bartosz Balcerzak  https://github.com/bartosz.maciej.balcerzak           *
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
__author__ = "scripts: bartosz.maciej.balcerzak and hyOzd; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec


def make_connector(name, params):
    """
    Originally created by Bartosz Balcerzak  https://github.com/bartosz.maciej.balcerzak
    Generates body and pins for a given Stocko connector.
    """
    model_name = name
    full_model_name = name + "-6-0-{}{:02d}_1x{}_P2.50mm_Vertical".format(
        params["pins"], params["pins"], params["pins"]
    )

    body = (
        cq.Workplane("XY")
        .move(-params["outline_x"], 0)
        .box(
            (params["pitch"] * (params["pins"] - 1)) + 2 * params["outline_x"],
            params["base_w"],
            params["base_h"],
            centered=(False, True, False),
        )
    )
    body = (
        body.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .rect(
            params["pitch"] * (params["pins"] - 1)
            + 2 * params["outline_x"]
            - params["lr_sides_t"],
            params["base_w"] - params["tb_sides_t"],
        )
        .cutBlind(-params["depth"])
        .faces(">Z")
        .edges("not(<X or >X or <Y or >Y)")
        .chamfer(0.7)
    )
    body = body.edges("|Z and >X").fillet(0.5)
    body = body.edges("|Z and <X").fillet(0.5)
    body = (
        body.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .center(0, -params["base_w"] / 2 + params["base_cutout"] / 2)
        .rect(
            params["pitch"] * (params["pins"] - 1)
            + 2 * (params["outline_x"] - params["leaf"]),
            params["base_cutout"],
        )
        .cutThruAll()
    )
    if params["top_cutout"]:
        body = (
            body.faces(">Y")
            .workplane(centerOption="CenterOfMass")
            .center(0, 6.5)
            .rect(params["t_cutout_w"], params["t_cutout_h"])
            .cutThruAll()
        )
    for x in range(params["pins"]):
        temp = (params["b_cutout_long_w"] - params["b_cutout_short_w"]) / 2
        body = (
            body.faces(">Y")
            .workplane(centerOption="CenterOfBoundBox")
            .center(
                ((params["pitch"] * (params["pins"] - 1) + 2 * params["outline_x"]) / 2)
                - params["outline_x"]
                - (params["b_cutout_long_w"] / 2)
                - x * params["pitch"],
                -7,
            )
            .lineTo(params["b_cutout_long_w"], 0)
            .lineTo(params["b_cutout_long_w"] - temp, params["b_cutout_h"])
            .lineTo(temp, params["b_cutout_h"])
            .close()
            .cutThruAll()
        )

    total_pin_length = (
        params["pin"]["length_above_board"] + params["pin"]["length_below_board"]
    )
    pin = (
        cq.Workplane("XY")
        .workplane(
            centerOption="CenterOfMass", offset=-params["pin"]["length_below_board"]
        )
        .box(
            params["pin"]["width"],
            params["pin"]["width"],
            total_pin_length,
            centered=(True, True, False),
        )
    )

    pin = pin.edges("#Z").chamfer(params["pin"]["end_chamfer"])
    pins_union = cq.Workplane("XY").workplane(
        centerOption="CenterOfMass", offset=-params["pin"]["length_below_board"]
    )

    for x in range(params["pins"]):
        pins_union = pins_union.union(pin.translate((x * params["pitch"], 0, 0)))

    return (body, pins_union)


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    # Generate the model
    body, pins = make_connector(spec.id, spec.spec)

    # Create the file name based on the rows and pins
    file_name = spec.id + "-6-0-{}{:02d}_1x{}_P2.50mm_Vertical".format(
        spec.spec["pins"],
        spec.spec["pins"],
        spec.spec["pins"],
    )

    parts = export_tools.AssemblyParts(
        [
            (body, spec.spec["body_color_key"]),
            (pins, spec.spec["pins_color_key"]),
        ]
    )

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.spec["destination_dir"],
        model_name=file_name,
        parts=parts,
    )
    return 1
