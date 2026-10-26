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


def make_Vishay_TCRT5000(all_params):
    # some dimensions are hardcoded
    # and some magic is also involved..
    widthX, lengthY, heightZ = 10.2, 5.8, 3

    pinX, pinY, pinZ = all_params["pin_xyz"]
    pinDX, pinDY = all_params["pin_dx_dy"]
    bodyChamfer = 1.65
    bodyVClipX = 0.95
    bodyVClipY = 0.7
    bodyVClipYMax = 1.2
    circRad = 0.45

    pts = [
        (bodyVClipYMax, -1.8),
        (bodyVClipYMax + 0.5 + 0.7, -1.6),
        (bodyVClipYMax + 0.5 + 0.7, -(3)),
        (bodyVClipYMax + 0.5, -(3)),
        (bodyVClipYMax, -1.8),
    ]

    caseVClipTopTriangle = (
        cq.Workplane("YZ")
        .polyline(pts)
        .close()
        .extrude(bodyVClipX)
        .faces("<Z")
        .edges("|X")
        .chamfer((0.1))
        .translate((-bodyVClipX / 2, 0.7, 0))
    )

    caseVClipTop = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .rect(
            bodyVClipX,
            bodyVClipY,
        )
        .extrude(heightZ + 3)
        .translate((0, (lengthY - bodyVClipY) / 2.0, -heightZ))
    )
    caseVClipTop = caseVClipTop.faces("<Z").edges("|X").fillet(
        (0.1)
    ) + caseVClipTopTriangle.rotate((0, 0, 0), (0, 0, 1), 180).translate(
        (0, lengthY - bodyVClipY / 2.0, 0)
    )

    caseVClipBot = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .rect(
            bodyVClipX,
            bodyVClipY,
        )
        .extrude(heightZ + 3)
        .translate((0, -(lengthY - bodyVClipY) / 2.0, -heightZ))
    )
    caseVClipBot = caseVClipBot.faces("<Z").edges("|X").fillet(
        (0.1)
    ) + caseVClipTopTriangle.translate((0, -(lengthY - bodyVClipY / 2.0), 0))

    caseVCircleBot = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .circle(circRad)
        .extrude(1.5)
        .translate((-widthX / 2 + circRad, -(lengthY) / 2.0 + circRad, -heightZ / 2))
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
        .faces(">Z")
        .rect(widthX, lengthY)
        .workplane(offset=heightZ / 2)
        .rect(widthX / 1.3, lengthY / 1.8)
        .loft()
        .faces("<X")
        .edges("|Z")
        .fillet((pinX / pinY) / 2)
        .faces(">X")
        .edges("|Z")
        .chamfer((bodyChamfer))
    )
    caseTop = (
        cq.Workplane("XY")
        .box(1, lengthY / 2, heightZ + 3)
        .translate((0, 0, heightZ + 1))  # To meet 7mm
        .faces(">Z")
        .edges("|X")
        .fillet(lengthY / 5)
    )
    case = case.union(caseVClipTop)
    case = case.union(caseVClipBot)
    case = case.union(caseVCircleBot)
    case = (
        (case + caseTop)
        .translate((pinDX / 2.0, -pinDY / 2.0, 0))
        .edges(">Z")
        .fillet((0.2))
    )

    caseBottomCut = cq.Workplane("XY").rect(widthX / 3, lengthY / 0.5).extrude(0.5)

    caseBottomCutUpper = cq.Workplane("XY").rect(0.15, lengthY / 0.5).extrude(1)

    case = case.cut(caseBottomCut.translate((circRad, 0, 0)))
    case = case.cut(
        caseBottomCutUpper.translate(((pinDX / 2.0) - bodyVClipX + 0.4, 0, 0))
    )
    case = case.cut(
        caseBottomCutUpper.translate(((pinDX / 2.0) + bodyVClipX - 0.4, 0, 0))
    )

    caseBottomCutSec = cq.Workplane("XY").rect(widthX / 6, lengthY / 0.5).extrude(0.5)
    case = case.cut(
        caseBottomCutSec.translate(
            (widthX / 12 + (pinDX / 2.0) + bodyVClipX - 0.4, 0, 0)
        )
    )
    case = case.cut(
        caseBottomCutSec.translate((widthX / 3 + (pinDX / 2.0) + bodyVClipX, 0, 0))
    )

    em = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .circle(1.5)
        .extrude(heightZ + 2.8)
        .edges(">Z")
        .fillet(1.5)
        .translate((0.6, -pinDY / 2.0, 0.6))
    )

    dt = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .circle(1.5)
        .extrude(heightZ + 2.8)
        .edges(">Z")
        .fillet(1.5)
        .translate((pinDX - 0.6, -pinDY / 2.0, 0.6))
    )

    text = (
        cq.Workplane("YZ")
        .workplane(offset=0, centerOption="CenterOfMass")
        .text("V19832", 0.6, 0.1)
        .translate((pinDX + (widthX - pinDX) / 2 - 0.09, -pinDY / 2, heightZ / 2))
    )
    # Some black magic here too
    textLoft = (
        cq.Workplane("XZ")
        .workplane(offset=0, centerOption="CenterOfMass")
        .text("TCRT5000", 1.5, 0.1)
        .rotate((0, 0, 0), (1, 0, 0), -41)
        .translate(
            (
                (widthX - pinDX) / 2 + 0.35,
                -(lengthY - pinDY) - 0.85 + 0.7,
                heightZ + 0.75,
            )
        )
    )

    pin = (
        cq.Workplane("XY")
        .workplane(offset=0, centerOption="CenterOfMass")
        .box(
            pinX,
            pinY,
            pinZ + 0.6,
            centered=(True, True, False),
        )
        .translate((0, 0, -pinZ))
    )
    pin = pin + pin.translate((pinDX, 0, 0))
    pin = pin + pin.translate((0, -pinDY, 0))

    return (case, em, dt, text.union(textLoft), pin)
