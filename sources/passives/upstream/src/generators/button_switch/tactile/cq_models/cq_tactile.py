#!/usr/bin/env python3

# CadQuery script for generating tactile button 3D models
#
# Copyright (c) 2015 Maurice https://launchpad.net/~easyw
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

from generators.tools.model.utils import (
    V2,
    Line,
    as_list,
    bodygen,
    features,
    make_asymmetric_chamfer,
    make_chamfer,
    make_fillet,
    make_rounded_corner_shape,
    make_z_chamfers,
    make_z_fillets,
    pingen,
    shellgen,
)


def _make_body_gnd_straight_pin_pocket(params, gnd_pin_index, gnd_pin_params):
    direction = gnd_pin_params[1]
    px = gnd_pin_params[2]
    py = gnd_pin_params[3]
    bottom_height = gnd_pin_params[4]
    width = gnd_pin_params[5]

    height = params["shell_height"] - bottom_height
    thickness = params["shell_thickness"]

    if direction == 0:
        px -= thickness
        if px < params["body_width"] / 2:
            thickness = params["body_width"] / 2 - px
    elif direction == 180:
        px += thickness
        if -px < params["body_width"] / 2:
            thickness = params["body_width"] / 2 + px
    elif direction == 90:
        py -= thickness
        if py < params["body_length"] / 2:
            thickness = params["body_length"] / 2 - py
    elif direction == 270:
        py += thickness
        if -py < params["body_length"] / 2:
            thickness = params["body_length"] / 2 + py
    else:
        raise ValueError(
            f"gnd_pin {gnd_pin_index + 1}: Direction can only in steps of 90 degrees"
        )

    body = cq.Workplane("YZ", origin=(0, 0, bottom_height + height / 2))
    body = body.rect(width, height)
    body = body.extrude(thickness)

    body = body.rotate((0, 0, 0), (0, 0, 1), direction)
    body = body.translate((px, py, 0))

    return body


def _make_body_gnd_pin_pockets(body, params):
    gnd_pins = params.get("gnd_pin", [])

    for gnd_pin_index, gnd_pin_params in enumerate(gnd_pins):
        pin_type = gnd_pin_params[0]

        if pin_type == "straight":
            gnd_pin_pocket = _make_body_gnd_straight_pin_pocket(
                params, gnd_pin_index, gnd_pin_params
            )
            body = body.cut(gnd_pin_pocket)
        elif pin_type == "gullwing":
            continue
        else:
            raise ValueError(
                f"gnd_pin {gnd_pin_index + 1}: Unknown pin type: {pin_type}"
            )

    return body


def make_body(params):
    body_board_distance = params.get("body_board_distance", 0)

    body = cq.Workplane("XY", origin=(0, 0, body_board_distance))
    body = body.rect(params["body_width"], params["body_length"])
    body = body.extrude(params["body_height"] - body_board_distance)

    body = make_z_chamfers(body, params.get("body_corner_chamfer"))
    body = make_z_fillets(body, params.get("body_corner_fillet"))
    body = bodygen.make_body_shell_top_clip_pocket(body, params)
    body = bodygen.make_body_shell_sides(body, params)
    body = _make_body_gnd_pin_pockets(body, params)
    body = bodygen.make_body_pin_pockets(body, params)
    body = features.make_features(
        body, params.get("body_features", []), "body_features"
    )
    # Pegs must be after features:
    body = bodygen.make_body_pegs(body, params)

    return body


def _make_shell_top(params):
    body = cq.Workplane(
        "XY", origin=(0, 0, params["shell_height"] - params["shell_thickness"])
    )
    body = body.rect(params["shell_width"], params["shell_length"])
    body = body.extrude(params["shell_thickness"])

    body = make_z_chamfers(body, params.get("shell_corner_chamfer"))
    body = make_z_fillets(body, params.get("shell_corner_fillet"))
    body = features.make_features(
        body, params.get("shell_top_features", []), "shell_top_features"
    )
    # Clips and lips go after features:
    body = shellgen.make_shell_top_clip(body, params)
    body = shellgen.make_shell_top_lips(body, params)

    return body


