# -*- coding: utf-8 -*-
#!/usr/bin/python
#
# This is derived from a cadquery script for generating PDIP models in X3D format
#
# from https://bitbucket.org/hyOzd/freecad-macros
# author hyOzd
# This is a
# Dimensions are from Microchips Packaging Specification document:
# DS00000049BY. Body drawing is the same as QFP generator#

## requirements
## cadquery FreeCAD plugin
##   https://github.com/jmwright/cadquery-freecad-module

## to run the script just do: freecad main_generator.py modelName
## e.g. c:\freecad\bin\freecad main_generator.py DIP8

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


import math

from .cq_parameters import *


class cq_parameters_tube_generic:

    def __init__(self):
        x = 0

    def make_3D_model(self, params):
        # destination_dir = self.get_dest_3D_dir()

        case_top = self.make_case_top(params)
        case = self.make_case(params)
        pins = self.make_pins(params)
        npth_pins = self.make_npth_pins(params)

        return (case_top, case, pins, npth_pins)

    def make_case_top(self, params):

        D = params["D"]  # package length
        E = params["E"]  # body overall width
        H = params["H"]  # body overall height
        A1 = params["A1"]  # package height
        pin_spigot = params["pin_spigot"]  # Spigot pin
        npth_pin = params["npth_pin"]  # NPTH holes
        center_pin = params["center_pin"]  # Center pin
        pin_type = params["pin_type"]  # Pin type
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Pin arc
        pin_diameter = params["pin_diameter"]  # Pin diameter
        rotation = params["rotation"]  # Rotation if required

        #
        # Calculate center
        # pin 1 always in origo
        #
        alpha_delta = 0 - math.radians(pin_arc)
        h = pin_diameter / 2.0
        origo_dx = h * math.sin(alpha_delta)
        origo_dy = h * math.cos(alpha_delta)

        origo_x = 0 - origo_dx
        origo_y = origo_dy

        ff = D / 8.0

        case = (
            cq.Workplane("XY")
            .workplane(offset=A1 + H * 0.90 - (D / 4.0), centerOption="CenterOfMass")
            .moveTo(origo_x, 0 - origo_y)
            .circle(D / 2.0, False)
            .extrude((D / 4.0))
        )
        case = case.faces(">Z").edges(">Y").fillet(D / 4.1)

        case2 = (
            cq.Workplane("XY")
            .workplane(offset=A1 + H * 0.90, centerOption="CenterOfMass")
            .moveTo(origo_x, 0 - origo_y)
            .circle(D / 8.0, False)
            .extrude(A1 + H * 0.10)
        )
        case = case.union(case2)
        case = case.faces(">Z").edges(">Y").fillet(D / 8.1)

        case = case.faces("<Z").shell(0.1)

        if rotation != 0:
            case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

        return case

    def make_case(self, params):

        D = params["D"]  # package length
        E = params["E"]  # body overall width
        H = params["H"]  # body overall height
        A1 = params["A1"]  # package height
        pin_spigot = params["pin_spigot"]  # Spigot pin
        npth_pin = params["npth_pin"]  # NPTH holes
        center_pin = params["center_pin"]  # Center pin
        pin_type = params["pin_type"]  # Pin type
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Pin arc
        pin_diameter = params["pin_diameter"]  # Pin diameter
        rotation = params["rotation"]  # Rotation if required

        #
        # Calculate center
        # pin 1 always in origo
        #
        alpha_delta = 0 - math.radians(pin_arc)
        h = pin_diameter / 2.0
        origo_dx = h * math.sin(alpha_delta)
        origo_dy = h * math.cos(alpha_delta)

        origo_x = 0 - origo_dx
        origo_y = origo_dy

        H1 = H - ((D / 4.0) + H * 0.10)

        ffs = D / 12.0
        case = (
            cq.Workplane("XY")
            .workplane(offset=A1, centerOption="CenterOfMass")
            .moveTo(origo_x, 0 - origo_y)
            .circle(D / 2.0, False)
            .extrude(H1)
        )
        case = case.faces("<Z").edges("<Y").fillet(ffs)

        case = case.faces(">Z").shell(0.1)

        if rotation != 0:
            case = case.rotate((0, 0, 0), (0, 0, 1), rotation)

        return case

    def make_pins(self, params):

        D = params["D"]  # package length
        E = params["E"]  # body overall width
        H = params["H"]  # body overall height
        A1 = params["A1"]  # package height
        pin_spigot = params["pin_spigot"]  # Spigot pin
        npth_pin = params["npth_pin"]  # NPTH holes
        center_pin = params["center_pin"]  # Center pin
        pin_type = params["pin_type"]  # Pin type
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Pin arc
        pin_diameter = params["pin_diameter"]  # Pin diameter
        rotation = params["rotation"]  # Rotation if required

        #
        # Calculate center
        # pin 1 always in origo
        #
        alpha_delta = 0 - math.radians(pin_arc)
        h = pin_diameter / 2.0
        origo_dx = h * math.sin(alpha_delta)
        origo_dy = h * math.cos(alpha_delta)

        origo_x = 0 - origo_dx
        origo_y = origo_dy

        alpha = alpha_delta
        if pin_type[0] == "round":
            x1 = (h * math.sin(alpha)) + origo_x
            y1 = (h * math.cos(alpha)) - origo_y
            pins = (
                cq.Workplane("XY")
                .workplane(offset=A1 + 0.1, centerOption="CenterOfMass")
                .moveTo(x1, y1)
                .circle(pin_type[1] / 2.0, False)
                .extrude(A1 - (0.1 + pin_type[2]))
            )
            pins = pins.faces("<Z").fillet(pin_type[1] / 5.0)
            alpha = alpha + alpha_delta
            for i in range(1, pin_number):
                x1 = (h * math.sin(alpha)) + origo_x
                y1 = (h * math.cos(alpha)) - origo_y
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=A1 + 0.1, centerOption="CenterOfMass")
                    .moveTo(x1, y1)
                    .circle(pin_type[1] / 2.0, False)
                    .extrude(A1 - (0.1 + pin_type[2]))
                )
                pint = pint.faces("<Z").fillet(pin_type[1] / 5.0)
                pins = pins.union(pint)
                alpha = alpha + alpha_delta

        if center_pin != None:
            if center_pin[0] == "metal":
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=A1 + 0.1, centerOption="CenterOfMass")
                    .moveTo(origo_x, 0 - origo_y)
                    .circle(center_pin[1] / 2.0, False)
                    .extrude(A1 - (0.1 + center_pin[2]))
                )
                pint = pint.faces("<Z").fillet(pin_type[1] / 5.0)
                pins = pins.union(pint)

        if rotation != 0:
            pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

        return pins

    def make_npth_pins(self, params):

        D = params["D"]  # package length
        E = params["E"]  # body overall width
        H = params["H"]  # body overall height
        A1 = params["A1"]  # package height
        pin_spigot = params["pin_spigot"]  # Spigot pin
        npth_pin = params["npth_pin"]  # NPTH holes
        center_pin = params["center_pin"]  # Center pin
        pin_type = params["pin_type"]  # Pin type
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Pin arc
        pin_diameter = params["pin_diameter"]  # Pin diameter
        rotation = params["rotation"]  # Rotation if required

        #
        # Calculate center
        # pin 1 always in origo
        #
        alpha_delta = 0 - math.radians(pin_arc)
        h = pin_diameter / 2.0
        origo_dx = h * math.sin(alpha_delta)
        origo_dy = h * math.cos(alpha_delta)

        origo_x = 0 - origo_dx
        origo_y = origo_dy

        pins = (
            cq.Workplane("XY")
            .workplane(offset=A1 - 0.5, centerOption="CenterOfMass")
            .moveTo(origo_x, 0 - origo_y)
            .circle((D / 2.0) - 0.5, False)
            .extrude(A1 + 2.0)
        )

        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + 0.5, centerOption="CenterOfMass")
            .moveTo((origo_x - (D / 2.0)) + 3.0, 0 - origo_y)
            .circle(0.5, False)
            .extrude((2.0 * H) / 3.0)
        )
        pint = pint.faces(">Z").fillet(0.4)
        pins = pins.union(pint)
        #
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + 0.5, centerOption="CenterOfMass")
            .moveTo((origo_x + (D / 2.0)) - 3.0, 0 - origo_y)
            .circle(0.5, False)
            .extrude((2.0 * H) / 3.0)
        )
        pint = pint.faces(">Z").fillet(0.4)
        pins = pins.union(pint)
        #
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + 0.5, centerOption="CenterOfMass")
            .moveTo(origo_x - 1.0, 0 - origo_y)
            .circle(0.5, False)
            .extrude((2.0 * H) / 3.0)
        )
        pint = pint.faces(">Z").fillet(0.4)
        pins = pins.union(pint)
        #
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + 0.5, centerOption="CenterOfMass")
            .moveTo(origo_x + 1.0, 0 - origo_y)
            .circle(0.5, False)
            .extrude((2.0 * H) / 3.0)
        )
        pint = pint.faces(">Z").fillet(0.4)
        pins = pins.union(pint)
        #
        pint = (
            cq.Workplane("XY")
            .workplane(offset=A1 + (H / 6.0), centerOption="CenterOfMass")
            .moveTo(origo_x, 0 - origo_y)
            .rect(D * 0.8, D / 4.0)
            .extrude(H / 3.0)
        )
        pint = pint.faces(">Z").fillet(D / 20.0)
        pint = pint.faces("<Z").fillet(D / 20.0)
        pins = pins.union(pint)

        if npth_pin != None:
            if npth_pin[0] == "metal":
                pint = (
                    cq.Workplane("XY")
                    .workplane(offset=A1 + 0.1, centerOption="CenterOfMass")
                    .moveTo(origo_x, 0 - origo_y)
                    .circle(npth_pin[1] / 2.0, False)
                    .extrude(0 - (H + 0.1 + pin_type[2]))
                )
                pins = pins.union(pint)

        if rotation != 0:
            pins = pins.rotate((0, 0, 0), (0, 0, 1), rotation)

        return pins
