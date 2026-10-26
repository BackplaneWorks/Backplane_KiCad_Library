#! /usr/bin/env python3

# CadQuery helper functions for generating plastic bodies
#
# Copyright (c) 2017 Terje Io https://github.com/terjeio
# Copyright (c) 2017 Maurice https://launchpad.net/~easyw
# Copyright (c) 2020 Mountyrox https://github.com/mountyrox
# Copyright (c) 2024-2025 Martin Sotirov <martin@libtec.org>
#
# All trademarks within this guide belong to their legitimate owners.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License (LGPL)
# as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
# For detail see the LICENCE text file.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import math

import cadquery as cq

from generators.tools.model.utils import as_list


def make_body_shell_top_clip_pocket(body, params):
    if "shell_top_clip_direction" not in params:
        return body

    d = params["shell_top_clip_pocket_depth"]
    w = params["shell_top_clip_pocket_width"]
    l = params["shell_top_clip_pocket_length"]

    x = params["shell_top_clip_x"]
    y = params["shell_top_clip_y"]
    z = params["shell_height"] - d

    pocket = cq.Workplane("XY", origin=(x, y, z))
    pocket = pocket.rect(w, l)
    pocket = pocket.extrude(d)

    body = body.cut(pocket)

    return body


def make_body_pin_pockets(body, params):
    if params["pin_type"] in "top-jbend":
        pl = params["pin_bottom_length"]
    elif params["pin_type"] == "bottom-jbend":
        pl = params["pin_length"]
    elif params["pin_type"] == "flat":
        pl = params["pin_length"]
    elif params["pin_type"] in ["gullwing", "through-hole"]:
        return body
    else:
        raise ValueError(f"Unknown pin_type: {params['pin_type']}")

    pw = params["pin_width"]
    ph = params["pin_thickness"] + params.get("pin_board_distance", 0)

    for pin in params["pins"]:
        px, py, ori = pin[0:3]

        pocket_body = cq.Workplane("XY", origin=(-pl / 2, 0, 0))
        pocket_body = pocket_body.rect(pl, pw)
        pocket_body = pocket_body.extrude(ph)
        pocket_body = pocket_body.rotate((0, 0, 0), (0, 0, 1), ori)
        pocket_body = pocket_body.translate((px, py, 0))

        body = body.cut(pocket_body)

    return body


def make_body_pegs(body, params):
    pegs = params.get("pegs", [])
    body_board_distance = params.get("body_board_distance", 0)

    for peg_index, peg_params in enumerate(pegs):
        x = peg_params.pop(0)
        y = peg_params.pop(0)
        z = body_board_distance
        r = peg_params.pop(0) / 2
        h = peg_params.pop(0) - body_board_distance

        chamfer = None

        while peg_params:
            peg_param_name = peg_params.pop(0)
            peg_param_value = peg_params.pop(0)
            if peg_param_name == "z":
                z += peg_param_value
            elif peg_param_name == "chamfer":
                chamfer = peg_param_value
            else:
                raise ValueError(
                    f"pegs[{peg_index}]: Unknown extra parameter: {peg_param_name}"
                )

        peg = cq.Workplane("XZ", origin=(x, y, z))
        peg = peg.moveTo(0, h)
        peg = peg.lineTo(0, 0)
        peg = peg.lineTo(r, 0)
        if chamfer:
            peg = peg.lineTo(r, h + chamfer[1])
            peg = peg.lineTo(r - chamfer[0], h)
        else:
            peg = peg.lineTo(r, h)
        peg = peg.close()
        peg = peg.revolve()

        body = body.union(peg)

    return body


