#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# * These are cadquery tools to export                                       *
# * generated models in STEP & VRML format.                                  *
# *                                                                          *
# * cadquery script for generating coil models in STEP AP214                 *
# * Copyright (c) 2025 KiCad Library Team                                    *
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

import cadquery as cq


def make_Vishay_CNY70(all_params):
    # some dimensions are hardcoded
    widthX, lengthY, heightZ = all_params["body_xyz"]

    pinX, pinY, pinZ = all_params["pin_xyz"]
    pinDX, pinDY = all_params["pin_dx_dy"]
    bodyVCutX = 1
    bodyVCutY = 1
    bodyThickness = 2

    caseVCutTop = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .rect(
            bodyVCutX,
            bodyVCutY,
        )
        .extrude(heightZ)
        .translate((0, lengthY / 2.0, 0))
    )
    caseVCutBot = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .rect(
            bodyVCutX,
            bodyVCutY,
        )
        .extrude(heightZ)
        .translate((0, -lengthY / 2.0, 0))
    )

    caseTopCut = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .rect(
            widthX - bodyThickness,
            lengthY - bodyThickness,
        )
        .extrude(1)
        .translate((0, 0, heightZ - 1))
    )
    # Create a 3D box based on the dimension variables above and fillet it
    case = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .box(
            widthX,
            lengthY,
            heightZ,
            centered=(True, True, False),
        )
        .edges("|Z")
        .fillet((pinX / pinY) / 2)
    )
    case = case.cut(caseVCutTop)
    case = case.cut(caseVCutBot)
    case = case.cut(caseTopCut)
    case = case.translate((pinDX / 2.0, -pinDY / 2.0, 0)).edges(">Z").fillet((0.2))

    em = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .circle(1.8 / 2)
        .extrude(heightZ - 0.9)
        .edges(">Z")
        .fillet((pinX / pinY) / 4)
        .translate((0, -pinDY / 2.0, 0.1))
    )

    dt = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .circle(1.8 / 2)
        .extrude(heightZ - 0.9)
        .edges(">Z")
        .fillet((pinX / pinY) / 4)
        .translate((pinDX, -pinDY / 2.0, 0.1))
    )

    text = (
        cq.Workplane("YZ")
        .workplane(offset=0, centerOption="CenterOfMass")
        .text("V69", 1.8, 0.1)
        .translate((widthX - pinDX + 0.61, -pinDY / 2, heightZ - 1))
    )

    text2 = (
        cq.Workplane("YZ")
        .workplane(offset=0, centerOption="CenterOfMass")
        .text("CNY 70", 1.6, 0.1)
        .translate((widthX - pinDX + 0.61, -pinDY / 2, heightZ - 3))
    )

    text3 = (
        cq.Workplane("YZ")
        .workplane(offset=0, centerOption="CenterOfMass")
        .text("809", 1.6, 0.1)
        .translate((widthX - pinDX + 0.61, -pinDY / 2, heightZ - 5))
    )

    pin = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .box(
            pinX,
            pinY,
            pinZ,
            centered=(True, True, False),
        )
        .translate((0, 0, -pinZ))
    )
    pin = pin + pin.translate((pinDX, 0, 0))
    pin = pin + pin.translate((0, -pinDY, 0))

    return (case, em, dt, text + text2 + text3, pin)
