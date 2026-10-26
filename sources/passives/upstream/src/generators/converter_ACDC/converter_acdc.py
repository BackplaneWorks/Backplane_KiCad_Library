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

import cadquery as cq

CASE_THT_TYPE = "tht"
CASE_SMD_TYPE = "smd"
CASE_THTSMD_TYPE = "thtsmd"
CASE_THT_N_TYPE = "tht_n"


CORNER_NONE_TYPE = "none"
CORNER_CHAMFER_TYPE = "chamfer"
CORNER_FILLET_TYPE = "fillet"


def make_case(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body seperation height
    rim = params["rim"]  # Rim underneath
    rotation = params["rotation"]  # rotation if required
    pin1corner = params["pin1corner"]  # Left upp corner relationsship to pin 1
    pin = params["pin"]  # pin/pad cordinates
    roundbelly = params["roundbelly"]  # If belly of caseing should be round (or flat)
    pintype = params["pintype"]  # pin type , like SMD or THT

    ff = W / 20.0

    if ff > 0.25:
        ff = 0.25

    mvX = 0
    mvY = 0
    # Dummy
    case = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=A1)
        .moveTo(0, 0)
        .rect(1, 1, False)
        .extrude(H)
    )

    if pintype == CASE_SMD_TYPE:
        mvX = 0 - (L / 2.0)
        mvY = 0 - (W / 2.0)
        case = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=A1)
            .moveTo(mvX, mvY)
            .rect(L, W, False)
            .extrude(H)
        )
    elif (pintype == CASE_THT_TYPE) or (pintype == CASE_THT_N_TYPE):
        p = pin[0]
        mvX = p[0] + pin1corner[0]
        mvY = p[1] - pin1corner[1]
        case = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=A1)
            .moveTo(mvX, mvY)
            .rect(L, -W, False)
            .extrude(H)
        )

    if rim != None:
        if len(rim) == 3:
            rdx = rim[0]
            rdy = rim[1]
            rdh = rim[2]
            print("\r\n")
            print("rdx " + str(rdx) + "\r\n")
            print("rdy " + str(rdy) + "\r\n")
            print("rdh " + str(rdh) + "\r\n")
            print("\r\n")
            case1 = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=A1)
                .moveTo(mvX + rdx, mvY)
                .rect(L - (2.0 * rdx), 0 - (W + 1.0), False)
                .extrude(rdh)
            )
            case = case.cut(case1)
            case1 = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=A1)
                .moveTo(mvX, mvY - rdy)
                .rect(L + 1.0, 0 - (W - (2.0 * rdy)), False)
                .extrude(rdh)
            )
            case = case.cut(case1)

    case = case.faces("<X").edges("<Y").fillet(ff)
    case = case.faces("<X").edges(">Y").fillet(ff)
    case = case.faces(">X").edges("<Y").fillet(ff)
    case = case.faces(">X").edges(">Y").fillet(ff)
    case = case.faces(">Y").edges(">Z").fillet(ff)

    if roundbelly == 1 and rim == None:
        # Belly is rounded
        case = case.faces(">Y").edges("<Z").fillet(ff / 2.0)

    if rotation != 0:
        case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

    return case


def make_case_top(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body seperation height
    rotation = params["rotation"]  # rotation if required
    pin1corner = params["pin1corner"]  # Left upp corner relationsship to pin 1
    pin = params["pin"]  # pin/pad cordinates
    show_top = params["show_top"]  # If top should be visible or not
    pintype = params["pintype"]  # pin type , like SMD or THT

    # print('make_case_top\r\n')

    mvX = 0
    mvY = 0
    # Dummy
    casetop = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=A1 + H)
        .moveTo(0, 0)
        .rect(1, 1, False)
        .extrude(0.8)
    )

    ff = W / 20.0
    if ff > 1.0:
        ff = 1.0

    Ldt = ff
    Wdt = ff

    L1 = L - (2.0 * Ldt)
    W1 = W - (2.0 * Wdt)

    if show_top == 1:
        tty = A1 + H - 0.1

        if pintype == CASE_SMD_TYPE:
            mvX = (0 - (L1 / 2.0)) + ((L - L1) / 2.0)
            mvY = (0 - (W1 / 2.0)) - ((W - W1) / 2.0)
            casetop = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=tty)
                .moveTo(mvX, mvY)
                .rect(L1, W1, False)
                .extrude(0.2)
            )
        elif pintype == CASE_THT_TYPE:
            p = pin[0]
            mvX = (p[0] + pin1corner[0]) + ((L - L1) / 2.0)
            mvY = (p[1] - pin1corner[1]) - ((W - W1) / 2.0)
            casetop = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=tty)
                .moveTo(mvX, mvY)
                .rect(L1, -W1, False)
                .extrude(0.2)
            )

        casetop = casetop.faces("<X").edges("<Y").fillet(ff)
        casetop = casetop.faces("<X").edges(">Y").fillet(ff)
        casetop = casetop.faces(">X").edges("<Y").fillet(ff)
        casetop = casetop.faces(">X").edges(">Y").fillet(ff)
    else:
        # If it is not used, just hide it inside the body
        if pintype == CASE_SMD_TYPE:
            mvX = 0
            mvY = 0
            casetop = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=A1 + (H / 4.0))
                .moveTo(mvX, mvY)
                .rect(0.1, 0.1, False)
                .extrude(0.1)
            )
        else:
            p = pin[0]
            mvX = (p[0] + pin1corner[0]) + (L / 2.0)
            mvY = (p[1] - pin1corner[1]) - (W / 2.0)
            casetop = (
                cq.Workplane("XY")
                .workplane(centerOption="CenterOfMass", offset=A1 + (H / 4.0))
                .moveTo(mvX, mvY)
                .rect(0.1, 0.1, False)
                .extrude(0.1)
            )

    if rotation != 0:
        casetop = casetop.rotate((0, 0, 0), (0, 0, 1), rotation)

    return casetop


