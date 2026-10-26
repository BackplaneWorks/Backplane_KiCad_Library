#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is derived from a cadquery script for generating PDIP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
# This is a
# Dimensions are from Microchips Packaging Specification document:
# DS00000049BY. Body drawing is the same as QFP generator#
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
__title__ = "make GullWings ICs 3D models"
__author__ = "scripts: maurice and hyOzd; models: see cq_model files; update: jmwright"
__Comment__ = """This generator loads cadquery model scripts and generates step/wrl files for the official kicad library."""

from math import radians, tan

import cadquery as cq


def make_gw(params):

    c = params["c"]
    the = params["the"]
    ef = params["ef"]
    fp_s = params["fp_s"]
    fp_r = params["fp_r"]
    fp_d = params["fp_d"]
    fp_z = params["fp_z"]
    D1 = params["D1"]
    E1 = params["E1"]
    E = params["E"]

    A1 = params["A1"]
    A2 = params["A2"]
    b = params["b"]
    e = params["e"]
    npx = params["npx"]
    npy = params["npy"]
    # mN  = params.modelName
    place_pinMark = params["place_pinMark"]
    color_pin_mark = params["color_pin_mark"]
    rot = params["rotation"]
    # dest_dir_pref = params.dest_dir_prefix
    if params["excluded_pins"]:
        excluded_pins = params["excluded_pins"]
    else:
        excluded_pins = ()  ##no pin excluded

    A = A1 + A2
    A2_t = A - c  # body top part height
    A2_b = c - A1  # body bottom part height
    D1_t = D1 - 2 * tan(radians(the)) * A2_t  # top part upper width
    E1_t = E1 - 2 * tan(radians(the)) * A2_t  # top part upper length
    D1_b = D1 - 2 * tan(radians(the)) * A2_b  # bottom width
    E1_b = E1 - 2 * tan(radians(the)) * A2_b  # bottom length

    if params["L"]:
        L = params["L"]
    else:
        L = (E - E1_b) / 2

    epad_rotation = 0.0
    epad_offset_x = 0.0
    epad_offset_y = 0.0
    if params["epad"]:
        # if isinstance(params.epad, float):
        if not isinstance(params["epad"], list):
            sq_epad = False
            epad_r = params["epad"]
        else:
            sq_epad = True
            D2 = params["epad"][0]
            E2 = params["epad"][1]
            if len(params["epad"]) > 2:
                epad_rotation = params["epad"][2]
            if len(params["epad"]) > 3:
                if isinstance(params["epad"][3], str):
                    if params["epad"][3] == "-topin":
                        epad_offset_x = ((D1 + E - E1) / 2 - L - D2 / 2) * -1
                    elif params.epad[3] == "+topin":
                        epad_offset_x = (D1 + E - E1) / 2 - L - D2 / 2
                else:
                    epad_offset_x = params["epad"][3]
            if len(params["epad"]) > 4:
                if isinstance(params["epad"][4], str):
                    if params["epad"][4] == "-topin":
                        epad_offset_y = (E / 2 - L - E2 / 2) * -1
                    elif params["epad"][4] == "+topin":
                        epad_offset_y = E / 2 - L - E2 / 2
                else:
                    epad_offset_y = params["epad"][4]

    # calculated dimensions for body
    # checking pin lenght compared to overall width
    # d=(E-E1 -2*(S+L)-2*(R1))
    # FreeCAD.Console.PrintMessage('E='+str(E)+';E1='+str(E1)+'\r\n')

    totpinwidthx = (npx - 1) * e + b  # total width of all pins on the X side
    totpinwidthy = (npy - 1) * e + b  # total width of all pins on the Y side

    case = (
        cq.Workplane(cq.Plane.XY())
        .workplane(centerOption="CenterOfMass", offset=A1)
        .rect(D1_b, E1_b)
        .workplane(centerOption="CenterOfMass", offset=A2_b)
        .rect(D1, E1)
        .workplane(centerOption="CenterOfMass", offset=A2_t)
        .rect(D1_t, E1_t)
        .loft(ruled=True)
        .faces(">Z")
    )

    # bottomrect = cq.Workplane("XY").rect(E1_t1,D1_t1).translate((0,0,A1))
    # middlerect =cq.Workplane("XY").rect(E1,D1).translate((0,0,A1+c))
    # fp_s = True
    if fp_r == 0:
        # global place_pinMark
        place_pinMark = False
        fp_r = 0.1
    if fp_s == False:
        pinmark = (
            cq.Workplane(cq.Plane.XY())
            .workplane(centerOption="CenterOfMass", offset=A)
            .box(fp_r, E1_t - fp_d, fp_z * 2)
        )  # .translate((E1/2,0,A1)).rotate((0,0,0), (0,0,1), 90)
        # translate the object
        pinmark = pinmark.translate(
            (-D1_t / 2 + fp_r / 2.0 + fp_d / 2, 0, 0)
        )  # .rotate((0,0,0), (0,1,0), 0)
    else:
        # first pin indicator is created with a spherical pocket

        sphere_r = (fp_r * fp_r / 2 + fp_z * fp_z) / (2 * fp_z)
        sphere_z = A + sphere_r * 2 - fp_z - sphere_r
        # Revolve a cylinder from a rectangle
        # Switch comments around in this section to try the revolve operation with different parameters
        ##cylinder =
        # pinmark=cq.Workplane("XZ", (-D1_t2/2+fp_d+fp_r, -E1_t2/2+fp_d+fp_r, A)).rect(sphere_r/2, -fp_z, False).revolve()
        pinmark = (
            cq.Workplane(
                "XZ", origin=(-D1_t / 2 + fp_d + fp_r, -E1_t / 2 + fp_d + fp_r, A)
            )
            .rect(fp_r / 2, -fp_z + 0.1, False)
            .revolve()
        )

    # result = cadquery.Workplane("XY").rect(rectangle_width, rectangle_length, False).revolve(angle_degrees)
    # result = cadquery.Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5,-5))
    # result = cadquery.Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5, -5),(-5, 5))
    # result = cadquery.Workplane("XY").rect(rectangle_width, rectangle_length).revolve(angle_degrees,(-5,-5),(-5,5), False)

    ## color_attr=(255,255,255,0)
    ## show(pinmark, color_attr)
    ##sphere = cq.Workplane("XY", (-D1_t2/2+fp_d+fp_r, -E1_t2/2+fp_d+fp_r, sphere_z)). \
    ##         sphere(sphere_r)
    # color_attr=(255,255,255,0)
    # show(sphere, color_attr)
    # case = case.cut(sphere)
    if (color_pin_mark == False) and (place_pinMark == True):
        case = case.cut(pinmark)

    # Create a pin object at the center of top side.
    bpin = (
        cq.Workplane("XY")
        .box(L, b, c)
        .translate(((E - L) / 2, 0, c / 2))
        .rotate((0, 0, 0), (0, 0, 1), 90)
    )

    pins = []
    pincounter = 1
    first_pos_x = (npx - 1) * e / 2
    for i in range(npx):
        if pincounter not in excluded_pins:
            pin = bpin.translate((first_pos_x - i * e, 0, 0)).rotate(
                (0, 0, 0), (0, 0, 1), 180
            )
            pins.append(pin)
        pincounter += 1

    first_pos_y = (npy - 1) * e / 2
    for i in range(npy):
        if pincounter not in excluded_pins:
            pin = bpin.translate((first_pos_y - i * e, (D1 - E1) / 2, 0)).rotate(
                (0, 0, 0), (0, 0, 1), 270
            )
            pins.append(pin)
        pincounter += 1

    for i in range(npx):
        if pincounter not in excluded_pins:
            pin = bpin.translate((first_pos_x - i * e, 0, 0))
            pins.append(pin)
        pincounter += 1

    for i in range(npy):
        if pincounter not in excluded_pins:
            pin = bpin.translate((first_pos_y - i * e, (D1 - E1) / 2, 0)).rotate(
                (0, 0, 0), (0, 0, 1), 90
            )
            pins.append(pin)
        pincounter += 1

    # create exposed thermal pad if requested
    if params["epad"]:
        if sq_epad:
            pins.append(
                cq.Workplane("XY")
                .box(D2, E2, A1)
                .translate((epad_offset_x, epad_offset_y, A1 / 2))
                .rotate((0, 0, 0), (0, 0, 1), epad_rotation)
            )
        else:
            # epad = cq.Workplane("XY", (0,0,A1/2)). \
            epad = cq.Workplane("XY").circle(epad_r).extrude(A1)
            # extrude(A1+A1/10)
            pins.append(epad)
    # merge all pins to a single object
    merged_pins = pins[0]
    for p in pins[1:]:
        merged_pins = merged_pins.union(p)
    pins = merged_pins

    # extract pins from case
    case = case.cut(pins)

    return (case, pins, pinmark)
