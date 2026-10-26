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

from math import sqrt

import cadquery as cq


def make_radial_th(params):

    L = params["L"]  # overall height
    D = params["D"]  # body diameter
    d = params["d"]  # lead diameter
    F = params["F"]  # lead separation (center to center)
    ll = params["ll"]  # lead length
    la = params["la"]  # extra lead length of the anode
    bs = params["bs"]  # board separation
    if params["pin3"]:
        pin3_width = params["pin3"][0]
        pin3_x = params["pin3"][1]
        pin3_y = params["pin3"][2]

    pol = params["pol"]

    bt = 1.0  # flat part before belt
    if D > 4:
        bd = 0.2  # depth of the belt
    else:
        bd = 0.15  # depth of the belt
    bh = 1.0  # height of the belt
    bf = 0.3  # belt fillet

    tc = 0.2  # cut thickness for the bottom&top
    dc = D * 0.7  # diameter of the bottom&top cut
    ts = 0.1  # thickness of the slots at the top in the shape of (+)
    ws = 0.1  # width of the slots

    ef = 0.2  # top and bottom edges fillet
    rot = params["rotation"]

    bpt = 0.1  # bottom plastic thickness (not visual)
    tmt = ts * 2  # top metallic part thickness (not visual)

    # TODO: calculate width of the cathode marker mark from the body size
    ciba = 45.0  # angle of the cathode identification mark

    # TODO: calculate marker sizes according to the body size
    base_h = 2.0  # lenght of the (-) marker on the cathode mark
    base_w = 0.5  # rough width of the marker

    ef_s2 = ef / sqrt(2)
    ef_x = ef - ef / sqrt(2)

    def bodyp():
        return (
            cq.Workplane("XZ")
            .move(0, bs)
            .move(0, tc + bpt)
            .line(dc / 2.0, 0)
            .line(0, -(tc + bpt))
            .line(D / 2.0 - dc / 2.0 - ef, 0)
            .threePointArc((D / 2.0 - (ef_x), bs + (ef_x)), (D / 2.0, bs + ef))
            .line(0, bt)
            .threePointArc((D / 2.0 - bd, bs + bt + bh / 2.0), (D / 2.0, bs + bt + bh))
            .lineTo(D / 2.0, L + bs - ef)
            .threePointArc((D / 2.0 - (ef_x), L + bs - (ef_x)), (D / 2.0 - ef, L + bs))
            .lineTo(dc / 2.0, L + bs)
            .line(0, -(tc + tmt))
            .line(-dc / 2.0, 0)
            .close()
        )

    if pol:
        body = bodyp().revolve(360 - ciba, (0, 0, 0), (0, 1, 0))
        mark = bodyp().revolve(ciba, (0, 0, 0), (0, 1, 0))
    else:
        body = bodyp().revolve(360, (0, 0, 0), (0, 1, 0))
        # Hide mark inside the cap
        mark = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=bs + 1.0)
            .moveTo(0.0, 0.0)
            .rect(0.001, 0.001)
            .extrude(0.001)
        )

    # # fillet the belt edges
    BS = cq.selectors.BoxSelector
    # note that edges are selected from their centers
    b_r = D / 2.0 - bd  # inner radius of the belt

    try:
        # body = body.edges(BS((-0.5,-0.5, bs+bt-0.01), (0.5, 0.5, bs+bt+bh+0.01))).\
        #    fillet(bf)
        pos = D / 10
        body = body.edges(
            BS((-pos, -pos, bs + bt - 0.2), (pos, pos, bs + bt + bh + 0.01))
        ).fillet(bf)
    except:
        print("Error: Not filleting")

    # draw the plastic at the bottom
    bottom = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=bs + tc)
        .circle(dc / 2)
        .extrude(bpt)
    )
    body = body.union(bottom)
    # draw the metallic part at the top
    top = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=bs + L - tc - ts)
        .circle(dc / 2)
        .extrude(tmt)
    )

    # draw the slots on top in the shape of plus (+)
    top = (
        top.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .move(ws / 2, ws / 2)
        .line(0, D)
        .line(-ws, 0)
        .line(0, -D)
        .line(-D, 0)
        .line(0, -ws)
        .line(D, 0)
        .line(0, -D)
        .line(ws, 0)
        .line(0, D)
        .line(D, 0)
        .line(0, ws)
        .close()
        .cutBlind(-ts)
    )

    if pol:
        # b_r = D/2.-bd # inner radius of the belt
        # mark = mark.edges(BS((b_r/sqrt(2), 0, bs+bt-0.01),(b_r, -b_r/sqrt(2), bs+bt+bh+0.01))).\
        #       fillet(bf)

        body = body.rotate((0, 0, 0), (0, 0, 1), ciba / 2)
        mark = mark.rotate((0, 0, 0), (0, 0, 1), -ciba / 2)

        # draw the (-) marks on the mark
        n = int(L / (2 * base_h))  # number of (-) marks to draw
        points = []
        first_z = (L - (2 * n - 1) * base_h) / 2
        for i in range(n):
            points.append((0, (i + 0.25) * 2 * base_h + first_z))
        base = (
            cq.Workplane("YZ", (-D / 2, 0, bs))
            .pushPoints(points)
            .box(base_w, base_h, D * 2)
            .edges("|X")
            .fillet(base_w / 2.0 - 0.001)
        )

        base = base.cut(base.translate((0, 0, 0)).cut(mark))
        mark = mark.cut(base)
    else:
        body = body.rotate((0, 0, 0), (0, 0, 1), 180)
        # Hide base inside the cap
        base = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=bs + 1.0)
            .moveTo(0.0, 0.0)
            .rect(0.001, 0.001)
            .extrude(0.001)
        )

    # draw the pins
    pins = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=bs + tc)
        .center(-F / 2, 0)
        .circle(d / 2)
        .extrude(-(ll + tc))
        .center(F, 0)
        .circle(d / 2)
        .extrude(-(ll + tc + la + 0.1))
        .translate((0, 0, 0.1))
    )  # need overlap for fusion
    if params["pin3"]:
        pins = pins.union(
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=bs + tc)
            .circle(pin3_width / 2)
            .extrude(-(ll + tc + la + 0.1))
            .translate((pin3_x, pin3_y, 0.1))
        )  # need overlap for fusion)

    return (body, base, mark, pins, top)
