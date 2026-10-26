# -*- coding: utf8 -*-
#!/usr/bin/python
#
# CadQuery script returning Molex PicoBlade 53398 Connectors

## requirements
## freecad (v1.5 and v1.6 have been tested)
## cadquery FreeCAD plugin (v0.3.0 and v0.2.0 have been tested)
##   https://github.com/jmwright/cadquery-freecad-module

## This script can be run from within the cadquery module of freecad.
## To generate VRML/ STEP files for, use launch-cq-molex
## script of the parent directory.

# * This is a cadquery script for the generation of MCAD Models.             *
# *                                                                          *
# *   Copyright (c) 2016                                                     *
# * Rene Poeschl https://github.com/poeschlr                                 *
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
# * The models generated with this script add the following exception:       *
# *   As a special exception, if you create a design which uses this symbol, *
# *   and embed this symbol or unaltered portions of this symbol into the    *
# *   design, this symbol does not by itself cause the resulting design to   *
# *   be covered by the GNU General Public License. This exception does not  *
# *   however invalidate any other reasons why the design itself might be    *
# *   covered by the GNU General Public License. If you modify this symbol,  *
# *   you may extend this exception to your version of the symbol, but you   *
# *   are not obligated to do so. If you do not wish to do so, delete this   *
# *   exception statement from your version.                                 *
# ****************************************************************************

__title__ = "model description for Molex 53398 Connectors"
__author__ = "poeschlr"
__Comment__ = "model description for Molex 53398 Connectors using cadquery"

___ver___ = "1.0 10/04/2016"


class LICENCE_Info:
    ############################################################################
    STR_licAuthor = "Rene Poeschl"
    STR_licEmail = "poeschlr@gmail.com"
    STR_licOrgSys = ""
    STR_licPreProc = ""

    LIST_license = [
        "",
    ]
    ############################################################################


# import sys

# DIRTY HACK TO ALLOW CENTRALICED HELPER SCRIPTS. (freecad cadquery does copy the file to /tmp and we can therefore not use relative paths for importing)

# if "module" in __name__ :
#     for path in sys.path:
#         if 'molex/cq_models':
#             p1 = path.replace('molex/cq_models','_tools')
#     if not p1 in sys.path:
#         sys.path.append(p1)
# else:
#     sys.path.append('../_tools')

import cadquery as cq

from generators.tools.model.cq_helpers import *

# from math import sqrt
# from Helpers import show
# from collections import namedtuple
# import FreeCAD

# global parameter

# mounting_pad_size_y = 3.0
# # y dimensions for pad given relative to mounting pad edge
# rel_pad_y_outside_edge = 4.9
# rel_pad_y_inside_edge = 3.6

# # amount to shift y position of center for pick-and-place (positive -> shift whole footprint up)
# center_shift_y = -0.55
# y_origin_from_mountpad = -rel_pad_y_outside_edge/2 + mounting_pad_size_y/2 + center_shift_y


# mount_pin_lenght = 1.7
# mount_pin_width = 2.2
# mount_pin_thickness = 0.25
# mount_pin_bend_radius = 0.1 #estimated
# mount_pin_height = 1.6 #Measured
# mount_pin_top_len = 0.8 #Measured
# mount_pin_fillet = 0.3

# mount_holder_len = 1.5
# mount_holder_width = 2.8
# mount_holder_top_z = 2.65 #Measured
# mount_holder_chamfer = 0.5 #Measured (+/-0.1 at least)

# pin_width = 0.32
# pin_pitch = 1.25
# pin_protrution = 0.5
# pin_contact_len = 0.6
# pin_front_height = 0.45
# pin_slope_len = 0.3 #estimated
# pin_back_z = 0.3 #Measured
# pin_len = 3.9 #Measured
# center_pin_pad_y = 2.75
# pin_center_offset = 0.05 # estimated
# pin_tip_y = center_pin_pad_y + pin_center_offset + pin_contact_len/2.0
# pin_tip_chamfer = 0.1