def _make_body_shell_side_holder(dim, chamfer, fillet):
    w = dim[2]
    h = dim[1]
    l = dim[0]

    chamfer_w = 0
    chamfer_h = 0
    if chamfer:
        chamfer_w = chamfer[0]
        chamfer_h = chamfer[1]
        if chamfer_w - w > 0.000001:
            raise ValueError(f"Side holder chamfer[0] can't be more than {w:.5}")
        if chamfer_h - h > 0.000001:
            raise ValueError(f"Side holder chamfer[1] can't be more than {h:.5}")

    if fillet is not None:
        if fillet - w > 0.000001:
            raise ValueError(f"Side holder fillet can't be more than {w:.5}")
        if fillet - h > 0.000001:
            raise ValueError(f"Side holder fillet can't be more than {h:.5}")

    body = cq.Workplane("XZ", origin=(0, l / 2, -h / 2))
    body = body.moveTo(0, 0)
    body = body.lineTo(w, 0)

    if chamfer:
        if abs(chamfer_h - h) > 0.000001:
            body = body.lineTo(w, h - chamfer_h)
        if abs(chamfer_w - w) > 0.000001:
            body = body.lineTo(w - chamfer_w, h)
        body = body.lineTo(0, h)
    elif fillet:
        if fillet < h:
            body = body.lineTo(w, h - fillet)
        body = body.radiusArc((w - fillet, h), -fillet)
        if fillet < w:
            body = body.lineTo(0, h)
    else:
        body = body.lineTo(w, h)
        body = body.lineTo(0, h)

    body = body.close()
    body = body.extrude(l)

    return body


def _make_body_shell_side_pocket(params, side_params, body_dim):
    st = params["shell_thickness"]

    w = side_params["width"]
    h = params["shell_height"] - side_params["bottom_height"]

    x = side_params["distance"] - st
    y = 0
    z = params["shell_height"] - h / 2

    if x < body_dim[0] / 2:
        depth = body_dim[0] / 2 - x
        body = cq.Workplane("YZ", origin=(x, y, z))
        body = body.rect(w, h)
        body = body.extrude(depth)
    else:
        body = None

    return body


def _make_body_shell_side(params, side_params, body_dim):
    body = None
    action = None

    side_w = side_params.get("side_width")
    hole_w = side_params.get("hole_width")
    hole_bot = side_params.get("hole_bottom_height")

    holder_chamfer = side_params.get("holder_chamfer")
    holder_fillet = side_params.get("holder_fillet")

    if hole_w is not None and hole_bot is not None:
        hole_top = side_params.get("hole_top_height", params["body_height"])
        hole_bot_gap_w = side_params.get("hole_bottom_gap_width", 0)

        w = (hole_w - hole_bot_gap_w) / 2
        h = hole_top - hole_bot
        d = side_params["distance"] - body_dim[0] / 2

        x = body_dim[0] / 2
        y = hole_w / 2 - w / 2
        z = params["body_height"] - h / 2

        body = _make_body_shell_side_holder([w, h, d], holder_chamfer, holder_fillet)
        body = body.translate((x, y, z))
        body = body.union(body.mirror("XZ"))
        action = "union"

    if side_w is not None:
        side_top = side_params["side_top_height"]

        w = (body_dim[1] - side_params["width"]) / 2
        h = params["body_height"] - side_top
        d = side_params["distance"] - body_dim[0] / 2

        x = body_dim[0] / 2
        y = body_dim[1] / 2 - w / 2
        z = params["body_height"] - h / 2

        side_body = _make_body_shell_side_holder(
            [w, h, d], holder_chamfer, holder_fillet
        )
        side_body = side_body.translate((x, y, z))
        side_body = side_body.union(side_body.mirror("XZ"))

        body = body.union(side_body) if body else side_body
        action = "union"

    if hole_bot is None and side_w is None:
        body = _make_body_shell_side_pocket(params, side_params, body_dim)
        action = "cut"

    return body, action


def make_body_shell_sides(body, params):
    shell_sides = params.get("shell_sides", [])

    for side_index, side_params in enumerate(shell_sides):
        side_directions = as_list(side_params["direction"])

        for side_direction in side_directions:
            if side_direction in [0, 180]:
                body_dim = (params["body_width"], params["body_length"])
            elif side_direction in [90, 270]:
                body_dim = (params["body_length"], params["body_width"])
            else:
                raise ValueError(
                    f"shell_sides[{side_index}]: Invalid direction: {side_directions}"
                )

            side_params = side_params.copy()
            side_params["direction"] = side_direction
            side_body, action = _make_body_shell_side(params, side_params, body_dim)

            if not side_body:
                continue

            side_body = side_body.rotate((0, 0, 0), (0, 0, 1), side_direction)

            if action == "union":
                body = body.union(side_body)
            elif action == "cut":
                body = body.cut(side_body)

    return body
