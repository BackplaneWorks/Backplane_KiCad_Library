#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating QFP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
#
# Dimensions are from Jedec MS-026D document.
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

__title__ = "make GullWings ICs 3D models exported to STEP and VRML"
__author__ = "scripts: maurice and hyOzd; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

___ver___ = "2.0.0"

from collections.abc import Callable
from math import atan2, cos, degrees, radians, sin, tan
from typing import cast

import cadquery as cq
from cadquery.cq import CQObject
from cadquery.occ_impl.shapes import Edge

from generators.tools.model import export_tools

from .spec import GullwingSpec

MAX_CC1 = 1
DEFAULT_PIN_SLOPE = 10.0


def get_z_is_not_filter(z1: float, z2: float) -> Callable[[CQObject], bool]:
    """
    Returns a filter function that checks if an edge has the z-coordinate of its center
    that is different from one of the two values provided.
    """
    tol = 0.001

    def filter_func(edge: CQObject) -> bool:
        h = cast(Edge, edge).Center().z
        return abs(h - z1) > tol and abs(h - z2) > tol

    return filter_func


def crect(
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


def create_models(spec: GullwingSpec, generator_name: str) -> int:
    """Create the model corresponding to the spec.

    Args:
        spec: The gullwing specification.
        generator_name: The name of this generator.

    Returns:
        The number of models generated.
    """
    if not spec.has_3d_data:
        return 0

    # General parameters
    pitch = spec.pitch
    npx = spec.num_pins_x
    npy = spec.num_pins_y
    marker = spec.marker

    # Lead parameters
    l = spec.lead_len.nominal if spec.lead_len else None
    s = spec.lead_top_flat_part_length
    b = spec.lead_width.nominal
    c = spec.lead_height
    r1 = spec.lead_radius_top
    r2 = spec.lead_radius_bottom
    the_p = spec.lead_angle

    # Body parameters (except from height)
    e1 = spec.body_size_x.nominal
    d1 = spec.body_size_y.nominal
    e = spec.overall_size_x.nominal
    ef = spec.body_fillet
    tb_s = spec.body_size_top_delta
    cc1 = spec.corners_chamfer
    the = spec.body_angle

    # Body height parameters
    a1 = spec.body_pcb_gap
    a2 = spec.body_height

    # Excluded pins:
    excluded_pins = spec.deleted_pins + spec.hidden_pins

    if s is not None and l is not None and the_p is not None:
        print(
            "Warning: All of S, L, and the_p are provided. The system is "
            "overconstrained. Ignoring the value of S."
        )
        s = None

    # Approximate small angle approximation (for small the_p) for the height (along
    # z-axis) of the slewed part of the pin:
    pin_slew_height = a1 + ((a2 - c) / 2) - (r1 + r2 + c)
    # Total length of the pin (well, of its projection on the x/y-plane):
    pin_total_length = (e - e1) / 2
    if the_p is None:
        if s is not None and l is not None:
            the_p = degrees(
                atan2(pin_total_length - s - l - r1, pin_slew_height)
            )  # Approximate formula for small angles of the_p.
            if the_p < 0:
                print(
                    "The provided values of S and L will result in inward-"
                    "sloping pins. If this is not what you intended, confirm those "
                    "values and reduce one or more of them."
                )
        # If more than one param is missing, we can't calculate a pin angle, so just
        # set it to the default:
        else:
            if l is not None:
                min_the_p = degrees(atan2(pin_total_length - l - r1, pin_slew_height))
            elif s is not None:
                min_the_p = degrees(atan2(pin_total_length - s - r1, pin_slew_height))
            else:
                raise KeyError("Either S or L must be provided.")
            the_p = min(DEFAULT_PIN_SLOPE, min_the_p)
    # Some parts (like the SOT-23) are defined with such large tolerances that a
    # negative pin angle results. In those cases we limit the pin angle to zero and
    # shorten the lengths S and L:
    if the_p < 0.0:
        the_p = 0.0
        s = 0.0
        l = pin_total_length - r1
    if abs(the_p) >= 90.0:
        raise Exception("the_p must be between +/- 90 degrees")

    # Approximate small angle approximation (for small the_p) for the length (along
    # x/y-axis) of the slewed part of the pin:
    pin_slew_length = pin_slew_height * tan(radians(the_p))
    if l is None:
        if s is not None:
            l = pin_total_length - pin_slew_length - r1 - s
        else:
            # Make top and bottom flat part equally long:
            l = (pin_total_length - pin_slew_length - r1) / 2
        if the_p > 0 and l < (c + r2):
            raise Exception("the_p is too large.")
    if s is None:
        s = pin_total_length - pin_slew_length - r1 - l
        if the_p > 0 and s < 0:
            raise Exception("the_p is too large.")

    if the_p < 0 and pin_slew_length - r1 > s:
        # doesn't account for bottom chamfer, that would be more trouble than it's
        # worth to check, better safe than sorry
        raise Exception(
            "the_p is too negative, the resulting pin will intersect with the"
            "component body."
        )
    if l < 0:
        raise Exception("L cannot be negative")
    if s < 0:
        raise Exception("S cannot be negative")
    if r1 < 0:
        raise Exception("R1 cannot be negative")
    if l < (c + r2):
        raise Exception("L must be greater than c + R2")

    A = a1 + a2
    A2_t = (a2 - c) / 2  # body top part height
    A2_b = A2_t  # body bottom part height
    D1_b = d1 - 2 * tan(radians(the)) * A2_b  # bottom width
    E1_b = e1 - 2 * tan(radians(the)) * A2_b  # bottom length
    D1_t1 = d1 - tb_s  # top part bottom width
    E1_t1 = e1 - tb_s  # top part bottom length
    D1_t2 = D1_t1 - 2 * tan(radians(the)) * A2_t  # top part upper width
    E1_t2 = E1_t1 - 2 * tan(radians(the)) * A2_t  # top part upper length

    # calculate chamfers
    totpinwidthx = (npx - 1) * pitch + b  # total width of all pins on the X side
    totpinwidthy = (npy - 1) * pitch + b  # total width of all pins on the Y side

    if cc1 != 0:
        cc1 = abs(
            min(abs((d1 - totpinwidthx) / 2.0), abs((e1 - totpinwidthy) / 2.0), cc1)
            - 0.5 * tb_s
        )
        cc1 = max(cc1, (d1 - D1_t2) / 4.0 + 0.001)
        cc1 = min(cc1, MAX_CC1)

    cc = cc1

    if cc1 != 0:
        case = cq.Workplane("XY").workplane(centerOption="CenterOfMass", offset=a1)
        # Bottom edges:
        case = crect(case, E1_b, D1_b, cc1 - (d1 - D1_b) / 4.0, cc - (d1 - D1_b) / 4.0)
        case = case.workplane(centerOption="CenterOfMass", offset=A2_b)
        # Center (lower) outer edges:
        case = crect(case, e1, d1, cc1, cc)
        case = case.workplane(centerOption="CenterOfMass", offset=c)
        # Center (upper) outer edges:
        case = crect(case, e1, d1, cc1, cc)
        case = case.workplane(centerOption="CenterOfMass", offset=0)
        # Center (upper) inner edges:
        case = crect(
            case, E1_t1, D1_t1, cc1 - (d1 - D1_t1) / 4.0, cc - (d1 - D1_t1) / 4.0
        )
        case = case.workplane(centerOption="CenterOfMass", offset=A2_t)
        # Top edges:
        case = crect(
            case, E1_t2, D1_t2, cc1 - (d1 - D1_t2) / 4.0, cc - (d1 - D1_t2) / 4.0
        )
        case = case.loft(ruled=True)
    else:
        case = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=a1)
            .rect(E1_b, D1_b)
            .workplane(centerOption="CenterOfMass", offset=A2_b)
            .rect(e1, d1)
            .workplane(centerOption="CenterOfMass", offset=c)
            .rect(e1, d1)
            .rect(E1_t1, D1_t1)
            .workplane(centerOption="CenterOfMass", offset=A2_t)
            .rect(E1_t2, D1_t2)
            .loft(ruled=True)
        )

    if ef != 0:
        try:
            z_min = a1 + A2_b
            z_max = a1 + A2_b + c
            is_edge_to_fillet = get_z_is_not_filter(z_min, z_max)
            case = case.edges().filter(is_edge_to_fillet).fillet(ef)
        except KeyboardInterrupt:
            raise
        except Exception as exeption:
            print("Filleting failed.\n")
            print("{:s}\n".format(exeption))

    if spec.ep_size_x.nominal and spec.ep_size_y.nominal:
        ex = spec.ep_size_x.nominal
        ey = spec.ep_size_y.nominal
        ez = max(a1, 0.01)
        epad = cq.Workplane("XY").box(ex, ey, ez).translate((0, 0, ez / 2))
        case = case.cut(epad)
    else:
        epad = None

    marker_diameter = max(D1_b, E1_b) / 10.0
    if min(D1_b, E1_b) < 5 * marker_diameter:
        marker_edge_clearance = marker_diameter / 4.0
    else:
        marker_edge_clearance = marker_diameter / 2.0
    if marker == "bar":
        pinmark = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=A)
            .box(marker_diameter, D1_t2 - marker_edge_clearance, a2 / 4)
            .translate(
                (
                    -E1_t2 / 2 + marker_diameter / 2.0 + marker_edge_clearance / 2,
                    0.0,
                    -a2 / 8,
                )
            )
        )
        case = case.cut(pinmark)
    elif marker == "circle":
        pinmark = (
            cq.Workplane(
                "XZ",
                (
                    -E1_t2 / 2 + marker_edge_clearance + marker_diameter / 2.0,
                    D1_t2 / 2 - marker_edge_clearance - marker_diameter / 2.0,
                    A,
                ),
            )
            .rect(marker_diameter / 2, -a2 / 4, False)
            .revolve()
        )
        case = case.cut(pinmark)
    else:  # if marker == "none"
        pinmark = None

    # calculated dimensions for pin
    r1_o = r1 + c  # pin upper corner, outer radius
    r2_o = r2 + c  # pin lower corner, outer radius

    # Create a pin object at the center of top side.
    bpin = (
        cq.Workplane("YZ")
        .moveTo(-tb_s, a1 + A2_b)
        .line(s + tb_s, 0)
        .radiusArc(
            (
                s + (r1 * cos(radians(the_p))),
                a1 + A2_b - r1 + (r1 * sin(radians(the_p))),
            ),
            r1,
        )
        .lineTo(
            pin_total_length - l + r2_o - (r2_o * cos(radians(the_p))),
            r2 + c - (r2_o * sin(radians(the_p))),
        )
        .radiusArc((pin_total_length - l + r2_o, 0), -r2_o)
        .line(l - r2_o, 0)
        .line(0, c)
        .line(-l + r2_o, 0)
        .radiusArc(
            (
                pin_total_length - l + r2_o - (r2 * cos(radians(the_p))),
                r2 + c - (r2 * sin(radians(the_p))),
            ),
            r2,
        )
        .lineTo(
            s + (r1_o * cos(radians(the_p))),
            a1 + A2_b - r1 + (r1_o * sin(radians(the_p))),
        )
        .radiusArc((s, a1 + A2_b + c), -r1_o)
        .line(-s - tb_s, 0)
        .close()
        .extrude(b)
        .translate((-b / 2, 0, 0))
    )

    # Define all pin locations and rotations first
    h_coords = [((npx - 1) * pitch / 2) - i * pitch for i in range(npx)]
    v_coords = [((npy - 1) * pitch / 2) - i * pitch for i in range(npy)]

    # Filter out excluded pins
    all_locs = (
        [
            cq.Location(cq.Vector(-e1 / 2, y, 0), cq.Vector(0, 0, 1), 90)
            for y in v_coords
        ]  # Left
        + [
            cq.Location(cq.Vector(-x, -d1 / 2, 0), cq.Vector(0, 0, 1), 180)
            for x in h_coords
        ]  # Bottom
        + [
            cq.Location(cq.Vector(e1 / 2, -y, 0), cq.Vector(0, 0, 1), -90)
            for y in v_coords
        ]  # Right
        + [cq.Location(cq.Vector(x, d1 / 2, 0)) for x in h_coords]  # Top
    )

    valid_locs = [loc for i, loc in enumerate(all_locs, 1) if i not in excluded_pins]

    # Create all pins in a single, efficient operation
    pins = (
        cq.Workplane("XY")
        .pushPoints(valid_locs)
        .each(lambda loc: bpin.val().located(loc), combine="a")  # type: ignore
    )

    case = case.cut(pins)

    parts = export_tools.AssemblyParts(
        [
            (case, "black body"),
            (pins, "metal grey pins"),
            (epad, "metal grey pins"),
            (pinmark, "light brown label"),
        ]
    )

    export_tools.export(
        generator_name=generator_name,
        lib_name=spec.lib_name,
        model_name=spec.model_name,
        parts=parts,
    )
    return 1