def _make_shell_top_cover_shape(workplane, params, d_param_name):
    h = as_list(params["shell_top_cover_height"])
    d = as_list(params[d_param_name])
    r = as_list(params.get("shell_top_cover_corner_radius", 0))

    if len(d) != len(h):
        raise ValueError(
            f"Parameters '{d_param_name}' and 'shell_top_cover_height' must have the same number of elements"
        )

    if len(r) > len(h):
        raise ValueError(
            f"Parameter 'shell_top_cover_corner_radius' can't have more elements than 'shell_top_cover_height'"
        )

    if len(h) == 1:
        h.insert(0, params["shell_height"])
        d.insert(0, d[0])

    p = list(map(lambda v: V2(v[0] / 2, v[1]), zip(d, h)))

    cover = make_rounded_corner_shape(workplane, p, r)

    return cover


def _make_shell_top_cover_round(body, params):
    if params.get("shell_top_cover_diameter") is None:
        raise ValueError(f"Parameter 'shell_top_cover_diameter' must be set")

    h = as_list(params["shell_top_cover_height"])

    if min(h) < params["shell_height"]:
        hole_d = max(as_list(params["shell_top_cover_diameter"]))
        hole_h = params["shell_thickness"]
        hole_z = params["shell_height"] - hole_h / 2
        hole = cq.Workplane("XY", origin=(0, 0, hole_z))
        hole = hole.cylinder(hole_h, hole_d / 2)
        body = body.cut(hole)

    cover = _make_shell_top_cover_shape(
        cq.Workplane("XZ"), params, "shell_top_cover_diameter"
    )
    cover = cover.revolve()
    body = body.union(cover)

    return body


def _make_shell_top_cover_rectangle(body, params):
    w = params.get("shell_top_cover_width")
    l = params.get("shell_top_cover_length")

    if w is None and l is None:
        raise ValueError(
            f"Parameters 'shell_top_cover_width' and/or 'shell_top_cover_length' must be provided"
        )

    if l is None:
        l = w
        w_shape = _make_shell_top_cover_shape(
            cq.Workplane("XZ"), params, "shell_top_cover_width"
        )
        l_shape = _make_shell_top_cover_shape(
            cq.Workplane("YZ"), params, "shell_top_cover_width"
        )
    elif w is None:
        w = l
        w_shape = _make_shell_top_cover_shape(
            cq.Workplane("XZ"), params, "shell_top_cover_length"
        )
        l_shape = _make_shell_top_cover_shape(
            cq.Workplane("YZ"), params, "shell_top_cover_length"
        )
    else:
        w_shape = _make_shell_top_cover_shape(
            cq.Workplane("XZ"), params, "shell_top_cover_width"
        )
        l_shape = _make_shell_top_cover_shape(
            cq.Workplane("YZ"), params, "shell_top_cover_length"
        )

    w_shape = w_shape.extrude(-max(l) / 2)
    l_shape = l_shape.extrude(max(w) / 2)
    cover = w_shape.intersect(l_shape)

    if params.get("shell_top_cover_diameter", 0):
        circle = _make_shell_top_cover_shape(
            cq.Workplane("XZ"), params, "shell_top_cover_diameter"
        )
        circle = circle.revolve()
        cover = cover.intersect(circle)

    cover = cover.union(cover.mirror("XZ"))
    cover = cover.union(cover.mirror("YZ"))
    cover = make_chamfer(
        cover,
        "(not (|X or |Y)) and (not (<Z or >Z))",
        params.get("shell_top_cover_vertical_corner_chamfer", 0),
    )
    cover = make_fillet(
        cover,
        "(not (|X or |Y)) and (not (<Z or >Z))",
        params.get("shell_top_cover_vertical_corner_fillet", 0),
    )

    cover = make_chamfer(cover, ">Z", params.get("shell_top_cover_top_chamfer"))
    cover = make_fillet(cover, ">Z", params.get("shell_top_cover_top_fillet"))

    body = body.union(cover)

    return body


def _make_shell_top_cover(body, params):
    cover_type = params.get("shell_top_cover_type")

    if cover_type == "round":
        body = _make_shell_top_cover_round(body, params)
    elif cover_type == "rectangle":
        body = _make_shell_top_cover_rectangle(body, params)
    elif cover_type:
        raise ValueError(f"Unknown shell_top_cover_type: {cover_type}")

    return body


