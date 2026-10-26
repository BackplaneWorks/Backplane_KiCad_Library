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

from math import radians, tan

import cadquery as cq


def make_tantalum(params):

    ma_deg = 8

    # Decide whether to use nominal or max values
    param_key = "param_nominal"
    if params["param_nominal"] != None:
        param_key = "param_nominal"
    else:
        param_key = "param_max"

    L = params[param_key]["L"]
    W = params[param_key]["W"]
    H = params[param_key]["H"]
    F = params[param_key]["F"]
    S = params[param_key]["S"]
    B = params[param_key]["B"]
    P = params[param_key]["P"]
    R = params[param_key]["R"]
    T = params[param_key]["T"]
    G = params[param_key]["G"]
    E = params[param_key]["E"]
    pml = params[param_key]["pml"]
    # dest_dir_pref = params.dest_dir_prefix

    Lb = L - 2.0 * T  # body lenght
    ppH = H * 0.45  # pivot point height

    ma_rad = radians(ma_deg)
    dtop = (H - ppH) * tan(ma_rad)
    dbot = (ppH - T) * tan(ma_rad)

    body_base = (
        cq.Workplane(cq.Plane.XY())
        .workplane(centerOption="CenterOfMass", offset=0)
        .rect(E, G)
        .workplane(centerOption="CenterOfMass", offset=T)
        .rect(E, G)
        .loft(ruled=True)
    )

    body = (
        cq.Workplane(cq.Plane.XY())
        .workplane(centerOption="CenterOfMass", offset=T)
        .rect(W - dbot, Lb - dbot)
        .workplane(centerOption="CenterOfMass", offset=ppH - T)
        .rect(W, Lb)
        .workplane(centerOption="CenterOfMass", offset=H - ppH)
        .rect(W - dtop, Lb - dtop)
        .loft(ruled=True)
    )

    if B != 0:
        BS = cq.selectors.BoxSelector
        body = body.edges(
            BS(
                (-(W - 2.0 * dtop) / 2, (Lb - 2.0 * dtop) / 2.0, H - 0.2),
                ((W + 2.0 * dtop) / 2, (Lb + 2.0 * dtop) / 2.0, H + 0.2),
            )
        ).chamfer(B)

    body = body.union(body_base)
    # add pinmark
    pinmark = (
        cq.Workplane(cq.Plane.XY())
        .workplane(centerOption="CenterOfMass", offset=H)
        .rect(W - dtop - dtop, pml)
        .extrude(0.01)
    )

    # translate the object
    pinmark = pinmark.translate(
        (0, Lb / 2.0 - B - pml / 2.0 - dtop / 2.0 - dtop / 2.0, 0)
    ).rotate((0, 0, 0), (0, 1, 0), 0)
    # Create a pin object at the center of top side.
    # threePointArc((L+K/sqrt(2), b/2-K*(1-1/sqrt(2))),
    #              (L+K, b/2-K)). \
    bpin1 = (
        cq.Workplane("XY")
        .moveTo(0, Lb / 2.0 - S)
        .lineTo(0, Lb / 2.0)
        .lineTo(F, Lb / 2.0)
        .lineTo(F, Lb / 2.0 - S)
        .close()
        .extrude(T + 0.01 * T)
    )
    bpin1 = bpin1.translate((-F / 2.0, 0, 0))
    bpin = bpin1.translate((0, -Lb + S, 0))

    delta = 0.01
    hpin = ppH - delta * ppH
    bpin2 = (
        cq.Workplane("XY")
        .moveTo(0, Lb / 2.0)
        .lineTo(0, Lb / 2.0 + T)
        .lineTo(F, Lb / 2.0 + T)
        .lineTo(F, Lb / 2.0)
        .close()
        .extrude(hpin)
    )
    bpin2 = bpin2.translate((-F / 2.0, 0, 0))
    BS = cq.selectors.BoxSelector
    bpin2 = bpin2.edges(
        BS(
            (0 - delta, L / 2.0 - delta, hpin - delta),
            (0 + delta, L / 2.0 + delta, hpin + delta),
        )
    ).fillet(T * 2.0 / 3.0)
    bpin2 = bpin2.edges(
        BS(
            (0 - delta, L / 2.0 - delta, 0 - delta),
            (0 + delta, L / 2.0 + delta, 0 + delta),
        )
    ).fillet(T * 2.0 / 3.0)
    bpinv = bpin2.rotate(
        (
            0,
            0,
        ),
        (0, 0, 1),
        180,
    )  # .translate((0,-T))

    if P != 0:
        anode = (
            cq.Workplane("XY")
            .moveTo(0, Lb / 2.0)
            .lineTo(0, Lb / 2.0 + T)
            .lineTo(R, Lb / 2.0 + T)
            .lineTo(R, Lb / 2.0)
            .close()
            .extrude(hpin - P)
            .translate((-R / 2.0, 0, P))
        )

        bpin2 = bpin2.cut(anode)

    merged_pins = bpin
    merged_pins = merged_pins.union(bpin1)
    merged_pins = merged_pins.union(bpin2)
    merged_pins = merged_pins.union(bpinv)
    pins = merged_pins

    return (body, pins, pinmark)
