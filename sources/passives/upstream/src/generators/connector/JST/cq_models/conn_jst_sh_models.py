#  -*- coding: utf8 -*-
#!/usr/bin/python
#

"""
KiCad Libraries 3D generator module providing JST SH connectors
"""


import sys

import cadquery as cq


def generate_pins(params):
    if params["angled"]:
        return generate_angled_pins(params)
    return generate_straight_pins(params)


def generate_straight_pins(params):
    num_pins = params["num_pins"]
    pin_width = params["pin_width"]
    pin_pitch = params["pin_pitch"]
    pin_distance = (num_pins - 1) * pin_pitch

    mount_pin = (
        cq.Workplane("YZ")
        .workplane(-pin_width / 2)
        .move(0.3, 0.02)
        .vLine(0.6)
        .hLine(1.0)
        .vLine(0.65)
        .hLine(0.5)
        .vLine(-1.25)
        .close()
        .extrude(pin_width)
    )

    signal_pin = (
        cq.Workplane("YZ")
        .workplane(-pin_distance / 2 - pin_width / 2)
        .move(0.5, 1.32)
        .line(0.130, 1.75)
        .hLine(0.35)
        .vLine(-1.75)
        .close()
        .extrude(pin_width)
    )

    signal_pcb_pin = (
        cq.Workplane("YZ")
        .workplane(-pin_distance / 2 - pin_width / 2)
        .move(-1.8, 0)
        .vLine(0.2)
        .hLine(0.7)
        .vLine(-0.13)
        .hLine(0.1)
        .vLine(-0.07)
        .close()
        .extrude(pin_width)
    )

    pins = signal_pin.union(signal_pcb_pin)

    for i in range(num_pins):
        pins = pins.union(signal_pin.translate((i * pin_pitch, 0, 0)))
        pins = pins.union(signal_pcb_pin.translate((i * pin_pitch, 0, 0)))

    pins = pins.union(mount_pin.translate((-pin_distance / 2 - 1.1, 0, 0)))
    pins = pins.union(mount_pin.translate((pin_distance / 2 + 1.1, 0, 0)))
    return pins


def generate_angled_pins(params):
    num_pins = params["num_pins"]
    pin_width = params["pin_width"]
    pin_pitch = params["pin_pitch"]
    pin_distance = (num_pins - 1) * pin_pitch

    mount_pin = (
        cq.Workplane("YZ")
        .workplane(-pin_width / 2)
        .move(-2.475, 0.01)
        .vLine(1.25)
        .hLine(0.5)
        .vLine(-0.65)
        .hLine(1.0)
        .vLine(-0.6)
        .close()
        .extrude(pin_width)
    )

    signal_pin = (
        cq.Workplane("YZ")
        .workplane(-pin_distance / 2 - pin_width / 2)
        .move(-1.225, 1.79)
        .vLine(0.35)
        .hLine(1.75)
        .vLine(-0.48)
        .close()
        .extrude(pin_width)
    )

    signal_pcb_pin = (
        cq.Workplane("YZ")
        .workplane(-pin_distance / 2 - pin_width / 2)
        .move(1.675, 0)
        .vLine(0.06)
        .hLine(0.1)
        .vLine(0.14)
        .hLine(0.7)
        .vLine(-0.2)
        .close()
        .extrude(pin_width)
    )

    pins = signal_pin.union(signal_pcb_pin)

    for i in range(num_pins):
        pins = pins.union(signal_pin.translate((i * pin_pitch, 0, 0)))
        pins = pins.union(signal_pcb_pin.translate((i * pin_pitch, 0, 0)))

    pins = pins.union(mount_pin.translate((-pin_distance / 2 - 1.1, 0, 0)))
    pins = pins.union(mount_pin.translate((pin_distance / 2 + 1.1, 0, 0)))
    return pins


def generate_angled_body(params):
    body_off_center_y = 0.0
    body = generate_straight_body(params)
    body = body.rotate((0, 0, 0), (1, 0, 0), 90)
    body = body.translate((0, body_off_center_y + 1.775, 1.09))
    return body


def generate_body(params):
    body_off_center_z = params["body_off_center_z"]
    if params["angled"]:
        body = generate_angled_body(params)
    else:
        body = generate_straight_body(params)
    return body.translate((0, 0, body_off_center_z))


def generate_straight_body(params):
    body_width = params["body_width"]
    body_height = params["body_height"]
    body_length = params["body_length"]

    top_L_side_cut_depth = 0.5
    bottom_L_side_cut_depth = 0.5

    front_box_y_offset = 0.4
    front_box_width = body_length - (0.8 * 2)
    front_box_depth = 3.0
    front_notch_depth = 2.4

    body_off_center_y = params["body_off_center_y"]

    body = (
        cq.Workplane("XY")
        .workplane()
        .box(body_length, body_width, body_height, centered=(True, True, False))
    )
    R_top_side_L_cut = (
        cq.Workplane("YZ")
        .workplane(-body_length / 2)
        .move(-body_width / 2, body_height)
        .hLine(1.2)
        .vLine(-0.5)
        .hLine(-0.65)
        .vLine(-1.0)
        .hLine(-0.55)
        .close()
        .extrude(top_L_side_cut_depth)
    )
    L_top_side_L_cut = R_top_side_L_cut.translate(
        (body_length - top_L_side_cut_depth, 0, 0)
    )
    top_side_L_cut = R_top_side_L_cut.union(L_top_side_L_cut)

    R_bottom_side_L_cut = (
        cq.Workplane("YZ")
        .workplane(-body_length / 2)
        .move(body_width / 2, 0)
        .hLine(-1.5)
        .vLine(0.55)
        .hLine(1.0)
        .vLine(0.65)
        .line(0.5, 0.289)
        .close()
        .extrude(bottom_L_side_cut_depth)
    )
    L_bottom_side_L_cut = R_bottom_side_L_cut.translate(
        (body_length - bottom_L_side_cut_depth, 0, 0)
    )
    bottom_side_L_cut = R_bottom_side_L_cut.union(L_bottom_side_L_cut)

    top_box_cut = (
        cq.Workplane("XY")
        .workplane(body_height)
        .move(front_box_width / 2, -body_width / 2 + front_box_y_offset)
        .vLine(2.1)
        .hLine(-front_box_width)
        .vLine(-2.1)
        .close()
        .extrude(-front_box_depth)
    )

    top_notch_cut = (
        cq.Workplane("XY")
        .workplane(body_height)
        .move(front_box_width / 2 + 0.35, -body_width / 2 + front_box_y_offset + 1.0)
        .vLine(0.6)
        .hLine(-0.35 - front_box_width - 0.35)
        .vLine(-0.6)
        .close()
        .extrude(-front_notch_depth)
    )

    body = body.cut(top_side_L_cut)
    body = body.cut(bottom_side_L_cut)
    body = body.cut(top_box_cut)
    body = body.cut(top_notch_cut)
    body = body.translate((0, body_off_center_y, 0))
    return body