def _get_shell_top_hole_bot_top(params):
    top = params["shell_height"]
    bot = params["shell_height"] - params["shell_thickness"]

    cover_height = params.get("shell_top_cover_height")
    if cover_height is not None:
        cover_height = max(as_list(cover_height))
        top = max(top, cover_height)

    return bot, top


def _make_shell_top_round_actuator_hole(body, params):
    bot, top = _get_shell_top_hole_bot_top(params)
    h = top - bot
    d = params["actuator_shell_hole_diameter"]

    hole = cq.Workplane("XY", origin=(0, 0, bot + h / 2))
    hole = hole.cylinder(h, d / 2)
    body = body.cut(hole)

    return body


def _make_shell_top_obround_actuator_hole(body, params):
    bot, top = _get_shell_top_hole_bot_top(params)
    h = top - bot
    w = params["actuator_shell_hole_width"]
    l = params["actuator_shell_hole_length"]

    if l < w:
        d = l
        rect_w = w - d
        rect_l = l
        cylinder_x = rect_w / 2
        cylinder_y = 0
    else:
        d = l
        rect_w = w
        rect_l = l - d
        cylinder_x = 0
        cylinder_y = rect_l / 2

    box = cq.Workplane("XY", origin=(0, 0, bot + h / 2))
    box = box.box(rect_w, rect_l, h)
    cylinder = cq.Workplane("XY", origin=(cylinder_x, cylinder_y, bot + h / 2))
    cylinder = cylinder.cylinder(h, d / 2)
    cylinders = cylinder.union(cylinder.translate((-rect_w, 0, 0)))
    hole = box.union(cylinders)

    body = body.cut(hole)

    return body


def _make_shell_top_rectangle_actuator_hole(body, params):
    bot, top = _get_shell_top_hole_bot_top(params)
    h = top - bot

    hole = cq.Workplane("XY", origin=(0, 0, bot + h / 2))

    if params.get("actuator_round_bottom_height") is not None:
        d = params["actuator_shell_hole_diameter"]
        hole = hole.cylinder(h, d / 2)
    else:
        w = params["actuator_shell_hole_width"]
        l = params.get("actuator_shell_hole_length", w)
        hole = hole.box(w, l, h)
        hole = make_chamfer(
            hole, "|Z", params.get("actuator_shell_hole_corner_chamfer")
        )
        hole = make_fillet(hole, "|Z", params.get("actuator_shell_hole_corner_fillet"))

    body = body.cut(hole)

    return body


def _make_shell_top_rectangle_round_actuator_hole(body, params):
    bot, top = _get_shell_top_hole_bot_top(params)
    h = top - bot
    w = params["actuator_shell_hole_width"]
    l = params["actuator_shell_hole_length"]
    d = params["actuator_shell_hole_diameter"]

    hole = cq.Workplane("XY", origin=(0, 0, bot + h / 2))
    hole_box = hole.box(w, l, h)
    hole_cylinder = hole.cylinder(h, d / 2)
    hole = hole_box.union(hole_cylinder)

    hole = make_chamfer(
        hole,
        "|Z and (<X or >X or <Y or >Y)",
        params.get("actuator_shell_hole_corner_chamfer"),
    )
    hole = make_fillet(
        hole,
        "|Z and (<X or >X or <Y or >Y)",
        params.get("actuator_shell_hole_corner_fillet"),
    )

    body = body.cut(hole)

    return body


def _make_shell_top_hex_actuator_hole(body, params):
    bot, top = _get_shell_top_hole_bot_top(params)
    h = top - bot
    w = params["actuator_shell_hole_width"]
    m = params["actuator_shell_hole_mid_length"]
    s = params["actuator_shell_hole_side_length"]

    hole = cq.Workplane("XY", origin=(0, 0, bot))
    hole = hole.move(0, m / 2)
    hole = hole.lineTo(w / 2, s / 2)
    hole = hole.lineTo(w / 2, -s / 2)
    hole = hole.lineTo(0, -m / 2)
    hole = hole.close()

    hole = hole.extrude(h)
    hole = hole.union(hole.mirror("YZ"))

    hole = make_chamfer(hole, "|Z", params.get("actuator_shell_hole_corner_chamfer"))
    hole = make_fillet(hole, "|Z", params.get("actuator_shell_hole_corner_fillet"))

    body = body.cut(hole)

    return body


