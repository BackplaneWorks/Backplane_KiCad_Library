# -*- coding: utf8 -*-
#!/usr/bin/python
# This is derived from a cadquery script to generate all pin header models in X3D format.
# It takes a bit long to run! It can be run from cadquery freecad
# module as well.
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd

## requirements
## cadquery FreeCAD plugin
##   https://github.com/jmwright/cadquery-freecad-module

## to run the script just do: freecad make_gwexport_fc.py modelName
## e.g. c:\freecad\bin\freecad make_gw_export_fc.py SOIC_8

## the script will generate STEP and VRML parametric models
## to be used with kicad StepUp script

# * These are a FreeCAD & cadquery tools                                     *
# * to export generated models in STEP & VRML format.                        *
# *                                                                          *
# * cadquery script for generating QFP/SOIC/SSOP/TSSOP models in STEP AP214  *
# *   Copyright (c) 2015                                                     *
# * Maurice https://launchpad.net/~easyw                                     *
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

__title__ = "make Pin header 3D models"
__author__ = "maurice and Shack"
__Comment__ = (
    "make pin header 3D models exported to STEP and VRML for Kicad StepUP script"
)

___ver___ = "2.0.0 21/11/2017"

import cadquery as cq

from generators.tools.model.cq_helpers import union_all


def make_Vertical_THT_base(n, pitch, rows, base_width, base_height, base_chamfer):
    if base_chamfer == 0:
        base = (
            cq.Workplane("XY")
            .moveTo(-(base_width - (rows - 1) * pitch) / 2.0, pitch / 2.0)
            .vLine(n * -pitch)
            .hLine(base_width)
            .vLine(n * pitch)
        )
    else:
        base = cq.Workplane("XY").moveTo(
            -(base_width - (rows - 1) * pitch) / 2.0 + base_chamfer, pitch / 2.0
        )
        for x in range(0, n):
            base = (
                base.line(-base_chamfer, -base_chamfer)
                .vLine(-pitch + base_chamfer * 2.0)
                .line(base_chamfer, -base_chamfer)
            )
        base = base.hLine(base_width - base_chamfer * 2.0)
        for x in range(0, n):
            base = (
                base.line(base_chamfer, base_chamfer)
                .vLine(pitch - base_chamfer * 2.0)
                .line(-base_chamfer, base_chamfer)
            )
    base = base.close().extrude(base_height)
    return base


def make_Horizontal_THT_base(
    n, pitch, rows, base_width, base_height, base_x_offset, base_chamfer
):
    if base_chamfer == 0:
        base = (
            cq.Workplane("ZY")
            .workplane(
                centerOption="CenterOfMass",
                offset=-(base_x_offset + (rows - 1) * pitch),
            )
            .moveTo(0.0, pitch / 2.0)
            .vLine(n * -pitch)
            .hLine(base_width)
            .vLine(n * pitch)
        )
    else:
        base = (
            cq.Workplane("ZY")
            .workplane(
                centerOption="CenterOfMass",
                offset=-(base_x_offset + (rows - 1) * pitch),
            )
            .moveTo(base_chamfer, pitch / 2.0)
        )
        for x in range(0, n):
            base = (
                base.line(-base_chamfer, -base_chamfer)
                .vLine(-pitch + base_chamfer * 2.0)
                .line(base_chamfer, -base_chamfer)
            )
        base = base.hLine(base_width - base_chamfer * 2.0)
        for x in range(0, n):
            base = (
                base.line(base_chamfer, base_chamfer)
                .vLine(pitch - base_chamfer * 2.0)
                .line(-base_chamfer, base_chamfer)
            )
    base = base.close().extrude(-base_height)
    return base


