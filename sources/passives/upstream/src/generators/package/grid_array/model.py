#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating QFP models in
# X3D format.
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#
# Dimensions are from Jedec MS-026D document.
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

__title__ = "make BGA ICs 3D models"
__author__ = "maurice, hyOzd, jmwright"
__Comment__ = "make BGA ICs 3D models exported to STEP and VRML"

___ver___ = "2.0.0"

from math import radians, tan

import cadquery as cq

from generators.tools.model import export_tools

from .pad_factory import make_pad_factory
from .spec import GridArraySpec


def make_plg(
    wp: cq.Workplane, rw: float, rh: float, cv1: float, cv: float
) -> cq.Workplane:
    """
    Creates a rectangle with chamfered corners.
    wp: workplane object
    rw: rectangle width (x)
    rh: rectangle height (y)
    cv1: chamfer value for 1st corner (top left)
    cv: chamfer value for other corners
    """
    x = rw / 2.0
    y = rh / 2.0
    points = [
        (-x, y - cv1),
        (-x + cv1, y),
        (x - cv, y),
        (x, y - cv),
        (x, -y + cv),
        (x - cv, -y),
        (-x + cv, -y),
        (-x, -y + cv),
        (-x, y - cv1),
    ]
    return wp.polyline(points, includeCurrent=False).wire()


def create_models(spec: GridArraySpec, generator_name: str) -> int:
    """Create the model corresponding to the spec.

    Args:
        spec: the grid array specification.
        generator_name: The name of this generator.

    Returns:
        The number of models generated.
    """
    if not spec.has_3d_data:
        return 0

    ef = spec.body_fillet
    cff = spec.first_corner_chamfer
    cf = spec.corner_chamfer
    d = spec.body_size_y
    e = spec.body_size_x
    d1 = spec.mold_size_y
    e1 = spec.mold_size_x
    a1 = spec.body_pcb_gap
    a2 = spec.mold_size_z_bottom
    a = spec.overall_height
    sp = spec.seating_plane
    b = spec.ball_diameter
    if b is None:
        raise KeyError("Cannot generate 3D model without a `ball_diameter` parameter.")

    sphere_r = b / 2 * (1.05)  # added extra 0.5% diameter for fusion
    s_center = (0, 0, 0)
    sphere = cq.Workplane("XY", s_center).sphere(sphere_r)
    bpin = sphere.translate((0, 0, b / 2 - sp))

    pads = list(make_pad_factory(spec).pads())
    pin_positions: list[cq.Location] = []
    for pad in pads:
        pos = pad.position
        pin_positions.append(cq.Location(cq.Vector(pos.x, -pos.y)))

    # Create all pins in a single, efficient operation
    merged_pins = (
        cq.Workplane("XY")
        .pushPoints(pin_positions)
        .each(lambda loc: bpin.val().located(loc), combine="a")  # type: ignore
    )

    # first pin indicator is created with a cylindrical pocket
    marker_depth = 0.05  # fixed 50 um for all markers
    marker_diameter = max(d, e) / 10.0
    if min(d, e) < 5 * marker_diameter:
        marker_edge_clearance = marker_diameter / 4.0
    else:
        marker_edge_clearance = marker_diameter / 2.0
    if spec.molded:
        the = 24
        d1_t = d1 - 2 * tan(radians(the)) * (a - a1 - a2)
        e1_t = e1 - 2 * tan(radians(the)) * (a - a1 - a2)
        # draw the case
        cw = e - 2 * a1
        ch = d - 2 * a1
        case_bot = cq.Workplane("XY").workplane(offset=0)
        case_bot = make_plg(case_bot, cw, ch, cff, cf)
        case_bot = case_bot.extrude(a2 - 0.01)
        case_bot = case_bot.translate((0, 0, a1))

        case = cq.Workplane("XY").workplane(offset=a1)
        case = make_plg(case, e1, d1, 3 * cf, 3 * cf)
        case = case.extrude(0.01)
        case = case.faces(">Z").workplane()
        case = make_plg(case, e1, d1, 3 * cf, 3 * cf).workplane(offset=a - a2 - a1)
        case = make_plg(case, e1_t, d1_t, 3 * cf, 3 * cf).loft(ruled=True)
        # fillet the bottom vertical edges
        if ef != 0:
            case_bot = case_bot.edges("|Z").fillet(ef)
        # fillet top and side faces of the top molded part
        if ef != 0:
            BS = cq.selectors.BoxSelector
            case = case.edges(
                BS((-e1 / 2, -d1 / 2, a2 + 0.001), (e1 / 2, d1 / 2, a + 0.001))  # type: ignore
            ).fillet(ef)
        case = case.translate((0, 0, a2 - 0.01))
        pinmark = (
            cq.Workplane(
                "XZ",
                (
                    -e / 2 + marker_edge_clearance + marker_diameter / 2,
                    d / 2 - marker_edge_clearance - marker_diameter / 2,
                    a,
                ),
            )
            .rect(marker_diameter / 2, -marker_depth, False)
            .revolve()
        )
        pinmark = pinmark.translate(
            (
                (e - e1_t) / 2 + marker_edge_clearance + cff,
                (d - d1_t) / 2 - marker_edge_clearance - cff,
                -sp,
            )
        )

    else:
        a2 = a - a1  # body height
        case = cq.Workplane("XY").box(e, d, a2)  # NO margin, pins don't emerge
        if ef != 0:
            case.edges("|X").fillet(ef)
            case.edges("|Z").fillet(ef)
        # translate the object
        case = case.translate((0, 0, a2 / 2 + a1 - sp)).rotate((0, 0, 0), (0, 0, 1), 0)
        pinmark = (
            cq.Workplane(
                "XZ",
                (
                    -e / 2 + marker_edge_clearance + marker_diameter / 2,
                    d / 2 - marker_edge_clearance - marker_diameter / 2,
                    marker_depth,
                ),
            )
            .rect(marker_diameter / 2, -2 * marker_depth, False)
            .revolve()
            .translate((0, 0, a2 + a1 - sp - marker_depth + 0.002))
        )
        case_bot = None

    if spec.marker is not None:
        pad_position_found = False
        for pad in pads:
            if pad.name == spec.marker:
                pad_position_found = True
                pos = pad.position
                pinmark = (
                    cq.Workplane("XY", (pos.x, -pos.y, a))
                    .circle(marker_diameter / 2, False)
                    .extrude(-marker_depth)
                )
                break
        if not pad_position_found:
            raise ValueError(f"Mark is '{spec.marker}', however no such pin was found.")
    case = case.cut(pinmark)

    parts = export_tools.AssemblyParts(
        [
            (case, "black body"),
            (merged_pins, "metal grey pins"),
            (pinmark, "light brown label"),
            (case_bot, "dark green body"),
        ]
    )

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.lib_name,
        model_name=spec.name,
        parts=parts,
    )
    return 1