def _make_shell_top_actuator_hole(body, params):
    actuator_type = params["actuator_type"]

    if actuator_type == "top-round":
        body = _make_shell_top_round_actuator_hole(body, params)
    elif actuator_type == "top-obround":
        body = _make_shell_top_obround_actuator_hole(body, params)
    elif actuator_type == "top-rectangle":
        body = _make_shell_top_rectangle_actuator_hole(body, params)
    elif actuator_type == "top-rectangle-round":
        body = _make_shell_top_rectangle_round_actuator_hole(body, params)
    elif actuator_type == "top-hex":
        body = _make_shell_top_hex_actuator_hole(body, params)
    elif actuator_type == "side-rectangle":
        body = body
    else:
        raise ValueError(f"Unknown actuator type: {actuator_type}")

    return body


def _make_shell_straight_pin(params, gnd_pin_index, gnd_pin_params):
    pt = params["shell_thickness"]

    gnd_pin_params = gnd_pin_params[1:]
    direction = gnd_pin_params.pop(0) % 360
    px = gnd_pin_params.pop(0)
    py = gnd_pin_params.pop(0)
    bot = gnd_pin_params.pop(0)
    w = gnd_pin_params.pop(0)

    top_height = params["shell_height"] - pt
    bridge_width = w

    tip_chamfer = None
    tip_fillet = None
    top_width = None
    mid_top_height = None
    mid_bot = None

    while gnd_pin_params:
        param_name = gnd_pin_params.pop(0)
        param_value = gnd_pin_params.pop(0)
        if param_name == "tip_chamfer":
            tip_chamfer = param_value
        elif param_name == "tip_fillet":
            tip_fillet = param_value
        elif param_name == "top_width":
            top_width = param_value
            bridge_width = top_width
        elif param_name == "mid_top_height":
            mid_top_height = param_value
        elif param_name == "mid_bottom_height":
            mid_bot = param_value
        else:
            raise ValueError(
                f"gnd_pin {gnd_pin_index}: Unknown extra parameter: {param_name}"
            )

    if top_width is not None and None in [mid_top_height, mid_bot]:
        raise ValueError(
            f"gnd_pin {gnd_pin_index}: The 'top_width' parameter also needs 'mid_top_height' and 'mid_bottom_height' parameters"
        )

    if direction == 0:
        bridge_shell_length = params["shell_width"]
        bridge_side_distance = px
        bridge_x = py
    elif direction == 180:
        bridge_shell_length = params["shell_width"]
        bridge_side_distance = -px
        bridge_x = -py
    elif direction == 90:
        bridge_shell_length = params["shell_length"]
        bridge_side_distance = py
        bridge_x = -px
    elif direction == 270:
        bridge_shell_length = params["shell_length"]
        bridge_side_distance = -py
        bridge_x = px
    else:
        raise ValueError(
            f"gnd_pin {gnd_pin_index + 1}: Direction can only in steps of 90 degrees"
        )

    body = cq.Workplane("YZ")
    body = body.moveTo(w / -2, bot)
    if top_width is not None:
        body = body.lineTo(w / -2, mid_bot)
        body = body.lineTo(top_width / -2, mid_top_height)
        body = body.lineTo(top_width / -2, top_height)
        body = body.lineTo(top_width / 2, top_height)
        body = body.lineTo(top_width / 2, mid_top_height)
        body = body.lineTo(w / 2, mid_bot)
    else:
        body = body.lineTo(w / -2, top_height)
        body = body.lineTo(w / 2, top_height)
    body = body.lineTo(w / 2, bot)
    body = body.close()

    body = body.extrude(-pt)

    if tip_chamfer:
        tip_chamfer_pos = (-pt / 2, 0, bot)
        body = make_asymmetric_chamfer(body, tip_chamfer, w, pt, tip_chamfer_pos, 90)

    body = make_fillet(body, "<Z and |X", tip_fillet)

    body = body.rotate((0, 0, 0), (0, 0, 1), direction)
    body = body.translate((px, py, 0))

    bridge = shellgen._make_shell_side_bridge(
        params, bridge_shell_length, bridge_side_distance, bridge_width, bridge_x
    )
    bridge = bridge.rotate((0, 0, 0), (0, 0, 1), direction)
    body = body.union(bridge)

    return body


