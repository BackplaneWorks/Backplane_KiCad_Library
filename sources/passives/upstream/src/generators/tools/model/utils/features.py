#!/usr/bin/env python3

# CadQuery helper functions for adding general details to a shape
#
# Copyright (C) 2025 Martin Sotirov <martin@libtec.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import cadquery as cq


def _make_shape_feature(feature):
    shape_type = feature[1]
    pos = feature[2]

    if shape_type == "box":
        dim = feature[3]
        extra = feature[4:]
        shape = cq.Workplane("XY", origin=pos)
        shape = shape.box(*dim)
    elif shape_type == "cylinder":
        plane = feature[3]
        h = feature[4]
        r = feature[5] / 2
        extra = feature[6:]
        shape = cq.Workplane(plane, origin=pos)
        shape = shape.cylinder(h, r)
    elif shape_type == "poly":
        plane = feature[3]
        depth = feature[4]
        coords = feature[5].copy()
        extra = feature[6:]
        shape = cq.Workplane(plane, origin=pos)
        x = coords.pop(0)
        y = coords.pop(0)
        shape = shape.moveTo(x, y)
        while coords:
            x = coords.pop(0)
            y = coords.pop(0)
            shape = shape.lineTo(x, y)
        shape = shape.close()
        shape = shape.extrude(depth / 2, both=True)
    else:
        raise ValueError(
            f"{namespace}[{feature_index}]: Unrecognized feature shape type: {shape_type}"
        )

    while extra:
        extra_name = extra.pop(0)
        if extra_name == "chamfer":
            edges, chamfer = extra.pop(0)
            shape = shape.edges(edges).chamfer(chamfer)
        elif extra_name == "fillet":
            edges, fillet = extra.pop(0)
            shape = shape.edges(edges).fillet(fillet)
        else:
            raise ValueError(
                f"{namespace}[{feature_index}]: Unrecognized extra parameter: {extra_name}"
            )

    return shape


def make_features(body, features, namespace):
    """Make a feature.

    Feature types:

    : [add, SHAPE ...] -- adds a shape
    : [cut, SHAPE ...] -- cuts a shape
    : [chamfer, EDGES, CHAMFER_SIZE] -- adds a chamfer to specified EDGES
    : [fillet, EDGES, FILLET_SIZE]   -- adds a fillet to specified EDGES

    Features 'add' and 'cut' can use several shapes, each having their
    own unique arguments:

    : [add/cut, box,      [X, Y, Z], [WIDTH, LENGTH, HEIGHT]]
    : [add/cut, cylinder, [X, Y, Z], WORKPLANE, DEPTH, DIAMETER]
    : [add/cut, poly,     [X, Y, Z], WORKPLANE, DEPTH, [COORD_X, COORD_Y, ...]]

    Features 'add' and 'cut' can also have optional arguments:

    : [add/cut, SHAPE ... , chamfer, [EDGES, CHAMFER_SIZE]]
    : [add/cut, SHAPE ... , fillet,  [EDGES, FILLET_SIZE]]

    == Example: Adding a cylinder ==

    : [add, cylinder, [0, 0, 1.5], XY, 3.0, 2.5, fillet, [">Z", 0.2]]

    This adds a cylindrical shape and has the following specs:

    - Its center is positioned 1.5 mm on the Z axis
    - Is orientated on the XY workplane
    - Has depth/height 3.0 mm and diameter 2.5 mm
    - Has a 0.2 mm fillet on the top

    == Example: Adding a chamfer ==

    : [chamfer, "|Z and >X and >Y", 0.1]

    This adds a chamfer to one of the vertical corners.
    """
    for feature_index, feature in enumerate(features):
        feature_type = feature[0]

        if feature_type == "add":
            shape = _make_shape_feature(feature)
            body = body.union(shape)
        elif feature_type == "cut":
            shape = _make_shape_feature(feature)
            body = body.cut(shape)
        elif feature_type == "chamfer":
            chamfer_edges = feature[1]
            chamfer_size = feature[2]
            body = body.edges(chamfer_edges).chamfer(chamfer_size)
        elif feature_type == "fillet":
            fillet_edges = feature[1]
            fillet_size = feature[2]
            body = body.edges(fillet_edges).fillet(fillet_size)
        else:
            raise ValueError(
                f"{namespace}[{feature_index}]: Unrecognized feature: {feature_type}"
            )

    return body