def make_Vertical_SMD_base(
    n,
    pitch,
    base_width,
    base_height,
    base_chamfer,
    base_z_offset=0,
    base_extra_length=0,
    base_wall_height=0,
    base_wall_internal_width=0,
    base_wall_internal_extra_length=0,
    notch_position="",
    notch_x_size=0,
    notch_y_size=0,
    notch_height=0,
):
    if base_chamfer == 0:
        base = (
            cq.Workplane("XY")
            .workplane(offset=base_z_offset)
            .moveTo(-base_width / 2.0, n / 2.0 * pitch + base_extra_length / 2.0)
            .vLine(n * -pitch - base_extra_length)
            .hLine(base_width)
            .vLine(n * pitch + base_extra_length)
        )
    else:
        base = (
            cq.Workplane("XY")
            .workplane(offset=base_z_offset)
            .moveTo(
                -base_width / 2.0 + base_chamfer,
                n / 2.0 * pitch + base_extra_length / 2.0,
            )
        )
        if base_extra_length != 0:
            base = base.line(-base_chamfer, -base_chamfer)
            base = base.vLine(-base_extra_length / 2.0 + base_chamfer * 2.0)
            base = base.line(base_chamfer, -base_chamfer)
        for x in range(0, n):
            base = (
                base.line(-base_chamfer, -base_chamfer)
                .vLine(-pitch + base_chamfer * 2.0)
                .line(base_chamfer, -base_chamfer)
            )
        if base_extra_length != 0:
            base = base.line(-base_chamfer, -base_chamfer)
            base = base.vLine(-base_extra_length / 2.0 + base_chamfer * 2.0)
            base = base.line(base_chamfer, -base_chamfer)
        base = base.hLine(base_width - base_chamfer * 2.0)
        if base_extra_length != 0:
            base = base.line(base_chamfer, base_chamfer)
            base = base.vLine(base_extra_length / 2.0 - base_chamfer * 2.0)
            base = base.line(-base_chamfer, base_chamfer)
        for x in range(0, n):
            base = (
                base.line(base_chamfer, base_chamfer)
                .vLine(pitch - base_chamfer * 2.0)
                .line(-base_chamfer, base_chamfer)
            )
        if base_extra_length != 0:
            base = base.line(base_chamfer, base_chamfer)
            base = base.vLine(base_extra_length / 2.0 - base_chamfer * 2.0)
            base = base.line(-base_chamfer, base_chamfer)
    base = base.close().extrude(base_height)

    if base_wall_height != 0:
        wall = (
            cq.Workplane("XY")
            .workplane(offset=base_z_offset)
            .rect(base_width, n * pitch + base_extra_length)
            .extrude(base_wall_height)
        )
        wall = wall.cut(
            cq.Workplane("XY")
            .rect(
                base_wall_internal_width,
                (n - 1) * pitch + base_wall_internal_extra_length,
            )
            .extrude(base_wall_height + base_z_offset)
        )
        base = base.union(wall)

    if notch_height != 0:
        if notch_position == "left":
            cutout = (
                cq.Workplane("XY")
                .workplane(offset=base_z_offset + base_wall_height - notch_height)
                .rect(notch_x_size * 2.0, notch_y_size)
                .extrude(base_wall_height)
                .translate((-base_width / 2.0, 0, 0))
            )
        elif notch_position == "right":
            cutout = (
                cq.Workplane("XY")
                .workplane(offset=base_wall_height - notch_height)
                .rect(notch_x_size * 2.0, notch_y_size)
                .extrude(base_wall_height)
                .translate((base_width / 2.0, 0, 0))
            )
        elif notch_position == "top":
            cutout = (
                cq.Workplane("XY")
                .workplane(offset=base_wall_height - notch_height)
                .rect(notch_x_size, notch_y_size * 2)
                .extrude(base_wall_height)
                .translate((0, (n * pitch + base_extra_length) / 2, 0))
            )
        elif notch_position == "bottom":
            cutout = (
                cq.Workplane("XY")
                .workplane(offset=base_wall_height - notch_height)
                .rect(notch_x_size, notch_y_size * 2)
                .extrude(base_wall_height)
                .translate((0, -(n * pitch + base_extra_length) / 2, 0))
            )
        base = base.cut(cutout)

    return base


def make_Vertical_THT_pins(
    n,
    pitch,
    rows,
    pin_length_above_base,
    pin_length_below_board,
    base_height,
    pin_width,
    pin_end_chamfer,
):
    total_length = pin_length_below_board + base_height + pin_length_above_base
    pin = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=-pin_length_below_board)
        .box(pin_width, pin_width, total_length, centered=(True, True, False))
    )
    if pin_end_chamfer > 0:
        pin = pin.edges("#Z").chamfer(pin_end_chamfer)

    pins = []
    for x in range(rows):
        for y in range(n):
            pins.append(pin.translate((x * pitch, y * -pitch, 0)))

    return union_all(pins)


