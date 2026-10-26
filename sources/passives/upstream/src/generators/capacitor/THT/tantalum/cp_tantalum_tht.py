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
# *     Maurice https://launchpad.net/~easyw                                 *
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

from math import radians, sin, sqrt

import cadquery as cq


def make_tantalum_th(params):
    L = params["L"]  # body length
    W = params["W"]  # body width
    d = params["d"]  # lead diameter
    F = params["F"]  # lead separation (center to center)
    ll = params["ll"]  # lead length
    bs = params["bs"]  # board separation
    rot = params["rotation"]
    # dest_dir_pref = params['dest_dir_prefix']

    bend_offset_y = (sin(radians(60.0)) * d) / sin(radians(90.0))
    bend_offset_z = (sin(radians(30.0)) * d) / sin(radians(90.0))

    # Draw the leads
    zbelow = 3.0
    h = W + zbelow
    r = d * 1.5  # radius of pin bends
    arco = (1 - sqrt(2) / 2) * r  # helper factor to create midpoints of profile radii

    # create the path and sweep the leads
    path = (
        cq.Workplane("XZ")
        .lineTo(0, h - r - zbelow)
        .threePointArc((arco, h - arco - zbelow), (r, h - zbelow))
        .lineTo(params["F"] - r, h - zbelow)
        .threePointArc(
            (params["F"] - arco, h - arco - zbelow), (params["F"], h - r - zbelow)
        )
        .lineTo(params["F"], 0)
    )
    lead1 = (
        cq.Workplane("XY")
        .circle(d / 2)
        .sweep(path)
        .translate((-params["F"] / 2.0, 0, -W / 4.0))
    )
    leads = lead1

    oval_base_w = 2 * d
    oval_base_L = L * 0.7

    body = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=bs)
        .moveTo(-(oval_base_L / 2 - d), -oval_base_w / 2)
        .threePointArc((-oval_base_L / 2, 0), (-(oval_base_L / 2 - d), oval_base_w / 2))
        .line(oval_base_L - d * 2, 0)
        .threePointArc((oval_base_L / 2, 0), (oval_base_L / 2 - d, -oval_base_w / 2))
        .close()
        .extrude(d)
        .edges("<Z")
        .fillet(d / 4)
    )
    body = body.union(
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=bs + d)
        .moveTo(-(oval_base_L / 2 - d), -oval_base_w / 2)
        .threePointArc((-oval_base_L / 2, 0), (-(oval_base_L / 2 - d), oval_base_w / 2))
        .line(oval_base_L - d * 2, 0)
        .threePointArc((oval_base_L / 2, 0), (oval_base_L / 2 - d, -oval_base_w / 2))
        .close()
        .workplane(centerOption="CenterOfMass", offset=L)
        .circle(L / 2)
        .loft(combine=True)
    )
    middlepoint = (sin(radians(45.0)) * L / 2) / sin(radians(90.0))
    body = body.union(
        cq.Workplane("YZ")
        .moveTo(0, bs + d + L)
        .vLine(L / 2, forConstruction=False)
        .threePointArc(
            (middlepoint, bs + d + L + middlepoint),
            (L / 2, bs + d + L),
            forConstruction=False,
        )
        .close()
        .revolve()
    )
    plussize = L / 3
    plusthickness = plussize / 3
    pinmark = (
        cq.Workplane("XZ")
        .workplane(centerOption="CenterOfMass", offset=-L / 2 - 1)
        .moveTo(-plusthickness / 2 - L / 4, bs + d + L + plusthickness / 2)
        .line(0, plusthickness)
        .line(plusthickness, 0)
        .line(0, -plusthickness)
        .line(plusthickness, 0)
        .line(0, -plusthickness)
        .line(-plusthickness, 0)
        .line(0, -plusthickness)
        .line(-plusthickness, 0)
        .line(0, plusthickness)
        .line(-plusthickness, 0)
        .line(0, plusthickness)
        .close()
        .extrude(L + 2)
        .edges(">X")
        .edges("|Y")
        .fillet(plusthickness / 2.5)
        .edges("<X")
        .edges("|Y")
        .fillet(plusthickness / 2.5)
        .edges(">Z")
        .edges("|Y")
        .fillet(plusthickness / 2.5)
        .edges("<Z")
        .edges("|Y")
        .fillet(plusthickness / 2.5)
    )
    subtract_part = pinmark.translate((0, 0.01, 0)).cut(body)
    subtract_part = (
        subtract_part.translate((0, -0.02, 0)).cut(body).translate((0, 0.01, 0))
    )
    pinmark = pinmark.cut(subtract_part)
    # draw the body
    leads = leads.cut(body, clean=False)

    return (body, leads, pinmark)  # body, pins, mark