# contact_to_front = 2.175
# contact_len = 0.6 #Measured (+/-0.1 at least)
# contact_top_z = 3.9 #Measured (+/-0.1 at least)
# contact_chamfer_len = 0.1 #estimated
# contact_chamfer_width = 0.05 #estimated
# contact_chamfer_depth = 0.5 #estimated

# body_width = 3.7
# body_back_width = 0.4
# body_side_width = 0.6
# body_main_z = 0.3 #Measured
# body_pin_cutout_depth = 0.5 #Measured
# body_pin_cutout_len = 0.9 #Measured
# body_front_plastic_protution = 0.2 # estimated
# body_center_y = -pin_tip_y+pin_protrution+body_width/2
# body_support_width = 0.5
# body_cutout_depth = 3.0
# body_front_cutout_depth = 1.0 #Measured (+/-0.1 at least)
# body_top_chamfer=0.2 #estimated

# body_cutout_width = 2.4

# connector_height = 4.7

# back_cutout_center_to_side = 2.0 #Measured
# back_cutout_b_height = 1.15
# back_cutout_b_width = 1.15
# back_cutout_t_height = 1.45
# back_cutout_t_width = 0.3 #Measured (+/-0.1 at least)

# class series_params():
#     manufacturer = 'Molex'
#     series = "PicoBlade"
#     mpn_format_string = '53398-{pins_per_row:02d}71'
#     orientation = 'V'
#     number_of_rows = 1
#     datasheet = 'http://www.molex.com/pdm_docs/sd/533980271_sd.pdf'
#     pinrange = range(2,16)
#     mount_pin = '-1MP'

#     body_color_key = "white body"
#     pins_color_key = "metal grey pins"

#     color_keys = [
#         body_color_key,
#         pins_color_key
#     ]
#     obj_suffixes = [
#         '__body',
#         '__pins'
#     ]

#     pitch = pin_pitch

# Params = namedtuple("Params",[
#     'num_pins',
#     'body_length',
#     'body_front_cutout_len'
# ])


def make_params(series_params, num_pins):
    body_length = 3 + (num_pins - 1) * series_params["pin_pitch"]
    body_front_cutout_len = body_length - 1.9

    return (num_pins, body_length, body_front_cutout_len)


