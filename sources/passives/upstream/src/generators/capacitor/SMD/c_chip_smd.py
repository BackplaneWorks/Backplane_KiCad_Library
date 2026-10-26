#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This was originaly derived from a cadquery script for generating PDIP models in X3D format
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
## the script will generate STEP and VRML parametric models
## to be used with kicad StepUp script
#
# *                                                                          *
# * cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
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
# *   it under the terms of the GNU General Public License (GPL)             *
# *   as published by the Free Software Foundation; either version 2 of      *
# *   the License, or (at your option) any later version.                    *
# *   for detail see the LICENCE text file.                                  *
# *                                                                          *
# *   This program is distribuited in the hope that it will be useful,        *
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
__author__ = (
    "scripts: maurice & Frank/Shack; models: see cq_model files; update: jmwright"
)
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

import cadquery as cq


def make_chip(params):
    # Dimensions for chip capacitors
    length = params["length"]  # package length
    width = params["width"]  # package width
    height = params["height"]  # package height

    pin_band = params["pin_band"]  # pin band
    pin_thickness = params["pin_thickness"]  # pin thickness
    if pin_thickness == "auto":
        pin_thickness = pin_band / 10.0

    edge_fillet = params["edge_fillet"]  # fillet of edges
    if edge_fillet == "auto":
        edge_fillet = pin_thickness

    # Create a 3D box based on the dimension variables above and fillet it
    case = (
        cq.Workplane("XY")
        .workplane(offset=pin_thickness)
        .box(
            length - 2 * pin_band,
            width - 2 * pin_thickness,
            height - 2 * pin_thickness,
            centered=(True, True, False),
        )
        .edges("|X")
        .fillet(edge_fillet)
    )

    # Create a 3D box based on the dimension variables above and fillet it
    pin1 = cq.Workplane("XY").box(pin_band, width, height)
    pin1 = pin1.edges("|X").fillet(edge_fillet)
    pin1 = pin1.translate((-length / 2 + pin_band / 2, 0, height / 2))
    pin2 = cq.Workplane("XY").box(pin_band, width, height)
    pin2 = pin2.edges("|X").fillet(edge_fillet)
    pin2 = pin2.translate((length / 2 - pin_band / 2, 0, height / 2))
    pins = pin1.union(pin2)
    # body_copy.ShapeColor=result.ShapeColor
    case = case.cut(pins)

    return (case, pins)
