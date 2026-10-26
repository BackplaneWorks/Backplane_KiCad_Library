#!/usr/bin/env python3

# CadQuery helper functions for generating shells
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

from generators.tools.model.utils import as_list, pingen


def make_shell_top_lips(body, params):
    lips = params.get("shell_top_lips", [])

    for lip_index, lip_params in enumerate(lips):
        lip_params = lip_params.copy()
        operation = lip_params.pop(0)
        directions = as_list(lip_params.pop(0))
        offset = lip_params.pop(0)
        length = lip_params.pop(0)
        base_width = lip_params.pop(0)
        tip_width = lip_params.pop(0)

        if lip_params:
            raise ValueError(f"shell_top_lips[{lip_index}]: Too many parameters")

        for direction in directions:
            if direction in [0, 180]:
                distance = params["shell_width"] / 2
            elif direction in [90, 270]:
                distance = params["shell_length"] / 2
            else:
                raise ValueError(
                    f"shell_top_lips[{lip_index}]: Invalid direction: {direction}"
                )

            x = distance
            y = -offset
            z = params["shell_height"] - params["shell_thickness"]
            lip = cq.Workplane("XY", origin=(x, y, z))
            lip = lip.moveTo(0, base_width / 2)
            lip = lip.lineTo(length, tip_width / 2)
            lip = lip.lineTo(length, -tip_width / 2)
            lip = lip.lineTo(0, -base_width / 2)
            lip = lip.close()
            lip = lip.extrude(params["shell_thickness"])

            if direction in [90, 270]:
                lip = lip.rotate((0, 0, 0), (0, 0, 1), 90)

            if direction == 180:
                lip = lip.mirror("YZ")
            if direction == 270:
                lip = lip.mirror("XZ")

            if operation == "add":
                body = body.union(lip)
            elif operation == "cut":
                body = body.cut(lip)
            else:
                raise ValueError(
                    f"shell_top_lips[{lip_index}]: Invalid operation: {operation}"
                )

    return body


def make_shell_top_clip(body, params):
    if "shell_top_clip_direction" not in params:
        return body

    w = params["shell_top_clip_width"]
    l = params["shell_top_clip_length"]
    d = params["shell_top_clip_depth"]

    x = params["shell_top_clip_x"]
    y = params["shell_top_clip_y"]
    z = params["shell_height"]

    st = params["shell_thickness"]

    pocket_w = params["shell_top_clip_pocket_width"]
    pocket_l = params["shell_top_clip_pocket_length"]

    pocket = cq.Workplane("XY", origin=(x, y))
    pocket = pocket.rect(pocket_w, pocket_l)
    pocket = pocket.extrude(z)
    body = body.cut(pocket)

    direction = params["shell_top_clip_direction"]
    corner_r = params["shell_top_clip_corner_radius"]

    clip = pingen.make_gullwing_pin(
        {
            "pin_width": w,
            "pin_thickness": st,
            "pin_length": l,
            "pin_top_height": d,
            "pin_top_length": l * 0.4,
            "pin_bottom_length": l * 0.4,
            "pin_corner_radius": corner_r,
        }
    )

    clip = clip.rotate((0, 0, 0), (0, 0, 1), direction)

    if direction == 0:
        x -= pocket_w / 2 - l
    elif direction == 180:
        x += pocket_w / 2 - l
    elif direction == 90:
        y -= pocket_l / 2 - l
    elif direction == 270:
        y += pocket_l / 2 - l
    else:
        raise ValueError(f"shell_top_clip_direction can only be in steps of 90 degrees")

    clip = clip.translate((x, y, z - d))
    body = body.union(clip)

    return body


def _make_shell_side_bridge(params, shell_length, side_distance, w, offs):
    st = params["shell_thickness"]
    h = params["shell_height"]

    body = cq.Workplane("XZ", origin=(0, offs, 0))
    body = body.moveTo(shell_length / 2, h - st)
    body = body.lineTo(shell_length / 2, h)
    if side_distance - st > shell_length / 2:
        body = body.lineTo(side_distance - st, h)
    body = body.radiusArc((side_distance, h - st), st)
    body = body.close()
    body = body.extrude(w / 2, both=True)

    return body


