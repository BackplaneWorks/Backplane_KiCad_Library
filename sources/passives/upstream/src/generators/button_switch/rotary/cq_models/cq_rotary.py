#!/usr/bin/env python3

# CadQuery script for generating rotary switch 3D models
#
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


import cadquery as cq

from generators.tools.model import fonts
from generators.tools.model.utils import bodygen, features, make_chamfer, make_fillet, pingen, shellgen


def _make_body_dial_pocket(body, params):
    dial_pocket = cq.Workplane("XY", origin=(0, 0, params["dial_bottom_height"]))
    dial_pocket = dial_pocket.circle(params["dial_diameter"] / 2)
    dial_pocket = dial_pocket.extrude(
        params["dial_height"] - params["dial_bottom_height"]
    )

    body = body.cut(dial_pocket)

    return body


def make_body(params):
    body_board_distance = params.get("body_board_distance", 0)

    body = cq.Workplane("XY", origin=(0, 0, body_board_distance))
    body = body.rect(params["body_width"], params["body_length"])
    body = body.extrude(params["body_height"] - body_board_distance)

    body = make_chamfer(body, "|Z", params.get("body_corner_chamfer"))
    body = make_fillet(body, "|Z", params.get("body_corner_fillet"))
    body = _make_body_dial_pocket(body, params)
    body = bodygen.make_body_shell_sides(body, params)
    body = features.make_features(
        body, params.get("body_features", []), "body_features"
    )

    return body


def make_dial(params):
    arrow_w = params["dial_arrow_width"]
    arrow_l = params["dial_arrow_length"]
    shaft_w = params["dial_arrow_shaft_width"]
    shaft_l = params["dial_arrow_shaft_length"]
    head_w = arrow_w
    head_l = arrow_l - shaft_l

    body = cq.Workplane("XY", origin=(0, 0, params["dial_bottom_height"]))
    body = body.circle(params["dial_diameter"] / 2)
    body = body.extrude(params["dial_height"] - params["dial_bottom_height"])

    arrow = cq.Workplane("XY", origin=(0, 0, params["dial_height"]))
    arrow = arrow.moveTo(0, 0)
    arrow = arrow.lineTo(head_w / 2, head_l)
    arrow = arrow.lineTo(shaft_w / 2, head_l)
    arrow = arrow.lineTo(shaft_w / 2, arrow_l)
    arrow = arrow.lineTo(0, arrow_l)
    arrow = arrow.close()
    arrow = arrow.extrude(-params["dial_arrow_depth"])

    arrow = arrow.union(arrow.mirror("YZ"))
    arrow = arrow.translate((0, -arrow_l / 2, 0))
    arrow = arrow.rotate((0, 0, 0), (0, 0, 1), 180)

    body = body.cut(arrow)

    return body


def _make_shell_top(params):
    z = params["shell_height"] - params["shell_thickness"]

    body = cq.Workplane("XY", origin=(0, 0, z))
    body = body.rect(params["shell_width"], params["shell_length"])
    body = body.circle(params["dial_diameter"] / 2)
    body = body.extrude(params["shell_thickness"])

    body = make_chamfer(body, "|Z", params.get("shell_corner_chamfer"))
    body = make_fillet(body, "|Z", params.get("shell_corner_fillet"))
    body = shellgen.make_shell_top_lips(body, params)

    return body


def make_shell(params):
    body = _make_shell_top(params)
    body = shellgen.make_shell_sides(body, params)

    labels = make_labels(params)
    body = body.cut(labels)

    return body


def make_labels(params):
    depth = params["shell_thickness"] / 2
    z = params["shell_height"] - depth

    r = params["dial_labels_radius"]
    size = params["dial_labels_size"]
    text = params["dial_labels"]
    font_name = "Roboto"
    font_path = fonts.RobotoRegular

    body = None
    for char_index, char in enumerate(text):
        angle = 360 / len(text) * char_index

        char_body = cq.Workplane("XY", origin=(0, r, z))
        char_body = char_body.text(
            char, size, depth, font=font_name, fontPath=font_path
        )
        char_body = char_body.rotate((0, 0, 0), (0, 0, 1), angle)

        if body:
            body = body.union(char_body)
        else:
            body = char_body

    return body


def make_pins(params):
    body = pingen.make_pins(params)

    return body
