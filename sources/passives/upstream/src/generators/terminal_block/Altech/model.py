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

__title__ = "make Altech connector 3D models"
__author__ = "Stefan, based on Converter_DCDC script"
__Comment__ = (
    "make Altech connectors 3D models exported to STEP and VRML for Kicad StepUP script"
)

___ver___ = "1.3.4 18/06/2020"

import math

import cadquery as cq

from generators.tools.model import export_tools
from generators.tools.spec.legacy_model_spec import LegacyModelSpec


def make_case_AK300(params, pinnumber):
    W = params["W"]  # package width
    H = params["H"]  # package height
    WD = params["WD"]  # > Y distance form pin center to package edge
    A1 = params["A1"]  # Body seperation height
    PE = params["PE"]  # Distance from edge to pin
    PS = params["PS"]  # Pin distance
    SW = params["SW"]  # Blender width
    rotation = params["rotation"]  # rotation if required

    lw = (2.0 * PE) + ((pinnumber - 1) * PS)

    #
    # Create a plygon of the shape and extrude it along the Y axis
    #
    pts = []
    pts.append((0.0, A1))
    #
    pts.append((0.0 - WD, A1))
    #
    pts.append((0.0 - WD, (A1 + H) - WD))
    #
    pts.append((0.0, A1 + H))
    #
    pts.append(((W - WD) - 0.5, A1 + H))
    #
    pts.append((W - WD, A1 + (H - 0.5)))
    #
    pts.append((W - WD, A1))
    #
    case = cq.Workplane("YZ").workplane(offset=0 - PE).polyline(pts).close().extrude(lw)
    #
    #
    A1A = A1 + 0.2
    bb = WD - 0.4
    SL = SW / 1.1  # Screw diameter

    px = 0.0

    for i in range(0, pinnumber):
        pp = (
            cq.Workplane("XY")
            .workplane(offset=A1A)
            .moveTo(px, 0.0 - (WD / 2.0))
            .rect(SW + 0.4, bb)
            .extrude(1.1 * H)
        )
        case = case.cut(pp)
        # Cut out screw header
        po = (
            cq.Workplane("XY")
            .workplane(offset=A1)
            .moveTo(0, 0)
            .circle(SL / 2.0, False)
            .extrude(W)
        )
        po = po.rotate((0, 0, 0), (1, 0, 0), 0 - 45.0)
        po = po.translate((px, 0.0, H / 2.0))
        case = case.cut(po)

        px = px + PS

    #    case = case.faces("<Y").edges(">X").fillet(0.1)
    case = case.faces("<X").fillet(0.2)
    case = case.faces(">X").fillet(0.2)
    case = case.faces(">Z").fillet(0.2)
    case = case.faces("<Y").edges(">Z").fillet(0.2)

    if rotation > 0.01:
        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

    return case


def make_pins_AK300(params, pinnumber):
    W = params["W"]  # package width
    H = params["H"]  # package height
    WD = params["WD"]  # > Y distance form pin center to package edge
    A1 = params["A1"]  # Body separation height
    PE = params["PE"]  # Distance from edge to pin
    PS = params["PS"]  # Pin distance
    PD = params["PD"]  # Pin diameter
    PL = params["PL"]  # Pin diameter
    PF = params["PF"]  # Pin form
    SW = params["SW"]  # Blender width
    rotation = params["rotation"]  # rotation if required

    px = 0.0
    pins = None

    for i in range(0, pinnumber):
        if PF == "round":
            pint = (
                cq.Workplane("XY")
                .workplane(offset=A1)
                .moveTo(px, 0.0)
                .circle(PD[0] / 2.0, False)
                .extrude(0 - (A1 + PL))
            )
            pint = pins.faces("<Z").fillet(PD[0] / 2.2)
        else:
            pint = (
                cq.Workplane("XY")
                .workplane(offset=A1)
                .moveTo(px, 0.0)
                .rect(PD[0], PD[1])
                .extrude(0 - (A1 + PL))
            )
            if PD[0] < PD[1]:
                pint = pint.faces("<Z").fillet(PD[0] / 2.2)
            else:
                pint = pint.faces("<Z").fillet(PD[1] / 2.2)

        if i == 0:
            pins = pint
        else:
            pins = pins.union(pint, glue=True)

        A1A = A1 + 0.2
        bb0 = WD - 0.5
        bb0 = bb0 / math.cos(math.radians(45.0))
        SL = SW / 1.1  # Screw diameter

        bb = bb0
        pl = (
            cq.Workplane("XY")
            .workplane(offset=0.0)
            .moveTo(0.0, 0.0)
            .rect(SW, bb)
            .extrude(0.0 - (WD))
        )
        # Make hole
        bb1 = SW - (SW * 0.2)

        plu = (
            cq.Workplane("XY")
            .workplane(offset=0.0 + 0.1)
            .moveTo(0.0, 0.0 - ((bb / 2.0) - (bb1 / 2) - (SW * 0.2)))
            .rect(bb1, bb1)
            .extrude(0.0 - (1.1 * H + 0.2))
        )
        pl = pl.cut(plu)

        plu = (
            cq.Workplane("ZX")
            .workplane(offset=0.0 - (WD - SL))
            .moveTo(0.0 - (bb / 2.0), 0.0)
            .circle(SW / 2.5, False)
            .extrude(SL)
        )
        pl = pl.union(plu, clean=False, glue=True)

        # Add the screw head
        bba = (W - WD) / math.cos(math.radians(45.0))
        bba = bba * 0.85
        pl = (
            pl.faces(">Y")
            .workplane(centerOption="CenterOfBoundBox")
            .center(0, A1 - SL / 2.0)
            .circle(SL / 2.0)
            .extrude(SL + (SL / 4.0))
        )
        pl = (
            pl.faces(">Y")
            .workplane(centerOption="CenterOfBoundBox", invert=True)
            .rect(SL / 4.0, 10.0)
            .cutBlind(SL / 8.0)
        )
        pl = pl.faces(">Y").edges("%CIRCLE").fillet(SL / 8.0)

        # Rotate and move the pin into the correct position
        pl = pl.rotate((0, 0, 0), (1, 0, 0), 45.0)
        pl = pl.translate(
            (px, 0.0 - (WD / 2.0) + 0.1, A1 + ((H - WD) / 2.0) + WD - 0.3)
        )

        pins = pins.union(pl, glue=True)

        px = px + PS

    # Add any rotation requested via the settings
    if rotation > 0.01:
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return pins


def create_models(spec: LegacyModelSpec, generator_name: str) -> int:
    """Create the 3D models.

    Args:
        spec: The spec of the part(s) to generate.
        generator_name: The name of the generator.

    Returns:
        The number of models generated.
    """
    body = make_case_AK300(spec.spec, spec.spec["pin_number"])
    pins = make_pins_AK300(spec.spec, spec.spec["pin_number"])

    parts = export_tools.AssemblyParts(
        [
            (body, "black body"),
            (pins, "metal grey pins"),
        ]
    )

    export_tools.export(
        generator_name=generator_name,
        lib_name="TerminalBlock_Altech",
        model_name=spec.id,
        parts=parts,
    )
    return 1