def _make_shell_gullwing_pin(params, gnd_pin_index, gnd_pin_params):
    gnd_pin_params = gnd_pin_params[1:]
    direction = gnd_pin_params.pop(0) % 360
    tip_x = gnd_pin_params.pop(0)
    tip_y = gnd_pin_params.pop(0)
    pin_width = gnd_pin_params.pop(0)

    top_width = pin_width
    bottom_width = pin_width
    mid_top_height = params["shell_height"] * 0.50
    mid_bottom_height = params["shell_height"] * 0.25

    top_height = None
    top_length = None
    bottom_length = None

    while gnd_pin_params:
        param_name = gnd_pin_params.pop(0)
        param_value = gnd_pin_params.pop(0)
        if param_name == "top_height":
            top_height = param_value
        elif param_name == "top_width":
            top_width = param_value
        elif param_name == "top_length":
            top_length = param_value
        elif param_name == "mid_top_height":
            mid_top_height = param_value
        elif param_name == "mid_bottom_height":
            mid_bottom_height = param_value
        elif param_name == "bottom_length":
            bottom_length = param_value
        else:
            raise ValueError(
                f"gnd_pin {gnd_pin_index}: Unknown extra parameter: {param_name}"
            )

    if direction == 0:
        pin_length = tip_x - params["shell_width"] / 2
    elif direction == 180:
        pin_length = -params["shell_width"] / 2 - tip_x
    elif direction == 90:
        pin_length = tip_y - params["shell_length"] / 2
    elif direction == 270:
        pin_length = -params["shell_length"] / 2 - tip_y
    else:
        raise ValueError(
            f"gnd_pin {gnd_pin_index + 1}: Direction can only in steps of 90 degrees"
        )

    pt = params["shell_thickness"]

    if top_height is None:
        top_height = params["shell_height"]

    body = pingen.make_gullwing_pin(
        {
            "pin_width": top_width,
            "pin_thickness": pt,
            "pin_length": pin_length,
            "pin_top_height": top_height,
            "pin_top_length": top_length,
            "pin_bottom_length": bottom_length,
            "pin_corner_radius": pt,
        }
    )

    if bottom_width < top_width:
        cut = cq.Workplane("YZ")
        cut = cut.moveTo(bottom_width / 2, 0)
        cut = cut.lineTo(bottom_width / 2, mid_bottom_height)
        cut = cut.lineTo(top_width / 2, mid_top_height)
        cut = cut.lineTo(top_width / 2, 0)
        cut = cut.close()
        cut = cut.extrude(-pin_length)
        cut = cut.union(cut.mirror("XZ"))
        body = body.cut(cut)

    body = body.rotate((0, 0, 0), (0, 0, 1), direction)
    body = body.translate((tip_x, tip_y, 0))

    return body


def _make_gnd_pins(body, params):
    gnd_pins = params.get("gnd_pin", [])
    for gnd_pin_index, gnd_pin_params in enumerate(gnd_pins):
        pin_type = gnd_pin_params[0]

        if pin_type == "straight":
            pin = _make_shell_straight_pin(params, gnd_pin_index, gnd_pin_params)
        elif pin_type == "gullwing":
            pin = _make_shell_gullwing_pin(params, gnd_pin_index, gnd_pin_params)
        else:
            raise ValueError(
                f"gnd_pin {gnd_pin_index + 1}: Unknown pin type: {pin_type}"
            )

        body = body.union(pin)

    return body


def make_shell(params):
    body = _make_shell_top(params)
    body = _make_shell_top_cover(body, params)
    body = _make_shell_top_actuator_hole(body, params)
    body = shellgen.make_shell_sides(body, params)
    body = _make_gnd_pins(body, params)

    return body