def make_pins_tht(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body seperation height
    rim = params["rim"]  # Rim underneth
    pinpadsize = params["pinpadsize"]  # pin diameter or pad size
    pinpadh = params["pinpadh"]  # pin length, pad height
    pintype = params["pintype"]  # Casing type
    rotation = params["rotation"]  # rotation if required
    pin = params[
        "pin"
    ]  # pin/pad cordinates and an optional different size definition per pin as the third in place

    pinss = 0.1
    if rim != None:
        if len(rim) == 3:
            rdx = rim[0]
            rdy = rim[1]
            rdh = rim[2]
            pinss = rdh + 0.1

    p = pin[0]
    temp_size = pinpadsize

    if len(p) >= 3:
        temp_size = p[2]

    pins = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=A1 + pinss)
        .moveTo(p[0], -p[1])
        .circle(temp_size / 2.0, False)
        .extrude(0 - (pinpadh + pinss))
    )
    pins = pins.faces("<Z").fillet(temp_size / 5.0)

    for i in range(1, len(pin)):
        p = pin[i]
        temp_size = pinpadsize

        if len(p) >= 3:
            temp_size = p[2]

        pint = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=A1 + pinss)
            .moveTo(p[0], -p[1])
            .circle(temp_size / 2.0, False)
            .extrude(0 - (pinpadh + pinss))
        )
        pint = pint.faces("<Z").fillet(temp_size / 5.0)
        pins = pins.union(pint)

    if rotation != 0:
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return pins


def make_pins_tht_n(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body seperation height
    pinpadsize = params["pinpadsize"]  # pin diameter or pad size
    pinpadh = params["pinpadh"]  # pin length, pad height
    pintype = params["pintype"]  # Casing type
    rotation = params["rotation"]  # rotation if required
    pin = params["pin"]  # pin/pad cordinates

    # print('make_pins_tht_n\r\n')

    p = pin[0]
    pins = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=A1 + 2.0)
        .moveTo(p[0], -p[1])
        .circle(pinpadsize / 2.0, False)
        .extrude(0 - (pinpadh + 2.0))
    )
    pins = pins.faces("<Z").fillet(pinpadsize / 5.0)

    pint = (
        cq.Workplane("XZ")
        .workplane(centerOption="CenterOfMass", offset=0 - p[1])
        .moveTo(p[0], 2.0)
        .circle(pinpadsize / 2.0, False)
        .extrude(0 - (W / 2.0))
    )
    pins = pins.union(pint)

    for i in range(1, len(pin)):
        p = pin[i]
        pint = (
            cq.Workplane("XY")
            .workplane(centerOption="CenterOfMass", offset=A1 + 2.0)
            .moveTo(p[0], -p[1])
            .circle(pinpadsize / 2.0, False)
            .extrude(0 - (pinpadh + 2.0))
        )
        pint = pint.faces("<Z").fillet(pinpadsize / 5.0)
        pins = pins.union(pint)
        pint = (
            cq.Workplane("XZ")
            .workplane(centerOption="CenterOfMass", offset=0 - p[1])
            .moveTo(p[0], 2.0)
            .circle(pinpadsize / 2.0, False)
            .extrude(0 - (W / 2.0))
        )
        pins = pins.union(pint)

    if rotation != 0:
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return pins


