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

import pytest

from kilibs.geom import (
    GeomArc,
    GeomCircle,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomShape,
)
from kilibs.geom.operations import split
from kilibs.geom.tolerances import TOL_MM
from tests.kilibs.geom.geom_test_shapes import (
    TEST_SHAPE_ARC,
    TEST_SHAPE_CIRCLE,
    TEST_SHAPE_COMPOUND_POLYGON,
    TEST_SHAPE_CROSS,
    TEST_SHAPE_CRUCIFORM,
    TEST_SHAPE_LINE,
    TEST_SHAPE_POLYGON,
    TEST_SHAPE_RECTANGLE,
    TEST_SHAPE_ROUND_RECTANGLE,
    TEST_SHAPE_STADIUM,
    TEST_SHAPE_TRAPEZOID,
)
from tests.kilibs.geom.is_equal import are_equal


def check_segments(
    cuts: list[GeomShape],
    expected_number: int,
    shape_to_cut: GeomShape,
    rel: float = TOL_MM,
) -> None:
    circumference = 0
    expected_circumference = 0
    assert len(cuts) == expected_number
    if len(cuts) > 1:
        for segment in shape_to_cut.get_atomic_shapes():
            expected_circumference += segment.length
        for segment in cuts:
            assert isinstance(segment, GeomArc) or isinstance(segment, GeomLine)
            assert shape_to_cut.is_point_on_self(segment.mid)
            circumference += segment.length
        assert abs(circumference - expected_circumference) <= rel
    else:
        if type(cuts[0]) is type(shape_to_cut):
            assert are_equal(cuts, [shape_to_cut], rel=rel)
        else:
            # It could be that a circle is cut exactly once and thus is an arc of 360°:
            if isinstance(cuts[0], GeomArc) and isinstance(shape_to_cut, GeomCircle):
                assert abs(cuts[0].length - shape_to_cut.length) <= rel


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_number_of_shapes",
    [
        (TEST_SHAPE_ARC,                2),
        (TEST_SHAPE_LINE,               2),
        (TEST_SHAPE_CROSS,              4),
        (TEST_SHAPE_CIRCLE,             2),
        (TEST_SHAPE_RECTANGLE,          6),
        (TEST_SHAPE_POLYGON,            6),
        (TEST_SHAPE_COMPOUND_POLYGON,   6),
        (TEST_SHAPE_STADIUM,            6),
        (TEST_SHAPE_CRUCIFORM,          14),
        (TEST_SHAPE_ROUND_RECTANGLE,    10),
        (TEST_SHAPE_TRAPEZOID,          6),
    ],
)
# fmt: on
def test_line_cuts(
    shape: GeomShape, expected_number_of_shapes: int, rel: float = TOL_MM
) -> None:
    # Cutting with a vertical line along the y-axis:
    cutting_line = GeomLine(start=(0, -100), end=(0, +100))
    cuts = split(shape_to_split=shape, splitting_shape=cutting_line, tol=rel)
    check_segments(cuts, expected_number_of_shapes, shape)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_number_of_shapes",
    [
        (TEST_SHAPE_ARC,                2),
        (TEST_SHAPE_LINE,               1),
        (TEST_SHAPE_CROSS,              1),
        (TEST_SHAPE_CIRCLE,             1),
        (TEST_SHAPE_RECTANGLE,          4),
        (TEST_SHAPE_POLYGON,            4),
        (TEST_SHAPE_COMPOUND_POLYGON,   4),
        (TEST_SHAPE_STADIUM,            5),
        (TEST_SHAPE_CRUCIFORM,          13),
        (TEST_SHAPE_ROUND_RECTANGLE,    9),
        (TEST_SHAPE_TRAPEZOID,          5),
    ],
)
# fmt: on
def test_arc_cuts(
    shape: GeomShape, expected_number_of_shapes: int, rel: float = TOL_MM
) -> None:
    # Cutting with an arc of 180° whose center coincides with the center-left point of
    # the shape's bounding box and intersects the origin:
    left = shape.bbox().left
    cutting_arc = GeomArc(center=(left, 0), start=(0, 0), angle=180)
    cuts = split(shape_to_split=shape, splitting_shape=cutting_arc, tol=rel)
    check_segments(cuts, expected_number_of_shapes, shape)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_number_of_shapes",
    [
        (TEST_SHAPE_ARC,                1),
        (TEST_SHAPE_LINE,               3),
        (TEST_SHAPE_CROSS,              6),
        (TEST_SHAPE_CIRCLE,             1),
        (TEST_SHAPE_RECTANGLE,          12),
        (TEST_SHAPE_POLYGON,            12),
        (TEST_SHAPE_COMPOUND_POLYGON,   12),
        (TEST_SHAPE_STADIUM,            8),
        (TEST_SHAPE_CRUCIFORM,          1),
        (TEST_SHAPE_ROUND_RECTANGLE,    16),
        (TEST_SHAPE_TRAPEZOID,          8),
    ],
)
# fmt: on
def test_circle_cuts(
    shape: GeomShape, expected_number_of_shapes: int, rel: float = TOL_MM
) -> None:
    # Cutting with a centered circle of radius of (1+sqrt(2))/2:
    cutting_circle = GeomCircle(center=(0, 0), radius=(1 + sqrt(2)) / 2)
    cuts = split(shape_to_split=shape, splitting_shape=cutting_circle, tol=rel)
    check_segments(cuts, expected_number_of_shapes, shape)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_number_of_shapes",
    [
        (TEST_SHAPE_ARC,                1),
        (TEST_SHAPE_LINE,               3),
        (TEST_SHAPE_CROSS,              6),
        (TEST_SHAPE_CIRCLE,             1),
        (TEST_SHAPE_RECTANGLE,          12),
        (TEST_SHAPE_POLYGON,            12),
        (TEST_SHAPE_COMPOUND_POLYGON,   12),
        (TEST_SHAPE_STADIUM,            8),
        (TEST_SHAPE_CRUCIFORM,          1),
        (TEST_SHAPE_ROUND_RECTANGLE,    16),
        (TEST_SHAPE_TRAPEZOID,          8),
    ],
)
# fmt: on
def test_rotated_rectangle_cuts(
    shape: GeomShape, expected_number_of_shapes: int, rel: float = TOL_MM
) -> None:
    # Cutting with a unit rectangle rotated by 45 degrees:
    cutting_rect = GeomRectangle(start=[-1, -1], end=[1, 1], angle=45)
    cuts = split(shape_to_split=shape, splitting_shape=cutting_rect, tol=rel)
    check_segments(cuts, expected_number_of_shapes, shape)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_number_of_shapes",
    [
        (TEST_SHAPE_ARC,                5),
        (TEST_SHAPE_LINE,               1),
        (TEST_SHAPE_CROSS,              1),
        (TEST_SHAPE_CIRCLE,             8),
        (TEST_SHAPE_RECTANGLE,          12),
        (TEST_SHAPE_POLYGON,            12),
        (TEST_SHAPE_COMPOUND_POLYGON,   12),
        (TEST_SHAPE_STADIUM,            12),
        (TEST_SHAPE_CRUCIFORM,          20),
        (TEST_SHAPE_ROUND_RECTANGLE,    16),
        (TEST_SHAPE_TRAPEZOID,          12),
    ],
)
# fmt: on
def test_concave_polygon_cuts(
    shape: GeomShape, expected_number_of_shapes: int, rel: float = TOL_MM
) -> None:
    # Cutting with a centered star-like polygon with circumradius of 2:
    pts: list[list[float]] = [
        [-1, -1],
        [0, -0.5],
        [1, -1],
        [0.5, 0],
        [1, 1],
        [0, 0.5],
        [-1, 1],
        [-0.5, 0],
    ]
    pts2: list[list[float]] = []
    for pt in pts:
        pts2.append([sqrt(2) * pt[0], sqrt(2) * pt[1]])
    cutting_poly = GeomPolygon(shape=pts2)
    cuts = split(shape_to_split=shape, splitting_shape=cutting_poly, tol=rel)
    print(len(cuts))
    check_segments(cuts, expected_number_of_shapes, shape)
