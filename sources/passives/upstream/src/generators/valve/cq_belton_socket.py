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

import cadquery as cq

from .cq_parameters import *


class cq_belton_socket:

    def __init__(self):
        x = 0

    def make_3D_model(self, params):

        if params["serie"] == "VT8-PT":
            case_top = self.make_case_top_VT8_PT(params)
            case = self.make_case_VT8_PT(params)
            pins = self.make_pins_VT8_PT(params)

        if params["serie"] == "VT9-PT":
            case_top = self.make_case_top(params)
            case = self.make_case_VT9_PT(params)
            pins = self.make_pins_VT9_PT(params)

        if params["serie"] == "VT9-PT-C":
            case_top = self.make_case_top_VT9_PT_C(params)
            case = self.make_case_VT9_PT(params)
            pins = self.make_pins_VT9_PT(params)

        npth_pins = self.make_npth_pins(params)

        return (case_top, case, pins, npth_pins)

    def make_case_top(self, params):

        return None  # this part has no case top by default

    def make_case_top_VT8_PT(self, params):
        D = params["D"]  # package length
        H = params["socket_H"]  # body overall height
        A1 = params["A1"]  # package height
        sadle = params[
            "sadle"
        ]  # "npth hole 1 x-pos, y-pos, diameter", "npth hole 2 x-pos, y-pos, diameter", width, length of flange, rotation in degree of flange
        sadle_hole = params[
            "sadle_hole"
        ]  # sadle hole1 x pos, sadle hole1 diameter, sadle hole2 x pos, sadle hole2 diameter
        sadle_shield = params["sadle_shield"]  #
        npth_pin = params["npth_pin"]  # NPTH hole [(x, y, length)]
        center_pin = params["center_pin"]  # center pin ['type', diameter length)]
        pin_type = params["pin_type"]  # Pin type, length
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Arch between pins
        pin_diameter = params[
            "pin_diameter"
        ]  # Diameter of the cricle where pins are located
        rotation = params["rotation"]  # Rotation if required

        if len(pin_type) > 2:
            A1 = A1 + pin_type[3]
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
        #
        cq_par = cq_parameters_help()
        top = cq_par.create_sadle(origo_x, origo_y, A1, D, sadle, sadle_hole, rotation)
        #

        return top

    def make_case_top_VT9_PT_C(self, params):
        D = params["D"]  # package length
        H = params["socket_H"]  # body overall height
        A1 = params["A1"]  # package height
        sadle = params[
            "sadle"
        ]  # "npth hole 1 x-pos, y-pos, diameter", "npth hole 2 x-pos, y-pos, diameter", width, length of flange, rotation in degree of flange
        sadle_hole = params[
            "sadle_hole"
        ]  # sadle hole1 x pos, sadle hole1 diameter, sadle hole2 x pos, sadle hole2 diameter
        sadle_shield = params["sadle_shield"]  #
        npth_pin = params["npth_pin"]  # NPTH hole [(x, y, length)]
        center_pin = params["center_pin"]  # center pin ['type', diameter length)]
        pin_type = params["pin_type"]  # Pin type, length
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Arch between pins
        pin_diameter = params[
            "pin_diameter"
        ]  # Diameter of the cricle where pins are located
        rotation = params["rotation"]  # Rotation if required

        if len(pin_type) > 2:
            A1 = A1 + pin_type[3]
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
        #
        cq_par = cq_parameters_help()
        case = cq_par.create_sadle(origo_x, origo_y, A1, D, sadle, sadle_hole, rotation)
        case1 = cq_par.create_sadle_shield(
            origo_x, origo_y, A1, sadle, sadle_hole, sadle_shield, rotation
        )
        case = case.union(case1)
        #
        sadle_z = sadle[0]
        sadle_w = sadle[1]
        sadle_r1 = sadle[2] / 2.0
        sadle_x = sadle[3]
        sadle_r2 = sadle[4] / 2.0
        sadle_a = sadle[5]
        sadle_h = 0.2
        #
        case1 = (
            cq.Workplane("XY")
            .workplane(offset=A1 + sadle_z - 6.6, centerOption="CenterOfMass")
            .moveTo(sadle_x, 0)
            .circle(1.5, False)
            .extrude(6.6)
        )
        case1 = case1.rotate((0, 0, 0), (0, 0, 1), sadle_a)
        case1 = case1.translate((origo_x, 0.0 - origo_y, 0.0))
        case = case.union(case1)

        case1 = (
            cq.Workplane("XY")
            .workplane(offset=A1 + sadle_z - 6.6, centerOption="CenterOfMass")
            .moveTo(sadle_x, 0)
            .circle(0.5, False)
            .extrude(-3.0)
        )
        case1 = case1.rotate((0, 0, 0), (0, 0, 1), sadle_a)
        case1 = case1.translate((origo_x, 0.0 - origo_y, 0.0))
        case = case.union(case1)

        return case

    def make_case_VT8_PT(self, params):
        D = params["D"]  # package length
        H = params["socket_H"]  # body overall height
        A1 = params["A1"]  # package height
        pin_top_diameter = params["pin_top_diameter"]  # Diameter of pin hole on top
        pin_spigot = params["pin_spigot"]  # Spigot
        npth_pin = params["npth_pin"]  # NPTH hole [(x, y, length)]
        center_pin = params["center_pin"]  # center pin ['type', diameter length)]
        pin_type = params["pin_type"]  # Pin type, length
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Arch between pins
        pin_diameter = params[
            "pin_diameter"
        ]  # Diameter of the cricle where pins are located
        rotation = params["rotation"]  # Rotation if required

        if len(pin_type) > 2:
            A1 = A1 + pin_type[3]
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

        cq_par = cq_parameters_help()
        case = cq_par.make_body_round(
            origo_x,
            origo_y,
            A1,
            D,
            pin_number,
            pin_type,
            pin_spigot,
            pin_top_diameter,
            H,
            alpha_delta,
            rotation,
        )

        return case

    def make_case_VT9_PT(self, params):
        D = params["D"]  # package length
        H = params["socket_H"]  # body overall height
        A1 = params["A1"]  # package height
        pin_top_diameter = params["pin_top_diameter"]  # Diameter of pin hole on top
        pin_spigot = params["pin_spigot"]  # Spigot
        npth_pin = params["npth_pin"]  # NPTH hole [(x, y, length)]
        center_pin = params["center_pin"]  # center pin ['type', diameter length)]
        pin_type = params["pin_type"]  # Pin type, length
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Arch between pins
        pin_diameter = params[
            "pin_diameter"
        ]  # Diameter of the cricle where pins are located
        rotation = params["rotation"]  # Rotation if required

        if len(pin_type) > 2:
            A1 = A1 + pin_type[3]
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

        cq_par = cq_parameters_help()
        case = cq_par.make_body_with_ring_with_cut(
            origo_x,
            origo_y,
            A1,
            D,
            pin_number,
            pin_type,
            pin_spigot,
            pin_top_diameter,
            H,
            alpha_delta,
            rotation,
        )

        return case

    def make_pins_VT8_PT(self, params):
        D = params["D"]  # package length
        H = params["socket_H"]  # body overall height
        A1 = params["A1"]  # package height
        npth_pin = params["npth_pin"]  # NPTH hole [(x, y, length)]
        center_pin = params["center_pin"]  # center pin ['type', diameter length)]
        pin_type = params["pin_type"]  # Pin type, length
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Arch between pins
        pin_diameter = params[
            "pin_diameter"
        ]  # Diameter of the cricle where pins are located
        rotation = params["rotation"]  # Rotation if required

        if len(pin_type) > 2:
            A1 = A1 + pin_type[3]
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

        cq_par = cq_parameters_help()
        pins = cq_par.create_pins(
            origo_x,
            origo_y,
            A1,
            pin_number,
            pin_type,
            center_pin,
            h,
            alpha_delta,
            rotation,
        )

        return pins

    def make_pins_VT9_PT(self, params):
        D = params["D"]  # package length
        H = params["socket_H"]  # body overall height
        A1 = params["A1"]  # package height
        npth_pin = params["npth_pin"]  # NPTH hole [(x, y, length)]
        center_pin = params["center_pin"]  # center pin ['type', diameter length)]
        pin_type = params["pin_type"]  # Pin type, length
        pin_number = params["pin_number"]  # Number of pins
        pin_arc = params["pin_arc"]  # Arch between pins
        pin_diameter = params[
            "pin_diameter"
        ]  # Diameter of the cricle where pins are located
        rotation = params["rotation"]  # Rotation if required

        if len(pin_type) > 2:
            A1 = A1 + pin_type[3]
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

        cq_par = cq_parameters_help()
        pins = cq_par.create_pins(
            origo_x,
            origo_y,
            A1,
            pin_number,
            pin_type,
            center_pin,
            h,
            alpha_delta,
            rotation,
        )

        return pins

    def make_npth_pins(self, params):

        return None  # this part has no NPTH pins