def _make_shell_side_extrusions(body, params, side_params):
    side_extrusions = side_params.get("extrusions")
    if not side_extrusions:
        return body

    top = side_params["bottom_height"]
    st = params["shell_thickness"]
    x = side_params["distance"] - st

    for side_extrusion in side_extrusions:
        offs, w, l = side_extrusion
        z = top - l / 2

        e_body = cq.Workplane("YZ", origin=(x, offs, z))
        e_body = e_body.rect(w, l)
        e_body = e_body.extrude(st)

        body = body.union(e_body)

    return body


def _make_shell_side(params, side_params, shell_length):
    st = params["shell_thickness"]
    sh = params["shell_height"]

    corner_chamfer = side_params.get("corner_chamfer")
    corner_fillet = side_params.get("corner_fillet")

    x = side_params["distance"] - st
    w = side_params["width"]
    top = sh - st
    bot = side_params["bottom_height"]
    hole_w = side_params.get("hole_width")
    hole_top = side_params.get("hole_top_height")
    side_w = side_params.get("side_width")

    body = cq.Workplane("YZ", origin=(x, 0, 0))
    body = body.moveTo(w / 2, top)

    if side_w is not None:
        side_top = side_params["side_top_height"]
        body = body.lineTo(w / 2, side_top)
        body = body.lineTo(side_w / 2, side_top)
        if corner_chamfer:
            body = body.lineTo(side_w / 2, bot + corner_chamfer[1])
            body = body.lineTo(side_w / 2 - corner_chamfer[0], bot)
        else:
            body = body.lineTo(side_w / 2, bot)
    else:
        if corner_chamfer:
            body = body.lineTo(w / 2, bot + corner_chamfer[1])
            body = body.lineTo(w / 2 - corner_chamfer[0], bot)
        else:
            body = body.lineTo(w / 2, bot)

    if hole_w is not None:
        hole_bot = side_params.get("hole_bottom_height")

        if hole_bot is not None:
            hole_bot_gap_w = side_params.get("hole_bottom_gap_width", 0)
            body = body.lineTo(hole_bot_gap_w / 2, bot)
            body = body.lineTo(hole_bot_gap_w / 2, hole_bot)
            body = body.lineTo(hole_w / 2, hole_bot)
        else:
            body = body.lineTo(hole_w / 2, bot)

        if hole_top is not None:
            body = body.lineTo(hole_w / 2, hole_top)
            body = body.lineTo(0, hole_top)
            body = body.lineTo(0, top)
        else:
            body = body.lineTo(hole_w / 2, top)
    else:
        body = body.lineTo(0, bot)
        body = body.lineTo(0, top)

    body = body.close()
    body = body.extrude(params["shell_thickness"])

    if corner_fillet:
        body = body.edges("|X and <Z and >Y").fillet(corner_fillet)

    if hole_w is not None and hole_top is None:
        bridge_w = w / 2 - hole_w / 2
        bridge_x = hole_w / 2 + bridge_w / 2
    else:
        bridge_w = w / 2
        bridge_x = bridge_w / 2

    bridge = _make_shell_side_bridge(
        params, shell_length, side_params["distance"], bridge_w, bridge_x
    )
    body = body.union(bridge)
    body = body.union(body.mirror("XZ"))

    body = _make_shell_side_extrusions(body, params, side_params)

    return body


def make_shell_sides(body, params):
    shell_sides = params.get("shell_sides", [])

    for side_index, side_params in enumerate(shell_sides):
        side_directions = as_list(side_params["direction"])

        for side_direction in side_directions:
            if side_direction in [0, 180]:
                shell_length = params["shell_width"]
            elif side_direction in [90, 270]:
                shell_length = params["shell_length"]
            else:
                raise ValueError(
                    f"shell_sides[{side_index}]: Invalid direction: {side_directions}"
                )

            side_params = side_params.copy()
            side_params["direction"] = side_direction
            side_body = _make_shell_side(params, side_params, shell_length)
            side_body = side_body.rotate((0, 0, 0), (0, 0, 1), side_direction)

            body = body.union(side_body)

    return body
