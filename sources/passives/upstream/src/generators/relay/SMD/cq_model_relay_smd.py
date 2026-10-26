#! /usr/bin/env python3

# Generates Relay SMD models for KiCad libraries
#
# Copyright (C) 2024 Martin Sotirov <martin@libtec.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import cadquery as cq
from cadquery import Vector


def _make_pin(pin_index, params, width, thickness):
    corner_radius = params["pin_corner_radius"]
    pin_height = params["pin_height"]
    pin_length = params["pin_length"]

    if thickness > pin_height:
        raise ValueError(
            f"Pin {pin_index + 1}: Thickness can't be more than pin height."
        )

    if corner_radius < 0:
        raise ValueError(f"Pin {pin_index + 1}: Corner radius can't be less than 0.")

    if corner_radius > 0:
        if corner_radius > pin_height:
            raise ValueError(
                f"Pin {pin_index + 1}: Corner radius can't be bigger then pin height."
            )
        if corner_radius > pin_length + thickness / 2:
            raise ValueError(
                f"Pin {pin_index + 1}: Corner radius is too big in relation to pin length."
            )

    inner_corner_radius = corner_radius - thickness

    start_b = Vector(-thickness / 2, pin_height)
    ankle_b = Vector(start_b.x, corner_radius)
    heel_b = Vector(start_b.x + corner_radius, 0)
    tip_b = Vector(pin_length, 0)

    start_f = Vector(thickness / 2, pin_height)
    if inner_corner_radius > 0:
        ankle_f = Vector(start_f.x, ankle_b.y)
        heel_f = Vector(heel_b.x, thickness)
    else:
        ankle_f = Vector(start_f.x, thickness)
        heel_f = Vector(start_f.x, thickness)
    tip_f = Vector(tip_b.x, thickness)

    pin = cq.Workplane("XZ")

    pin = pin.moveTo(start_b.x, start_b.y)
    if ankle_b.y < start_b.y:
        pin = pin.lineTo(ankle_b.x, ankle_b.y)
    if corner_radius > 0:
        pin = pin.radiusArc((heel_b.x, heel_b.y), -corner_radius)
    if tip_b.x > heel_b.x:
        pin = pin.lineTo(tip_b.x, tip_b.y)

    if tip_f.x > start_f.x:
        pin = pin.lineTo(tip_f.x, tip_f.y)
    if heel_f.x < tip_f.x:
        pin = pin.lineTo(heel_f.x, heel_f.y)
    if inner_corner_radius > 0:
        pin = pin.radiusArc((ankle_f.x, ankle_f.y), inner_corner_radius)
    if inner_corner_radius <= 0 or start_f.y > ankle_f.y:
        pin = pin.lineTo(start_f.x, start_f.y)

    pin = pin.close()
    pin = pin.extrude(width / 2, both=True)

    return pin


def make_case(params, has_marker):
    body_h = params["H"] - params["pin_height"]

    fillet = params["W"] / 20
    if fillet > 0.25:
        fillet = 0.25

    body = (
        cq.Workplane("XY")
        .workplane(offset=params["pin_height"])
        .rect(params["L"], params["W"])
        .extrude(body_h)
        .edges("not(<Z)")
        .fillet(fillet)
    )

    if has_marker:
        marker = make_marker(params)
        body = body.cut(marker)

    return body


def make_marker(params):
    mx = params["marker_pos"][0]
    my = -params["marker_pos"][1]
    mw = params["marker_dim"][0]
    mh = params["marker_dim"][1]

    marker = (
        cq.Workplane("XY")
        .workplane(offset=params["H"] - 0.01)
        .center(mx, my)
        .rect(mw, mh)
        .extrude(0.01)
    )

    return marker


def make_pins(params):
    pin_union = None

    for pin_index in range(len(params["pin"])):
        pin = params["pin"][pin_index]

        x = pin[0]
        y = -pin[1]
        rotation = pin[2]
        width = pin[3]
        thickness = pin[4]

        p = _make_pin(pin_index, params, width, thickness)
        p = p.rotate((0, 0, 0), (0, 0, 1), rotation)
        p = p.translate((x, y, 0))

        if pin_union:
            pin_union = pin_union.union(p)
        else:
            pin_union = p

    return pin_union