def make_Horizontal_THT_pins(
    n,
    pitch,
    rows,
    pin_length_above_base,
    pin_length_below_board,
    base_height,
    base_width,
    pin_width,
    pin_end_chamfer,
    base_x_offset,
):
    R1 = pin_width
    pin_array = []
    for row in range(rows):
        row_offset = row * pitch
        pin_array.append(
            cq.Workplane("XZ")
            .workplane(centerOption="CenterOfMass", offset=-pin_width / 2)
            .moveTo(
                base_x_offset
                + (rows - 1) * pitch
                + base_height
                + pin_length_above_base,
                (base_width - ((rows - 1) * pitch)) / 2 + pin_width / 2 + (row) * pitch,
            )
            .vLine(-pin_width)
            .hLine(
                -pin_length_above_base
                - base_height
                - base_x_offset
                - row_offset
                + pin_width / 2
            )
            .vLine(
                -(base_width / rows - pin_width) / 2
                - pin_length_below_board
                - row_offset
            )
            .hLine(-pin_width)
            .vLine(
                ((base_width / rows) - pin_width) / 2
                + pin_length_below_board
                + row_offset
                + pin_width
            )
            .close()
            .extrude(pin_width)
            .edges("<X and >Z")
            .fillet(pin_width)
        )

        if pin_end_chamfer > 0:
            pin_array[row] = pin_array[row].faces("<Z").chamfer(pin_end_chamfer)
            pin_array[row] = pin_array[row].faces(">X").chamfer(pin_end_chamfer)

    pins = []
    for x in range(rows):
        for y in range(n):
            pins.append(pin_array[x].translate((0, y * -pitch, 0)))

    return union_all(pins)


def make_Vertical_SMD_pins(
    n,
    pitch,
    rows,
    pin_length_above_base,
    pin_length_horizontal,
    base_height,
    base_width,
    pin_width,
    pin_end_chamfer,
    base_z_offset,
    pin_1_start=None,
):
    R1 = pin_width
    pin_array = []
    pin_array.append(
        cq.Workplane("XZ")
        .workplane(
            centerOption="CenterOfMass", offset=-((n - 1) * pitch + pin_width) / 2
        )
        .moveTo(
            -((rows - 1) * pitch - pin_width) / 2,
            base_z_offset + base_height + pin_length_above_base,
        )
        .hLine(-pin_width)
        .vLine(-base_z_offset - base_height - pin_length_above_base + pin_width)
        .hLine(-pin_length_horizontal + pin_width)
        .vLine(-pin_width)
        .hLine(pin_length_horizontal)
        .close()
        .extrude(pin_width)
        .edges(">X and <Z")
        .fillet(pin_width)
    )
    if pin_end_chamfer > 0:
        pin_array[0] = pin_array[0].faces(">Z").chamfer(pin_end_chamfer)
        pin_array[0] = pin_array[0].faces("<X").chamfer(pin_end_chamfer)
    pin_array.append(
        cq.Workplane("XZ")
        .workplane(
            centerOption="CenterOfMass", offset=-((n - 1) * pitch + pin_width) / 2
        )
        .moveTo(
            ((rows - 1) * pitch - pin_width) / 2,
            base_z_offset + base_height + pin_length_above_base,
        )
        .hLine(pin_width)
        .vLine(-base_z_offset - base_height - pin_length_above_base + pin_width)
        .hLine(pin_length_horizontal - pin_width)
        .vLine(-pin_width)
        .hLine(-pin_length_horizontal)
        .close()
        .extrude(pin_width)
        .edges("<X and <Z")
        .fillet(pin_width)
    )
    if pin_end_chamfer > 0:
        pin_array[1] = pin_array[1].faces(">Z").chamfer(pin_end_chamfer)
        pin_array[1] = pin_array[1].faces(">X").chamfer(pin_end_chamfer)

    if rows == 1:
        if pin_1_start == "right":
            right_pin = range(1, n, 2)
            left_pin = range(0, n, 2)
        elif pin_1_start == "left":
            right_pin = range(0, n, 2)
            left_pin = range(1, n, 2)
        else:
            print("not found")
    else:
        right_pin = range(n)
        left_pin = range(n)

    pins = []
    for y in right_pin:
        pins.append(pin_array[0].translate((0, y * -pitch, 0)))
    for y in left_pin:
        pins.append(pin_array[1].translate((0, y * -pitch, 0)))
    return union_all(pins)
