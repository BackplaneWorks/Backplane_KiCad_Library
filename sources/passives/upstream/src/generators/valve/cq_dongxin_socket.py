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
from collections import namedtuple
from collections.abc import Mapping

from .cq_parameters import *


class cq_dongxin_socket:

    def __init__(self):
        x = 0

    def make_3D_model(self, params):

        if params["serie"] == "GZC8-Y-5":
            case_top = self.make_case_top_GZC8_Y_5(params)
        else:
            case_top = self.make_case_top_dummy(params)

        if (
            params["serie"] == "GZC9-A"
            or params["serie"] == "GZS9-Y"
            or params["serie"] == "GZC7-Y-B"
        ):
            case = self.make_case_top_straight_round(params)

        if (
            params["serie"] == "GZC9-B"
            or params["serie"] == "GZC9-Y-2"
            or params["serie"] == "GZC8-Y"
            or params["serie"] == "GZC8-Y-2"
        ):
            case = self.make_case_body_with_ring(params)

        if params["serie"] == "GZC8-Y-5":
            case = self.make_case_top_straight_round(params)

        pins = self.make_pins(params)

        npth_pins = self.make_npth_pins(params)

        return (case_top, case, pins, npth_pins)

    def make_case_top_dummy(self, params):

        return None  # return None when there is no case top

    def make_case_top_GZC8_Y_5(self, params):

        D = params["D"]  # package length
        H = params["socket_H"]  # body overall height
        A1 = params["A1"]  # package height
        pin_top_diameter = params["pin_top_diameter"]  # Diameter of pin hole on top
        pin_spigot = params["pin_spigot"]  # Spigot
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

        cq_par = cq_parameters_help()
        top = cq_par.create_sadle(origo_x, origo_y, A1, D, sadle, sadle_hole, rotation)

        return top

    def make_case_top_straight_round(self, params):

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

    def make_case_body_with_ring(self, params):

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

        case = cq_par.make_body_with_ring_cricle(
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

    def make_pins(self, params):

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