def make_pins_smd(params):

    L = params["L"]  # package length
    W = params["W"]  # package width
    H = params["H"]  # package height
    A1 = params["A1"]  # Body seperation height
    pinpadsize = params["pinpadsize"]  # pin diameter or pad size
    pinpadh = params["pinpadh"]  # pin length, pad height
    pintype = params["pintype"]  # Casing type
    rotation = params["rotation"]  # rotation if required
    pin = params["pin"]  # pin/pad cordinates

    # print('make_pins_smd\r\n')

    #
    # Dummy
    #
    pins = (
        cq.Workplane("XY")
        .workplane(centerOption="CenterOfMass", offset=0)
        .moveTo(0, 0)
        .rect(0.1, 0.1)
        .extrude(0.1)
    )
    #

    for i in range(0, len(pin)):
        p = pin[i]
        myX1 = p[0] - pinpadsize
        myY1 = -p[1]
        xD = myX1
        yD = pinpadsize
        if p[0] < 0 and (p[1] > (0 - (W / 2.0)) and p[1] < ((W / 2.0))):
            # Left side
            if p[0] < (0 - (L / 2.0)):
                # Normal pad
                myX1 = p[0] / 2.0
                myY1 = -p[1]
                xD = p[0]
                yD = pinpadsize
                pint = (
                    cq.Workplane("XY")
                    .workplane(centerOption="CenterOfMass", offset=0)
                    .moveTo(myX1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
            else:
                # pad cordinate is inside the body
                myZ1 = pinpadsize / 2.0
                myY1 = -p[1]
                xD = pinpadsize
                yD = pinpadsize
                pint = (
                    cq.Workplane("ZY")
                    .workplane(
                        centerOption="CenterOfMass", offset=(L / 2.0) - (pinpadh / 2.0)
                    )
                    .moveTo(myZ1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )

        #
        elif p[0] >= 0 and (p[1] > (0 - (W / 2.0)) and p[1] < ((W / 2.0))):
            # Right side
            if p[0] > (L / 2.0):
                # Normal pad
                myX1 = p[0] / 2.0
                xD = -p[0]
                yD = pinpadsize
                pint = (
                    cq.Workplane("XY")
                    .workplane(centerOption="CenterOfMass", offset=0)
                    .moveTo(myX1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
            else:
                # pad cordinate is inside the body
                myZ1 = pinpadsize / 2.0
                myY1 = -p[1]
                xD = pinpadsize
                yD = pinpadsize
                pint = (
                    cq.Workplane("ZY")
                    .workplane(
                        centerOption="CenterOfMass",
                        offset=0 - ((L / 2.0) + (pinpadh / 2.0)),
                    )
                    .moveTo(myZ1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
        elif p[1] < 0:
            # top pad
            if p[1] < (W / 2.0):
                myX1 = p[0] - (pinpadsize / 2.0)
                myY1 = 0 - (p[1] / 2.0)
                yD = 0 - p[1]
                xD = pinpadsize
                pint = (
                    cq.Workplane("XY")
                    .workplane(centerOption="CenterOfMass", offset=0)
                    .moveTo(myX1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
            else:
                # pad cordinate is inside the body
                myZ1 = pinpadsize / 2.0
                yD = pinpadsize
                xD = pinpadsize
                myX1 = p[0] - (pinpadsize / 2.0)
                pint = (
                    cq.Workplane("ZX")
                    .workplane(
                        centerOption="CenterOfMass",
                        offset=((W / 2.0) - (pinpadh / 2.0)),
                    )
                    .moveTo(myZ1, myX1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
        else:
            # bottom pad
            if p[1] > (W / 2.0):
                myX1 = p[0] - (pinpadsize / 2.0)
                myY1 = 0 - (p[1] / 2.0)
                yD = 0 - p[1]
                xD = pinpadsize
                pint = (
                    cq.Workplane("XY")
                    .workplane(centerOption="CenterOfMass", offset=0)
                    .moveTo(myX1, myY1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )
            else:
                # pad cordinate is inside the body
                myX1 = p[0] - (pinpadsize / 2.0)
                myZ1 = pinpadsize / 2.0
                yD = pinpadsize
                xD = pinpadsize
                pint = (
                    cq.Workplane("ZX")
                    .workplane(
                        centerOption="CenterOfMass",
                        offset=0 - ((W / 2.0) + (pinpadh / 2.0)),
                    )
                    .moveTo(myZ1, myX1)
                    .rect(xD, yD)
                    .extrude(pinpadh)
                )

        if i == 0:
            pins = pint
        else:
            pins = pins.union(pint)

    if rotation != 0:
        pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

    return pins
