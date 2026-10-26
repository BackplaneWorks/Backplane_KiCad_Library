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

import cadquery as cq

color_pin_mark = True


def make_radial_smd(params):

    L = params["L"]  # overall height
    D = params["D"]  # diameter
    A = params["A"]  # base width (x&y)
    H = params["H"]  # max width (x) with pins
    P = params["P"]  # distance between pins
    W = params["W"]  # pin width
    PM = params["PM"]  # hide pin marker

    if not color_pin_mark:
        PM = False

    c = 0.15  # pin thickness

    bh = L / 6  # belt start height
    br = min(D, L) / 20.0  # belt radius
    bf = br / 10  # belt fillet

    D2 = A + 0.1  # cut diameter

    h1 = 1.0  # bottom plastic height, cathode side
    h2 = 0.5  # bottom plastic base height, mid side
    h3 = 0.7  # bottom plastic height, anode side

    cf = 0.4  # cathode side corner fillet
    ac = min(1, A / 4)  # anode side chamfer

    ef = D / 15  # fillet of the top and bottom edges of the metallic body

    rot = params["rotation"]

    cimw = D / 2.0 * 0.7  # cathode identification mark width

    # draw aluminium the body
    body = (
        cq.Workplane("XZ", (0, 0, c + h2))
        .lineTo(D / 2.0, 0)
        .line(0, bh)
        .threePointArc((D / 2.0 - br, bh + br), (D / 2.0, bh + 2 * br))
        .lineTo(D / 2.0, L - c - h2)
        .line(-D / 2, 0)
        .close()
        .revolve()
    )

    # fillet the belt edges
    BS = cq.selectors.BoxSelector
    body = body.edges(BS((-0.1, -0.1, c + h2 + 0.1), (0.1, 0.1, L - 0.1))).fillet(bf)

    # fillet the top and bottom
    body = body.faces(">Z").fillet(ef).faces("<Z").fillet(ef)

    # draw the plastic base
    base = (
        cq.Workplane("XY", (0, 0, c))
        .moveTo(-A / 2.0, -A / 2.0)
        .line(A - ac, 0)
        .line(ac, ac)
        .line(0, A - 2 * ac)
        .line(-ac, ac)
        .line(-A + ac, 0)
        .close()
        .extrude(h1)
    )

    # fillet cathode side
    base = (
        base.edges(BS((-A, -A, 0), (-A / 2.0 + 0.01, -A / 2.0 + 0.01, c + h1 + 0.01)))
        .fillet(cf)
        .edges(BS((-A, A, 0), (-A / 2.0 + 0.01, A / 2.0 - 0.01, c + h1 + 0.01)))
        .fillet(cf)
    )

    # cut base center
    base = base.cut(
        cq.Workplane("XY", (0, 0, c + h2)).circle(D2 / 2.0).extrude(h1 - h2)
    )

    # cut anode side of the base
    base = base.cut(
        cq.Workplane("XY", (0, -A / 2.0, c + h3)).box(
            A / 2.0, A, h1 - h3, centered=(False, False, False)
        )
    )

    # draw pins
    pins = (
        cq.Workplane("XY")
        .moveTo(H / 2.0, -W / 2.0)
        .line(0, W)
        .lineTo(P / 2.0 + W / 2.0, W / 2.0)
        .threePointArc((P / 2.0, 0), (P / 2.0 + W / 2.0, -W / 2))
        .close()
        .extrude(c)
    )

    pins = pins.union(pins.rotate((0, 0, 0), (0, 0, 1), 180))

    # draw the cathode identification mark
    if PM:
        cim = cq.Workplane("XY", (-D / 2.0, 0, L - ef)).box(
            cimw, D, ef, centered=(False, True, False)
        )

        # do intersection
        cim = cim.cut(cim.translate((0, 0, 0)).cut(body))
        body.cut(cim)

        # offset mark so it does not intersect with part surface on WRL
        cim = cim.translate((-0.01, 0, 0.01))

    else:
        cim = None

    return (body, base, cim, pins)