def make_actuator_base(params):
    if params.get("actuator_base_height") is None:
        return

    h = params["actuator_base_height"] - params["body_height"]
    z = params["body_height"] + h / 2

    body = cq.Workplane("XY", origin=(0, 0, z))

    d = params.get("actuator_base_diameter")
    if d is not None:
        body = body.cylinder(h, d / 2)
    else:
        w = params["actuator_base_width"]
        l = params["actuator_base_length"]
        body = body.box(w, l, h)
        body = make_chamfer(body, "|Z", params.get("actuator_base_corner_chamfer"))
        body = make_fillet(body, "|Z", params.get("actuator_base_corner_fillet"))

    body = make_chamfer(body, ">Z", params.get("actuator_base_top_chamfer"))
    body = make_fillet(body, ">Z", params.get("actuator_base_top_fillet"))

    return body


def _make_top_round_actuator(params):
    h = as_list(params["actuator_height"])
    d = as_list(params["actuator_diameter"])
    r = as_list(params.get("actuator_corner_radius", 0))

    if len(d) != len(h):
        raise ValueError(
            f"Parameters 'actuator_diameter' and 'actuator_height' must have the same number of elements"
        )

    if len(r) > len(h):
        raise ValueError(
            f"Parameter 'actuator_corner_radius' can't have more elements than 'actuator_height'"
        )

    if len(h) == 1:
        shell_bot = params["shell_height"] - params["shell_thickness"]
        bot = min(params["body_height"], shell_bot)
        h.insert(0, bot)
        d.insert(0, d[0])

    p = list(map(lambda v: V2(v[0] / 2, v[1]), zip(d, h)))
    body = cq.Workplane("XZ")
    body = make_rounded_corner_shape(body, p, r)
    body = body.revolve()

    body = make_chamfer(body, ">Z", params.get("actuator_top_chamfer"))
    body = make_fillet(body, ">Z", params.get("actuator_top_fillet"))

    return body


def _make_top_obround_actuator(params):
    body_h = params["body_height"]
    shell_bottom_h = params["shell_height"] - params["shell_thickness"]
    if shell_bottom_h < body_h:
        body_h = shell_bottom_h

    w = params["actuator_width"]
    l = params["actuator_length"]
    r = l / 2

    body = cq.Workplane("XY", origin=(0, 0, body_h))
    body = body.moveTo(0, r)
    body = body.lineTo((w - l) / 2, r)
    body = body.radiusArc(((w - l) / 2, -r), r)
    body = body.lineTo(0, -r)
    body = body.close()

    body = body.extrude(params["actuator_height"] - body_h)
    body = body.union(body.mirror("YZ"))

    body = make_chamfer(body, ">Z", params.get("actuator_top_chamfer"))
    body = make_fillet(body, ">Z", params.get("actuator_top_fillet"))

    return body