def generate_pins(series_params, num_pins):
    (num_pins, body_length, body_front_cutout_len) = make_params(
        series_params, num_pins
    )
    # num_pins = series_params['num_pins']
    # body_len = series_params['body_length']

    first_pin_wp_offset = (num_pins - 1) / 2.0 * series_params[
        "pin_pitch"
    ] - series_params["pin_width"] / 2.0

    pin = (
        cq.Workplane("YZ")
        .workplane(offset=first_pin_wp_offset, centerOption="CenterOfMass")
        .moveTo(series_params["pin_tip_y"], 0)
        .vLine(series_params["pin_front_height"])
        .hLine(-series_params["pin_protrusion"])
        .line(
            -series_params["pin_slope_len"],
            series_params["body_main_z"]
            + series_params["body_pin_cutout_depth"]
            - series_params["pin_front_height"],
        )
        .hLine(-series_params["contact_to_front"] + series_params["pin_slope_len"])
        .vLineTo(series_params["contact_top_z"])
        .hLine(-series_params["contact_len"])
        .vLineTo(series_params["body_main_z"] + series_params["body_pin_cutout_depth"])
        .hLineTo(-series_params["pin_len"] + series_params["pin_tip_y"])
        .vLineTo(series_params["pin_back_z"])
        .hLineTo(
            series_params["pin_tip_y"]
            - series_params["pin_contact_len"]
            - series_params["pin_slope_len"]
        )
        .lineTo(
            series_params["center_pin_pad_y"] - series_params["pin_contact_len"] / 2, 0
        )
        .close()
        .extrude(series_params["pin_width"])
    )

    pin = (
        pin.faces(">Z")
        .edges("<Y")
        .chamfer(
            series_params["contact_chamfer_len"], series_params["contact_chamfer_depth"]
        )
    )
    pin = (
        pin.faces(">Z")
        .edges(">Y")
        .chamfer(
            series_params["contact_chamfer_len"], series_params["contact_chamfer_depth"]
        )
    )
    pin = (
        pin.faces(">Z")
        .edges(">X")
        .chamfer(
            series_params["contact_chamfer_width"],
            series_params["contact_chamfer_depth"],
        )
    )
    pin = (
        pin.faces(">Z")
        .edges("<X")
        .chamfer(
            series_params["contact_chamfer_width"],
            series_params["contact_chamfer_depth"],
        )
    )
    # pin = pin.faces(">Y").edges("|X")\
    #    .chamfer(pin_tip_chamfer)
    pins = pin
    for i in range(0, num_pins):
        pins = pins.union(pin.translate((-i * series_params["pin_pitch"], 0, 0)))

    outher_bend_radius = (
        series_params["mount_pin_bend_radius"] + series_params["mount_pin_thickness"]
    )
    mount_pin_tip_x = body_length / 2 + series_params["mount_pin_length"]
    mount_pin_points = [(mount_pin_tip_x, 0)]
    arc_points = []
    add_p_to_chain(mount_pin_points, (0, series_params["mount_pin_thickness"]))
    add_p_to_chain(
        mount_pin_points,
        (
            -series_params["mount_pin_length"]
            + series_params["mount_pin_thickness"]
            + series_params["mount_pin_bend_radius"],
            0,
        ),
    )
    add_p_to_chain(
        mount_pin_points,
        (
            -series_params["mount_pin_bend_radius"],
            series_params["mount_pin_bend_radius"],
        ),
    )
    arc_points.append(get_third_arc_point2(mount_pin_points[2], mount_pin_points[3]))
    add_p_to_chain(
        mount_pin_points,
        (
            0,
            series_params["mount_pin_height"]
            - 2
            * (
                series_params["mount_pin_thickness"]
                + series_params["mount_pin_bend_radius"]
            ),
        ),
    )
    add_p_to_chain(
        mount_pin_points,
        (
            series_params["mount_pin_bend_radius"],
            series_params["mount_pin_bend_radius"],
        ),
    )
    arc_points.append(get_third_arc_point1(mount_pin_points[4], mount_pin_points[5]))
    add_p_to_chain(
        mount_pin_points,
        (
            series_params["mount_pin_top_len"]
            - series_params["mount_pin_bend_radius"]
            - series_params["mount_pin_thickness"],
            0,
        ),
    )
    add_p_to_chain(mount_pin_points, (0, series_params["mount_pin_thickness"]))
    add_p_to_chain(
        mount_pin_points,
        (
            -series_params["mount_pin_top_len"]
            + series_params["mount_pin_bend_radius"]
            + series_params["mount_pin_thickness"],
            0,
        ),
    )
    add_p_to_chain(mount_pin_points, (-outher_bend_radius, -outher_bend_radius))
    arc_points.append(get_third_arc_point2(mount_pin_points[8], mount_pin_points[9]))
    add_p_to_chain(
        mount_pin_points,
        (
            0,
            -series_params["mount_pin_height"]
            + 2
            * (
                series_params["mount_pin_thickness"]
                + series_params["mount_pin_bend_radius"]
            ),
        ),
    )
    add_p_to_chain(mount_pin_points, (outher_bend_radius, -outher_bend_radius))
    arc_points.append(get_third_arc_point1(mount_pin_points[10], mount_pin_points[11]))

    mount_pin1 = (
        cq.Workplane("XZ")
        .workplane(
            offset=-series_params["mount_pin_width"] / 2, centerOption="CenterOfMass"
        )
        .moveTo(*mount_pin_points[0])
        .lineTo(*mount_pin_points[1])
        .lineTo(*mount_pin_points[2])
        .threePointArc(arc_points[0], mount_pin_points[3])
        .lineTo(*mount_pin_points[4])
        .threePointArc(arc_points[1], mount_pin_points[5])
        .lineTo(*mount_pin_points[6])
        .lineTo(*mount_pin_points[7])
        .lineTo(*mount_pin_points[8])
        .threePointArc(arc_points[2], mount_pin_points[9])
        .lineTo(*mount_pin_points[10])
        .threePointArc(arc_points[3], mount_pin_points[11])
        .close()
        .extrude(series_params["mount_pin_width"])
    )

    # mount_pin1 = mount_pin1.faces(">X").edges("|Z").fillet(mount_pin_fillet)
    mount_pin1 = (
        mount_pin1.faces(">Y")
        .edges(">X")
        .chamfer(series_params["mount_pin_fillet"], series_params["mount_pin_fillet"])
    )
    mount_pin1 = (
        mount_pin1.faces("<Y")
        .edges(">X")
        .chamfer(series_params["mount_pin_fillet"], series_params["mount_pin_fillet"])
    )

    mount_pin_points = mirror(mount_pin_points)
    arc_points = mirror(arc_points)

    mount_pin2 = (
        cq.Workplane("XZ")
        .workplane(
            offset=-series_params["mount_pin_width"] / 2, centerOption="CenterOfMass"
        )
        .moveTo(*mount_pin_points[0])
        .lineTo(*mount_pin_points[1])
        .lineTo(*mount_pin_points[2])
        .threePointArc(arc_points[0], mount_pin_points[3])
        .lineTo(*mount_pin_points[4])
        .threePointArc(arc_points[1], mount_pin_points[5])
        .lineTo(*mount_pin_points[6])
        .lineTo(*mount_pin_points[7])
        .lineTo(*mount_pin_points[8])
        .threePointArc(arc_points[2], mount_pin_points[9])
        .lineTo(*mount_pin_points[10])
        .threePointArc(arc_points[3], mount_pin_points[11])
        .close()
        .extrude(series_params["mount_pin_width"])
    )
    # mount_pin2 = mount_pin2.faces("<X").edges("|Z").fillet(mount_pin_fillet)
    mount_pin2 = (
        mount_pin2.faces(">Y")
        .edges("<X")
        .chamfer(series_params["mount_pin_fillet"], series_params["mount_pin_fillet"])
    )
    mount_pin2 = (
        mount_pin2.faces("<Y")
        .edges("<X")
        .chamfer(series_params["mount_pin_fillet"], series_params["mount_pin_fillet"])
    )

    pins = pins.union(mount_pin1)
    pins = pins.union(mount_pin2)
    return pins


