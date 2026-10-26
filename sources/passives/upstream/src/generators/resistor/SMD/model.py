# -*- coding: utf8 -*-
#!/usr/bin/python
#
# The original, CadQuery 1.x based script was derived from a CadQuery
# script for generating PDIP models in X3D format.
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
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
# * Copyright (c) 2015                                                       *
# *     Maurice https://launchpad.net/~easyw                                 *
# * Copyright (c) 2021                                                       *
# *     Update 2021                                                          *
# *     jmwright (https://github.com/jmwright)                               *
# *     Work sponsored by KiCAD Services Corporation                         *
#           (https://www.kipro-pcb.com/)                                    *
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

__title__ = "Make chip Resistors 3D models"
__author__ = "maurice, jmwright"
__Comment__ = "Make chip Resistors 3D models exported to STEP and VRML"

___ver___ = "2.0.0"

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec

dest_dir_prefix = "Resistor_SMD.3dshapes"

"""
Generates the CadQuery model that will be exported.
"""


def make_chip(model, all_params):
    # dimensions for chip capacitors
    length = all_params["length"]  # package length
    width = all_params["width"]  # package width
    height = all_params["height"]  # package height

    pin_band = all_params["pin_band"]  # pin band
    pin_thickness = all_params["pin_thickness"]  # pin thickness
    if pin_thickness == "auto":
        pin_thickness = height / 10.0

    edge_fillet = all_params["edge_fillet"]  # fillet of edges
    if edge_fillet == "auto":
        edge_fillet = pin_thickness

    # Create a 3D box based on the dimension variables above and fillet it
    case = (
        cq.Workplane("XY")
        .workplane(offset=pin_thickness)
        .box(
            length - 2 * pin_thickness,
            width,
            height - 2 * pin_thickness,
            centered=(True, True, False),
        )
    )
    top = (
        cq.Workplane("XY")
        .workplane(offset=height - pin_thickness)
        .box(length - 2 * pin_band, width, pin_thickness, centered=(True, True, False))
    )

    # Create a 3D box based on the dimension variables above and fillet it
    pin1 = cq.Workplane("XY").box(pin_band, width, height)
    pin1 = pin1.edges("|Y").fillet(edge_fillet)
    pin1 = pin1.translate((-length / 2 + pin_band / 2, 0, height / 2)).rotate(
        (0, 0, 0), (0, 0, 1), 0
    )
    pin2 = cq.Workplane("XY").box(pin_band, width, height)
    pin2 = pin2.edges("|Y").fillet(edge_fillet)
    pin2 = pin2.translate((length / 2 - pin_band / 2, 0, height / 2)).rotate(
        (0, 0, 0), (0, 0, 1), 0
    )
    pins = pin1.union(pin2)
    # body_copy.ShapeColor=result.ShapeColor

    # extract case from pins
    # case = case.cut(pins)
    pins = pins.cut(case)

    return (case, top, pins)


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    body, top, pins = make_chip(spec.id, spec.spec)

    parts = export_tools.AssemblyParts(
        [
            (body, "white body"),
            (pins, "metal grey pins"),
            (top, "resistor black body"),
        ]
    )

    export_tools.export(
        generator_name=generator_name,
        lib_name="Resistor_SMD",
        model_name=spec.id,
        parts=parts,
    )
    return 1