def _make_top_rectangle_actuator(params):
    shell_bot = params["shell_height"] - params["shell_thickness"]
    bot = min(params["body_height"], shell_bot)

    h = as_list(params["actuator_height"]).copy()
    w = as_list(params["actuator_width"]).copy()
    l = as_list(params.get("actuator_length", w)).copy()

    if len(w) != len(h):
        raise ValueError(
            f"Parameters 'actuator_width' and 'actuator_height' must have the same number of elements"
        )

    if len(l) != len(h):
        raise ValueError(
            f"Parameters 'actuator_length' and 'actuator_height' must have the same number of elements"
        )

    if len(h) == 1:
        h.insert(0, bot)
        w.insert(0, w[0])
        l.insert(0, l[0])

    chamfers = as_list(params.get("actuator_chamfer", []))
    fillets = as_list(params.get("actuator_fillet", []))

    if params.get("actuator_round_bottom_height") is not None:
        base_h = params["actuator_round_bottom_height"] - bot
        base_d = params["actuator_round_bottom_diameter"]

        base = cq.Workplane("XY", origin=(0, 0, bot + base_h / 2))
        base = base.cylinder(base_h, base_d / 2)

        base = make_chamfer(base, ">Z", params.get("actuator_round_bottom_chamfer"))
        base = make_fillet(base, ">Z", params.get("actuator_round_bottom_fillet"))

        body = base
    else:
        body = None

    def _make_edges(func_name, part, edges_list, edges_index):
        jobs = {"b": 0, "m": 0, "t": 0}

        if i >= 1 and w[i - 1] < w[i] and l[i - 1] < l[i]:
            jobs["b"] = edges_list[edges_index] if edges_index < len(edges_list) else 0
            edges_index += 1

        if h[i] < h[i + 1]:
            jobs["m"] = edges_list[edges_index] if edges_index < len(edges_list) else 0
            edges_index += 1

        if (i + 2 == len(h)) or (
            i + 2 < len(h) and w[i + 1] > w[i + 2] and l[i + 1] > l[i + 2]
        ):
            jobs["t"] = edges_list[edges_index] if edges_index < len(edges_list) else 0
            edges_index += 1

        if jobs["m"] and jobs["m"] == jobs["b"] and jobs["m"] == jobs["t"]:
            part = getattr(part.edges(), func_name)(jobs["m"])
        elif jobs["m"] and jobs["m"] == jobs["b"]:
            part = getattr(part.edges("not >Z"), func_name)(jobs["m"])
        elif jobs["m"] and jobs["m"] == jobs["t"]:
            part = getattr(part.edges("not <Z"), func_name)(jobs["m"])
        else:
            if jobs["m"]:
                part = getattr(part.edges("(not <Z) and (not >Z)"), func_name)(
                    jobs["m"]
                )
            if jobs["b"]:
                part = getattr(part.edges("<Z"), func_name)(jobs["b"])
            if jobs["t"]:
                part = getattr(part.edges(">Z"), func_name)(jobs["t"])

        return part, edges_index

    edges_index = 0

    for i in range(0, len(h) - 1):
        if h[i] == h[i + 1]:
            continue

        part = cq.Workplane(origin=(0, 0, h[i]))
        part = part.rect(w[i], l[i])
        part = part.workplane(offset=h[i + 1] - h[i])
        part = part.rect(w[i + 1], l[i + 1])
        part = part.loft()
        part, _ = _make_edges("chamfer", part, chamfers, edges_index)
        part, edges_index = _make_edges("fillet", part, fillets, edges_index)

        body = body.union(part) if body else part

    if params.get("actuator_top_hole_diameter"):
        hole = cq.Workplane("XY", origin=(0, 0, h[-1]))
        hole = hole.circle(params["actuator_top_hole_diameter"] / 2)
        hole = hole.extrude(-params["actuator_top_hole_depth"])

        body = body.cut(hole)
        body = make_chamfer(
            body, "%CIRCLE and >Z", params.get("actuator_top_hole_chamfer")
        )
        body = make_fillet(
            body, "%CIRCLE and >Z", params.get("actuator_top_hole_fillet")
        )

    return body


def _make_top_rectangle_round_actuator(params):
    body_h = params["body_height"]
    shell_bottom_h = params["shell_height"] - params["shell_thickness"]
    if shell_bottom_h < body_h:
        body_h = shell_bottom_h

    w = params["actuator_width"]
    l = params["actuator_length"]
    r = params["actuator_diameter"] / 2

    rect = cq.Workplane("XY", origin=(0, 0, body_h))
    rect = rect.rect(w, l)
    rect = rect.extrude(params["actuator_height"] - body_h)

    rect = make_chamfer(rect, "|Z", params.get("actuator_corner_chamfer"))
    rect = make_fillet(rect, "|Z", params.get("actuator_corner_fillet"))

    circ = cq.Workplane("XY", origin=(0, 0, body_h))
    circ = circ.circle(r)
    circ = circ.extrude(params["actuator_height"] - body_h)

    body = rect.union(circ)

    body = make_chamfer(body, ">Z", params.get("actuator_top_chamfer"))
    body = make_fillet(body, ">Z", params.get("actuator_top_fillet"))

    return body