def generate_body(series_params, num_pins):
    (num_pins, body_length, body_front_cutout_len) = make_params(
        series_params, num_pins
    )
    # body_len = series_params['body_length']
    # body_front_cutout_len = series_params['body_front_cutout_len']
    # num_pins = series_params['num_pins']
    first_pin_center_x = (num_pins - 1) / 2.0 * series_params["pin_pitch"]

    body = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass")
        .moveTo(0, -series_params["body_center_y"])
        .rect(body_length, series_params["body_width"])
        .extrude(series_params["connector_height"])
    )
    body = (
        body.faces("<Z")
        .workplane(centerOption="CenterOfMass")
        .rect(
            body_length - 2 * series_params["body_support_width"],
            series_params["body_width"],
        )
        .cutBlind(-series_params["body_main_z"])
    )
    pin_cutout = (
        cq.Workplane("XY")
        .workplane(offset=series_params["body_main_z"], centerOption="CenterOfMass")
        .moveTo(first_pin_center_x, -series_params["body_center_y"])
        .rect(series_params["body_pin_cutout_len"], series_params["body_width"])
        .extrude(series_params["body_pin_cutout_depth"])
    )
    pin_cutouts = pin_cutout
    for i in range(0, num_pins):
        pin_cutouts = pin_cutouts.union(
            pin_cutout.translate((-i * series_params["pin_pitch"], 0, 0))
        )
    body = body.cut(pin_cutouts)

    front_thickness = (
        series_params["body_width"]
        - series_params["body_cutout_width"]
        - series_params["body_back_width"]
        - series_params["body_front_plastic_protrusion"]
    )
    body = (
        body.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .moveTo(
            -body_length / 2.0 + series_params["body_side_width"],
            -series_params["body_width"] / 2.0 + series_params["body_back_width"],
        )
        .hLine(body_length - 2 * series_params["body_side_width"])
        .vLine(series_params["body_cutout_width"])
        .hLineTo(body_front_cutout_len / 2.0)
        .vLineTo(
            series_params["body_width"] / 2
            - series_params["body_front_plastic_protrusion"]
        )
        .hLineTo(body_length / 2.0)
        .vLineTo(series_params["body_width"] / 2.0)
        .hLine(-body_length)
        .vLine(-series_params["body_front_plastic_protrusion"])
        .hLineTo(-body_front_cutout_len / 2.0)
        .vLine(-front_thickness)
        .hLineTo(-body_length / 2.0 + series_params["body_side_width"])
        .close()
        .cutBlind(-series_params["body_cutout_depth"])
    )

    body_front_cutout = (
        cq.Workplane("XY")
        .workplane(
            offset=series_params["connector_height"], centerOption="CenterOfMass"
        )
        .moveTo(
            0,
            -series_params["body_center_y"]
            + series_params["body_width"] / 2.0
            - series_params["body_front_plastic_protrusion"]
            - front_thickness / 2.0,
        )
        .rect(body_length, front_thickness)
        .extrude(-series_params["body_front_cutout_depth"])
    )
    body = body.cut(body_front_cutout)

    # BS = cq.selectors.BoxSelector
    # body = body.edges(BS(
    #     (-body_length/2.0+series_params['body_side_width']/2.0,
    #      -series_params['body_center_y']+series_params['body_width']/2.0,
    #      series_params['connector_height']-0.3),
    #     (body_length/2.0-series_params['body_side_width']/2.0,
    #      -series_params['body_center_y']-series_params['body_width']/2.0+series_params['body_back_width']/2.0,
    #      series_params['connector_height']+1),True))\
    #      .chamfer(series_params['body_top_chamfer'])

    back_y = series_params["body_center_y"] + series_params["body_width"] / 2

    back_cutout_center_x = 0
    if num_pins > 3:
        back_cutout_center_x = (
            body_length / 2 - series_params["back_cutout_center_to_side"]
        )

    back_cutout = (
        cq.Workplane("XZ")
        .workplane(back_y, centerOption="CenterOfMass")
        .moveTo(
            back_cutout_center_x - series_params["back_cutout_t_width"] / 2,
            series_params["connector_height"],
        )
        .hLine(series_params["back_cutout_t_width"])
        .vLine(-series_params["back_cutout_t_height"])
        .hLine(
            (
                series_params["back_cutout_b_width"]
                - series_params["back_cutout_t_width"]
            )
            / 2.0
        )
        .vLine(-series_params["back_cutout_b_height"])
        .hLine(-series_params["back_cutout_b_width"])
        .vLine(series_params["back_cutout_b_height"])
        .hLine(
            (
                series_params["back_cutout_b_width"]
                - series_params["back_cutout_t_width"]
            )
            / 2.0
        )
        .close()
        .extrude(-series_params["body_back_width"])
    )

    if num_pins > 3:
        back_cutout = back_cutout.union(
            back_cutout.translate(
                (-body_length + 2 * series_params["back_cutout_center_to_side"], 0, 0)
            )
        )
    body = body.cut(back_cutout)

    sp = (body_length / 2.0, series_params["body_main_z"])
    poly_points = [
        v_add(
            sp,
            (
                series_params["mount_holder_len"]
                - series_params["mount_holder_chamfer"],
                0,
            ),
        )
    ]
    add_p_to_chain(
        poly_points,
        (series_params["mount_holder_chamfer"], series_params["mount_holder_chamfer"]),
    )
    add_p_to_chain(
        poly_points,
        (
            0,
            series_params["mount_holder_top_z"]
            - series_params["mount_holder_chamfer"]
            - series_params["body_main_z"],
        ),
    )
    add_p_to_chain(poly_points, (-series_params["mount_holder_len"], 0))
    mount_holder1 = (
        cq.Workplane("XZ")
        .workplane(back_y, centerOption="CenterOfMass")
        .moveTo(*sp)
        .polyline(poly_points, includeCurrent=True)
        .close()
        .extrude(-series_params["mount_holder_width"])
    )

    poly_points = mirror(poly_points)
    mount_holder2 = (
        cq.Workplane("XZ")
        .workplane(back_y, centerOption="CenterOfMass")
        .moveTo(-sp[0], sp[1])
        .polyline(poly_points, includeCurrent=True)
        .close()
        .extrude(-series_params["mount_holder_width"])
    )

    poly_points = [v_add(sp, (series_params["mount_pin_thickness"], 0))]
    add_p_to_chain(
        poly_points,
        (
            0,
            series_params["mount_pin_height"]
            - series_params["mount_pin_bend_radius"]
            - series_params["mount_pin_thickness"]
            - series_params["body_main_z"],
        ),
    )
    add_p_to_chain(
        poly_points,
        (
            series_params["mount_pin_bend_radius"],
            series_params["mount_pin_bend_radius"],
        ),
    )
    add_p_to_chain(
        poly_points,
        (
            series_params["mount_pin_top_len"]
            - series_params["mount_pin_bend_radius"]
            - series_params["mount_pin_thickness"],
            0,
        ),
    )
    add_p_to_chain(poly_points, (0, series_params["mount_pin_thickness"]))
    add_p_to_chain(poly_points, (-series_params["mount_pin_top_len"], 0))
    mount_holder1_cutout = (
        cq.Workplane("XZ")
        .workplane(back_y, centerOption="CenterOfMass")
        .moveTo(*sp)
        .polyline(poly_points, includeCurrent=True)
        .close()
        .extrude(-series_params["mount_pin_width"])
    )

    poly_points = mirror(poly_points)
    mount_holder2_cutout = (
        cq.Workplane("XZ")
        .workplane(back_y, centerOption="CenterOfMass")
        .moveTo(-sp[0], sp[1])
        .polyline(poly_points, includeCurrent=True)
        .close()
        .extrude(-series_params["mount_pin_width"])
    )

    body = body.union(mount_holder1)
    body = body.union(mount_holder2)
    body = body.cut(mount_holder1_cutout)
    body = body.cut(mount_holder2_cutout)
    return body


def generate_part(series_params, pincount):
    params = make_params(series_params, pincount)
    pins = generate_pins(series_params, pincount)
    body = generate_body(series_params, pincount)
    dummy_latch = cq.Workplane()
    pins = pins.translate((0, -series_params["y_origin_from_mountpad"], 0))
    body = body.translate((0, -series_params["y_origin_from_mountpad"], 0))
    return (pins, body, dummy_latch)


# #opend from within freecad
# if "module" in __name__ :
#     #part_to_build = 2
#     part_to_build = 4
#     FreeCAD.Console.PrintMessage("Started from cadquery: Building " +str(part_to_build)+"\n")
#     (pins, body) = generate_part(part_to_build)
#     show(pins)
#     show(body)
