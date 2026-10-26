# kilibs is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# kilibs is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with kilibs.
# If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

from math import sqrt

from kilibs.geom import (
    GeomArc,
    GeomCircle,
    GeomCompoundPolygon,
    GeomCross,
    GeomCruciform,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomRoundRectangle,
    GeomShapeClosed,
    GeomShapeOpen,
    GeomStadium,
    GeomTrapezoid,
    Vec2DCompatible,
    Vector2D,
)

CENTER = (0, 0)
POINTS: list[Vec2DCompatible] = [
    Vector2D(-1, -1),
    (1, -1),
    [1, 1],
    (-1, 1),
]  # different types on purpose
# When adding shapes to the `TEST_SHAPE*` the rule is that:
#   (0, 0) is inside the shape (for closed shapes only),
#   (1, 1) and (-1, -1) are on the outline of the shape,
# Adapt also the implementation of the following tests:
#   `test_geom_shape.test_bbox()`
#   `test_geom_shape.test_constructor()`
TEST_SHAPE_ARC = GeomArc(center=CENTER, start=POINTS[0], angle=-180)
TEST_SHAPE_LINE = GeomLine(start=POINTS[0], end=POINTS[2])
TEST_SHAPE_CROSS = GeomCross(center=(0, 0), size=(2*sqrt(2), 2*sqrt(2)), angle=45)  # fmt: skip  # NOQA

TEST_SHAPES_OPEN: list[GeomShapeOpen] = [
    TEST_SHAPE_ARC,
    TEST_SHAPE_LINE,
    TEST_SHAPE_CROSS,
]

TEST_SHAPE_CIRCLE = GeomCircle(center=CENTER, radius=sqrt(2))
TEST_SHAPE_RECTANGLE = GeomRectangle(center=CENTER, size=[2, 2])
TEST_SHAPE_POLYGON = GeomPolygon(shape=POINTS)
TEST_SHAPE_COMPOUND_POLYGON = GeomCompoundPolygon(shape=[GeomPolygon(shape=POINTS)])
TEST_SHAPE_STADIUM = GeomStadium(center_1=(-1, 0), center_2=(+1, 0), radius=1)
TEST_SHAPE_CRUCIFORM = GeomCruciform(overall_h=4, overall_w=4, tail_h=2, tail_w=2, center=(0, 0))  # fmt: skip  # NOQA
TEST_SHAPE_ROUND_RECTANGLE = GeomRoundRectangle(center=(0, 0), size=(3-sqrt(2)/2, 3-sqrt(2)/2), corner_radius=0.5)  # fmt: skip  # NOQA
TEST_SHAPE_TRAPEZOID = GeomTrapezoid(center=(0, 0), size=(6, 2), corner_radius=0, side_angle=45)  # fmt: skip  # NOQA

TEST_SHAPES_CLOSED: list[GeomShapeClosed] = [
    TEST_SHAPE_CIRCLE,
    TEST_SHAPE_RECTANGLE,
    TEST_SHAPE_POLYGON,
    TEST_SHAPE_COMPOUND_POLYGON,
    TEST_SHAPE_STADIUM,
    TEST_SHAPE_CRUCIFORM,
    TEST_SHAPE_ROUND_RECTANGLE,
    TEST_SHAPE_TRAPEZOID,
]

TEST_SHAPES = TEST_SHAPES_OPEN + TEST_SHAPES_CLOSED