def _make_top_hex_actuator(params):
    body_h = params["body_height"]
    shell_bottom_h = params["shell_height"] - params["shell_thickness"]
    if shell_bottom_h < body_h:
        body_h = shell_bottom_h

    w = params["actuator_width"]
    m = params["actuator_mid_length"]
    s = params["actuator_side_length"]

    body = cq.Workplane("XY", origin=(0, 0, body_h))
    body = body.move(0, m / 2)
    body = body.lineTo(w / 2, s / 2)
    body = body.lineTo(w / 2, -s / 2)
    body = body.lineTo(0, -m / 2)
    body = body.close()

    body = body.extrude(params["actuator_height"] - body_h)
    body = body.union(body.mirror("YZ"))

    body = make_chamfer(body, "|Z", params.get("actuator_corner_chamfer"))
    body = make_fillet(body, "|Z", params.get("actuator_corner_fillet"))

    body = make_chamfer(body, ">Z", params.get("actuator_top_chamfer"))
    body = make_fillet(body, ">Z", params.get("actuator_top_fillet"))

    return body


def _make_side_rectangle_actuator(params):
    btn_dir = params["actuator_direction"] % 360

    head_t = params["actuator_thickness"]
    head_w = params["actuator_width"]
    head_top_h = params["actuator_top_height"]
    head_bot_h = params["actuator_bottom_height"]
    head_h = head_top_h - head_bot_h
    head_dist = params["actuator_distance"]
    head_start_dist = head_dist - head_t

    neck_w = params["actuator_neck_width"]
    neck_top_h = params["actuator_neck_top_height"]
    neck_bot_h = params["actuator_neck_bottom_height"]
    neck_h = neck_top_h - neck_bot_h
    neck_gaps = params.get("actuator_neck_gaps", [])

    if btn_dir in [0, 180]:
        neck_start_dist = params["body_width"] / 2
    elif btn_dir in [90, 270]:
        neck_start_dist = params["body_length"] / 2
    else:
        raise ValueError(f"Side actuator direction can only in steps of 90 degrees")
    neck_l = head_start_dist - neck_start_dist

    corner_chamfer = params.get("actuator_corner_chamfer")

    head = cq.Workplane("XY", origin=(head_start_dist, 0, head_bot_h))
    head = head.moveTo(0, 0)
    head = head.lineTo(0, head_w / 2)
    if corner_chamfer:
        head = head.lineTo(head_t - corner_chamfer[1], head_w / 2)
        head = head.lineTo(head_t, head_w / 2 - corner_chamfer[0])
    else:
        head = head.lineTo(head_t, head_w / 2)
    head = head.lineTo(head_t, 0)
    head = head.close()
    head = head.extrude(head_h)
    head = head.union(head.mirror("XZ"))

    head = make_fillet(head, ">X and |Z", params.get("actuator_corner_fillet"))
    head = make_chamfer(head, "<Z and >X", params.get("actuator_bottom_chamfer"))
    head = make_fillet(head, "<Z and >X", params.get("actuator_bottom_fillet"))

    neck = cq.Workplane("YZ", origin=(neck_start_dist, 0, neck_bot_h + neck_h / 2))
    neck = neck.rect(neck_w, neck_h)
    neck = neck.extrude(neck_l)

    for [neck_gap_x, neck_gap_w] in neck_gaps:
        neck_gap = cq.Workplane(
            "YZ", origin=(neck_start_dist, neck_gap_x, neck_bot_h + neck_h / 2)
        )
        neck_gap = neck_gap.rect(neck_gap_w, neck_h)
        neck_gap = neck_gap.extrude(neck_l)
        neck = neck.cut(neck_gap)

    body = head.union(neck)
    body = body.rotate((0, 0, 0), (0, 0, 1), btn_dir)

    return body


def make_actuator(params):
    actuator_type = params["actuator_type"]
    if actuator_type == "top-round":
        body = _make_top_round_actuator(params)
    elif actuator_type == "top-obround":
        body = _make_top_obround_actuator(params)
    elif actuator_type == "top-rectangle":
        body = _make_top_rectangle_actuator(params)
    elif actuator_type == "top-rectangle-round":
        body = _make_top_rectangle_round_actuator(params)
    elif actuator_type == "top-hex":
        body = _make_top_hex_actuator(params)
    elif actuator_type == "side-rectangle":
        body = _make_side_rectangle_actuator(params)
    else:
        raise ValueError(f"Unknown actuator type: {actuator_type}")

    body = features.make_features(
        body, params.get("actuator_features", []), "actuator_features"
    )

    return body


def make_pins(params):
    body = pingen.make_pins(params)
    return body
