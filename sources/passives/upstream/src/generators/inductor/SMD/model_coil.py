#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# * These are cadquery tools to export                                       *
# * generated models in STEP & VRML format.                                  *
# *                                                                          *
# * cadquery script for generating coil models in STEP AP214                 *
# * Copyright (c) 2024 KiCad Library Team                                    *
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

import numpy as np

from .spec import HorizontalAirCoreParameters


class DSectionFoot:
    r"""
    This produces a "d-section" coil foot with a circular top connection land
    for a wire.

    End aspect: (o is origin)

     ____---------____  -------------------
    /                 \                  ^
    +-----------------+  ---         overall height
    |                 |   square H       v
    +--------o--------+  ----------------------------- Z = 0
    |<------ W ------>|


    Top aspect:


    |<------- L -------->|
    +-----------------+       ^ Y
    |               /   \     |
    |         o    |     |    +---> X
    |               \   /
    +-----------------+
    """

    def __init__(
        self, length_x: float, sq_height: float, overall_height: float, width_y: float
    ):
        self.length_x = length_x
        self.sq_height = sq_height
        self.overall_height = overall_height
        self.width_y = width_y

    def make(self):

        # Create the foot prism extrustion
        extrude_x = self.length_x - self.width_y / 2

        # This is the D-shaped cross section
        end_cross_section = (
            cq.Workplane("YZ")
            .workplane(offset=-self.length_x / 2)  # Start from the "toe"
            .moveTo(-self.width_y / 2, 0)
            # Top left corner of the rectangular base
            .lineTo(-self.width_y / 2, self.sq_height)
            .threePointArc(
                # Top of the foot
                (0, self.overall_height),
                # Top right corner of the rectangular base
                (self.width_y / 2, self.sq_height),
            )
            .lineTo(self.width_y / 2, 0)
            .close()
        )

        extrude = end_cross_section.extrude(extrude_x, both=False)

        # Create the circular upright cylinder
        circle_radius = self.width_y / 2
        circle_offset_x = (self.length_x / 2) - circle_radius

        cylinder = (
            cq.Workplane("XY")
            .circle(circle_radius)
            .extrude(self.overall_height)
            .translate((circle_offset_x, 0, 0))
        )

        return extrude.union(cylinder)


def _coil_spline_points(diameter, length, wire_size, num_turns):
    coil_radius = diameter / 2.0  # calculate the radius of the coil
    points = []

    # define the number of points for a turn
    num_points = 60

    # total number of points in the coil
    total_points = int(num_turns) * num_points
    x = 0
    for i in range(total_points):
        # calculate the angle for each point based on the total number of points
        angle = (i / num_points) * 2 * np.pi  # full circle
        x = x + wire_size / num_points  # +0.001 # incremental x based on wire size

        # calculate y and z based on the angle
        y = coil_radius + coil_radius * np.cos(angle)  # y position
        z = coil_radius * np.sin(angle)  # z position

        # append the point to the list
        points.append((x, y, z))
        # exit half a turn to meet the pin
        if i == total_points - num_points / 2.0:
            break

    return points


def make_coil(wire_size: float, part_length: float, coil_diameter: float):
    """
    Make a coil with a given wire size, length, and diameter.

    The coil will be centred at the origin and will be oriented along the X axis.

    The coil has zero spacing between turns.

    The connection points are the centres of two circles that form the bottoms
    of the coil ends.
    """
    coilLength = part_length
    coilTurns, coilTurnsRem = divmod(coilLength, wire_size)
    pts = _coil_spline_points(coil_diameter, coilLength, wire_size, coilTurns)

    spline_path = cq.Workplane("XY").spline(pts, makeWire=True)
    coil = (
        cq.Workplane("XY")
        .circle(wire_size / 2.0)
        .sweep(spline_path, isFrenet=True)
        .translate(
            (
                (-(coilTurns - 1.5) * wire_size) / 2.0,
                -coil_diameter / 2.0,
                0,
            )
        )
    )
    pin_connections = [
        (-(coilTurns - 0.5) * wire_size / 2, (coil_diameter) / 2, 0),
        ((coilTurns - 0.5) * wire_size / 2, -(coil_diameter) / 2, 0),
    ]

    return coil, pin_connections


def _make_connector(wire_size: float, base, tip):
    """
    Make a circular cross-section (circular in planes parallel to XY) "connector"
    between two points.
    """
    pts = [base, tip]
    spline_path = cq.Workplane("XY").spline(pts, makeWire=True)
    conn = (
        cq.Workplane("XY")
        .circle(wire_size / 2.0)
        .sweep(spline_path, isFrenet=True)
        .translate(tip)
    )
    return conn


class DSectionFootAirCoreCoil:

    def __init__(self, body_params: HorizontalAirCoreParameters):
        self.body_params = body_params

        self.coilLength = self.body_params.width_x - self.body_params.wire_size * 0.75
        self.coilTurns, self.coilTurnsRem = divmod(
            self.coilLength, self.body_params.wire_size
        )

    def make_coil(self):
        """
        Returns the coil and union of the pins.
        """

        # Centre-to-centre distance between the pins
        pinX = self.body_params.device_pad_dims.spacing_centre / 2

        foot_len = self.body_params.device_pad_dims.size_crosswise
        foot_height = self.body_params.wire_size

        # Create the pins
        dfoot = DSectionFoot(
            length_x=foot_len,
            sq_height=self.body_params.wire_size * 0.75,
            overall_height=foot_height,
            width_y=self.body_params.wire_size,
        )

        # Rotate the feet to be aligned to Y
        pin = dfoot.make().rotate((0, 0, 0), (0, 0, 1), 90)

        pin1 = pin.translate((-pinX, 0, 0))

        # Centre-line diameter of the coil
        coil_dia = self.body_params.length_y - self.body_params.wire_size

        coil, coil_connection_points = make_coil(
            coil_diameter=coil_dia,
            wire_size=self.body_params.wire_size,
            part_length=self.coilLength,
        )

        # Shift the coil to sit on the surface
        surface_coil_z_gap = max(0, self.body_params.height - self.body_params.length_y)
        coil_offset_z = (
            coil_dia / 2.0 + self.body_params.wire_size / 2.0 + surface_coil_z_gap
        )

        coil = coil.translate((0, 0, coil_offset_z))

        # Translate the coil's connection point in the same was as the coil
        coil_end_point = (
            coil_connection_points[1][0],
            coil_connection_points[1][1],
            coil_connection_points[1][2] + coil_offset_z + 0.001,
        )

        # Figure out the pin foot connection point
        conn_pt = (
            pinX,
            -foot_len / 2 + self.body_params.wire_size / 2,
            foot_height,
        )

        # Create the connector between the coil and the pin
        pin_coil_joiner = _make_connector(
            self.body_params.wire_size,
            coil_end_point,
            conn_pt,
        )

        pin1 = pin1.union(pin_coil_joiner)

        # Pin 2 is just pin 1 spun around the Z axis by 180 degrees
        pin2 = pin1.rotate((0, 0, 0), (0, 0, 1), 180)

        pins = pin1.union(pin2)

        return coil, pins
