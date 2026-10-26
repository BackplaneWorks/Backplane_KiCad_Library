#! /usr/bin/env python3

# Generates generic rectangular SMD buzzers
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


def make_body(params):
    body = cq.Workplane("XY")
    body = body.rect(params["D"], params["E"])
    body = body.extrude(params["H"])

    top_sound_holes_params = params.get("top_sound_holes")
    if top_sound_holes_params:
        for hole_params in top_sound_holes_params:
            hole_x = hole_params[0]
            hole_y = hole_params[1]
            hole_diameter = hole_params[2]
            hole_depth = hole_params[3]

            hole = cq.Workplane("XY", origin=(hole_x, hole_y, params["H"]))
            hole = hole.circle(hole_diameter / 2)
            hole = hole.extrude(-hole_depth)
            body = body.cut(hole)

    return body


def make_pins(params):
    pins = None

    for pin_params in params["pin"]:
        p = pin_params.copy()
        x = p.pop(0)
        y = p.pop(0)
        w = p.pop(0)
        h = p.pop(0)
        pin = cq.Workplane("XY", origin=(x, y))
        pin = pin.rect(w, h)
        pin = pin.extrude(params["pin_thickness"])

        while p:
            pp = p.pop(0)
            if pp == "hole":
                hole_diameter = p.pop(0)
                hole = cq.Workplane("XY", origin=(x, y))
                hole = hole.circle(hole_diameter / 2)
                hole = hole.extrude(params["pin_thickness"])
                pin = pin.cut(hole)
            else:
                raise ValueError(f"Unknown pin paramter: {pp}")

        if pins:
            pins = pins.union(pin)
        else:
            pins = pin

    return pins
