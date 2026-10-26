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
    TOL_MM,
    GeomArc,
    GeomCircle,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomShape,
    Vector2D,
)
from kilibs.geom.operations.intersection_points import get_intersection_points
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
    TEST_SHAPES,
    TEST_SHAPES_CLOSED,
)
from tests.kilibs.geom.is_equal import are_equal


@pytest.mark.parametrize("shape", TEST_SHAPES)
@pytest.mark.parametrize("strict_intersection", [True, False])
def test_intersect_shape_fully_inside(
    shape: GeomShape, strict_intersection: bool, rel: float = TOL_MM
) -> None:
    inflate_amount = (shape.bbox().size / 2).norm()
    for other_shape in TEST_SHAPES_CLOSED:
        inflated_shape = other_shape.inflated(amount=inflate_amount, tol=rel)
        intersections = get_intersection_points(
            shape1=inflated_shape,
            shape2=shape,
            strict_intersection=strict_intersection,
            tol=rel,
        )
        assert len(intersections) == 0


@pytest.mark.parametrize("shape", TEST_SHAPES)
@pytest.mark.parametrize("strict_intersection", [True, False])
def test_intersect_shape_fully_outside(
    shape: GeomShape, strict_intersection: bool, rel: float = TOL_MM
) -> None:
    bbox = shape.bbox()
    for other_shape in TEST_SHAPES:
        translate_amount = bbox.left - other_shape.bbox().right - 1
        translated_shape = other_shape.translated(Vector2D(translate_amount, 0))
        intersections = get_intersection_points(
            shape1=translated_shape,
            shape2=shape,
            strict_intersection=strict_intersection,
            tol=rel,
        )
        assert len(intersections) == 0


@pytest.mark.parametrize("shape", TEST_SHAPES)
@pytest.mark.parametrize("strict_intersection", [True, False])
def test_intersect_shape_touching_outline_in_two_points(
    shape: GeomShape, strict_intersection: bool, rel: float = TOL_MM
) -> None:
    # We know that all test shapes must have an outline going through the points
    # (-1, -1) and (+1, +1). Let's create some shapes that are basically just dots in
    # these two points:
    other_shapes: list[GeomShape] = []
    rel_vec = Vector2D(rel, -rel)
    for point in [Vector2D(-1, -1), Vector2D(+1, +1)]:
        other_shapes += [
            # Shapes with zero size:
            GeomArc(center=point, start=point, angle=180),
            GeomCircle(center=point, radius=0),
            # skipping as line segments with 0 length will never intersect - hence
            # commented out (same applies to polygons and rectangles):
            # GeomLine(start=point, end=point),
            # GeomPolygon(shape=[point, point, point, point]),
            # GeomRectangle(center=point, size=[0, 0]),
            # Shapes with 2*`rel` size:
            # The arc doesn't work because of an optimization made for detecting almost-
            # tangent lines to circles - hence commented out:
            # GeomArc(center=point, start=point+rel/2, angle=180),
            GeomCircle(center=point, radius=rel / 2),
            GeomLine(start=point - rel_vec, end=point + rel_vec),
            GeomRectangle(center=point, size=[2 * rel, 2 * rel]),
            GeomPolygon(shape=GeomRectangle(center=point, size=[2 * rel, 2 * rel])),
        ]
    for other_shape in other_shapes:
        intersections = get_intersection_points(
            shape1=other_shape,
            shape2=shape,
            strict_intersection=strict_intersection,
            tol=rel,
        )
        if strict_intersection:
            assert len(intersections) == 0
        else:
            assert len(intersections) > 0


@pytest.mark.parametrize("shape", TEST_SHAPES)
def test_intersect_shape_touching_outline_on_all_sides(
    shape: GeomShape, rel: float = TOL_MM
) -> None:
    # Test that a tangent horizontal line along the top of the shape creates no
    # intersections:
    top = shape.bbox().top + rel / 2
    line_horizontal_tangent = GeomLine(start=(100, top), end=(+100, top))
    intersections = get_intersection_points(
        shape1=shape, shape2=line_horizontal_tangent, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent horizontal line along the bottom of the shape creates no
    # intersections:
    bottom = shape.bbox().bottom - rel / 2
    line_horizontal_tangent = GeomLine(start=(100, bottom), end=(+100, bottom))
    intersections = get_intersection_points(
        shape1=shape, shape2=line_horizontal_tangent, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent vertical line along the left of the shape creates no
    # intersections:
    left = shape.bbox().left + rel / 2
    line_vertical_tangent = GeomLine(start=(left, -100), end=(left, +100))
    intersections = get_intersection_points(
        shape1=shape, shape2=line_vertical_tangent, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent vertical line along the right of the shape creates no
    # intersections:
    right = shape.bbox().right - rel / 2
    line_vertical_tangent = GeomLine(start=(right, -100), end=(right, +100))
    intersections = get_intersection_points(
        shape1=shape, shape2=line_vertical_tangent, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent circle on the top has no intersection:
    top = shape.bbox().top
    circle_tangent_top = GeomCircle(center=(0, top - 1), radius=1 + rel / 2)
    intersections = get_intersection_points(
        shape1=shape, shape2=circle_tangent_top, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent circle on the bottom has no intersection:
    bottom = shape.bbox().bottom
    circle_tangent_bottom = GeomCircle(center=(0, bottom + 1), radius=1 + rel / 2)
    intersections = get_intersection_points(
        shape1=shape, shape2=circle_tangent_bottom, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent circle on the left has no intersection:
    left = shape.bbox().left
    circle_tangent_left = GeomCircle(center=(left - 1, 0), radius=1 + rel / 2)
    intersections = get_intersection_points(
        shape1=shape, shape2=circle_tangent_left, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent circle on the right has no intersection:
    right = shape.bbox().right
    circle_tangent_right = GeomCircle(center=(right + 1, 0), radius=1 + rel / 2)
    intersections = get_intersection_points(
        shape1=shape, shape2=circle_tangent_right, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent half-circle (arc with 180° angle) on the top has no
    # intersection:
    top = shape.bbox().top
    arc_tangent_top = GeomArc(center=(0, top - 1), start=(1 + rel / 2, top - 1), angle=180)  # fmt: skip
    intersections = get_intersection_points(
        shape1=shape, shape2=arc_tangent_top, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent half-circle (arc with 180° angle) on the bottom has no
    # intersection:
    bottom = shape.bbox().bottom
    arc_tangent_bottom = GeomArc(center=(0, bottom + 1), start=(1 + rel / 2, bottom + 1), angle=-180)  # fmt: skip
    intersections = get_intersection_points(
        shape1=shape, shape2=arc_tangent_bottom, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent half-circle (arc with 180° angle) on the left has no
    # intersection:
    left = shape.bbox().left
    arc_tangent_left = GeomArc(center=(left - 1, 0), start=(left - 1, 1 + rel / 2), angle=-180)  # fmt: skip
    intersections = get_intersection_points(
        shape1=shape, shape2=arc_tangent_left, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent half-circle (arc with 180° angle) on the right has no
    # intersection:
    right = shape.bbox().right
    arc_tangent_right = GeomArc(center=(right + 1, 0), start=(right + 1, 1 + rel / 2), angle=180)  # fmt: skip
    intersections = get_intersection_points(
        shape1=shape, shape2=arc_tangent_right, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent rectangle on the top has no intersection:
    top = shape.bbox().top
    rectangle_tangent_top = GeomRectangle(center=(0, top - 1 + rel / 2), size=(1, 1))
    intersections = get_intersection_points(
        shape1=shape, shape2=rectangle_tangent_top, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent rectangle on the bottom has no intersection:
    bottom = shape.bbox().bottom
    rectangle_tangent_bottom = GeomRectangle(
        center=(0, bottom + 1 - rel / 2), size=(1, 1)
    )
    intersections = get_intersection_points(
        shape1=shape, shape2=rectangle_tangent_bottom, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent rectangle on the left has no intersection:
    left = shape.bbox().left
    rectangle_tangent_left = GeomRectangle(center=(left - 1 + rel / 2, 0), size=(1, 1))
    intersections = get_intersection_points(
        shape1=shape, shape2=rectangle_tangent_left, tol=rel
    )
    assert len(intersections) == 0

    # Test that a tangent rectangle on the right has no intersection:
    right = shape.bbox().right
    rectangle_tangent_right = GeomRectangle(
        center=(right + 1 - rel / 2, 0), size=(1, 1)
    )
    intersections = get_intersection_points(
        shape1=shape, shape2=rectangle_tangent_right, tol=rel
    )
    assert len(intersections) == 0


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_intersections",
    [
        (TEST_SHAPE_ARC,                [(0, sqrt(2))]),
        (TEST_SHAPE_LINE,               [(0, 0)]),
        (TEST_SHAPE_CROSS,              [(0, 0)]),
        (TEST_SHAPE_CIRCLE,             [(0, -sqrt(2)), (0, sqrt(2))]),
        (TEST_SHAPE_RECTANGLE,          [(0, -1), (0, 1)]),
        (TEST_SHAPE_POLYGON,            [(0, -1), (0, 1)]),
        (TEST_SHAPE_COMPOUND_POLYGON,   [(0, -1), (0, 1)]),
        (TEST_SHAPE_STADIUM,            [(0, -1), (0, 1)]),
        (TEST_SHAPE_CRUCIFORM,          [(0, 2), (0, -2)]),
        (TEST_SHAPE_ROUND_RECTANGLE,    [(0, 1.5-sqrt(2)/4), (0, sqrt(2)/4-1.5)]),
        (TEST_SHAPE_TRAPEZOID,          [(0, -1), (0, 1)]),
    ],
)  # fmt: on
def test_intersect_with_line(shape: GeomShape, expected_intersections: list[tuple[float, float]], rel: float = TOL_MM) -> None:
    # Test that a vertical line along the y-axis creates the correct intersections:
    line_vertical = GeomLine(start=(0, -100), end=(0, +100))
    intersections = get_intersection_points(shape1=shape, shape2=line_vertical, tol=rel)
    assert are_equal(intersections, expected_intersections, rel=rel)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_intersections",
    [
        (TEST_SHAPE_ARC,                [(-sqrt(1 / 2), sqrt(3 / 2))]),
        (TEST_SHAPE_LINE,               [(0, 0)]),
        (TEST_SHAPE_CROSS,              [(0, 0)]),
        (TEST_SHAPE_CIRCLE,             [(-sqrt(1 / 2), sqrt(3 / 2)), (-sqrt(1 / 2), -sqrt(3 / 2))]),  # NOQA
        (TEST_SHAPE_RECTANGLE,          [(-1, -1), (-1, 1)]),
        (TEST_SHAPE_POLYGON,            [(-1, -1), (-1, 1)]),
        (TEST_SHAPE_COMPOUND_POLYGON,   [(-1, -1), (-1, 1)]),
        (TEST_SHAPE_STADIUM,            [(sqrt(3) - 2, -1), (sqrt(3) - 2, +1)]),
        (TEST_SHAPE_CRUCIFORM,          [(-1, sqrt(3)), (-1, -sqrt(3))]),
        (TEST_SHAPE_ROUND_RECTANGLE,    [(-0.8439027006376734, 1.1058060460527974), (-0.8439027006376734, -1.1058060460527974)]),  # NOQA
        (TEST_SHAPE_TRAPEZOID,          [(2 * sqrt(2) - 3, -1), (2 * sqrt(2) - 3, +1)]),
    ],
)  # fmt: on
def test_intersect_with_circle(shape: GeomShape, expected_intersections: list[tuple[float, float]], rel: float = TOL_MM) -> None:
    # Test that a circle (whose center coincides with the center-left point of the
    # shape's bounding box and intersects the origin) intesects as expected:
    left = shape.bbox().left
    circle_left = GeomCircle(center=(left, 0), radius=left)
    intersections = get_intersection_points(shape1=shape, shape2=circle_left, tol=rel)
    assert are_equal(intersections, expected_intersections, rel=rel)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_intersections",
    [
        (TEST_SHAPE_ARC,                [(-sqrt(1 / 2), sqrt(3 / 2))]),
        (TEST_SHAPE_LINE,               []),
        (TEST_SHAPE_CROSS,              []),
        (TEST_SHAPE_CIRCLE,             [(-sqrt(1 / 2), sqrt(3 / 2))]),
        (TEST_SHAPE_RECTANGLE,          [(-1, 1)]),
        (TEST_SHAPE_POLYGON,            [(-1, 1)]),
        (TEST_SHAPE_COMPOUND_POLYGON,   [(-1, 1)]),
        (TEST_SHAPE_STADIUM,            [(sqrt(3) - 2, 1)]),
        (TEST_SHAPE_CRUCIFORM,          [(-1, sqrt(3))]),
        (TEST_SHAPE_ROUND_RECTANGLE,    [(-0.8439027006376734, 1.1058060460527974)]),
        (TEST_SHAPE_TRAPEZOID,          [(2 * sqrt(2) - 3, +1)]),
    ],
)  # fmt: on
def test_intersect_with_arc(shape: GeomShape, expected_intersections: list[tuple[float, float]], rel: float = TOL_MM) -> None:
    # Test that an arc of 180° (whose center coincides with the center-left point of the
    # shape's bounding box and intersects the origin) intesects as expected:
    left = shape.bbox().left
    arc_left = GeomArc(center=(left, 0), start=(0, 0), angle=180)
    intersections = get_intersection_points(shape1=shape, shape2=arc_left, tol=rel)
    assert are_equal(intersections, expected_intersections, rel=rel)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_intersections",
    [
        (TEST_SHAPE_ARC,                [(0, sqrt(2))]),
        (TEST_SHAPE_LINE,               [(0, 0)]),
        (TEST_SHAPE_CROSS,              [(0, 0)]),
        (TEST_SHAPE_CIRCLE,             [(0, sqrt(2)), (0, -sqrt(2))]),
        (TEST_SHAPE_RECTANGLE,          []),
        (TEST_SHAPE_POLYGON,            []),
        (TEST_SHAPE_COMPOUND_POLYGON,   []),
        (TEST_SHAPE_STADIUM,            [(0, -1), (0, 1)]),
        (TEST_SHAPE_CRUCIFORM,          []),
        (TEST_SHAPE_ROUND_RECTANGLE,    []),
        (TEST_SHAPE_TRAPEZOID,          [(0, -1), (0, 1)]),
    ],
)  # fmt: on
def test_intersect_with_rectangle(shape: GeomShape, expected_intersections: list[tuple[float, float]], rel: float = TOL_MM) -> None:
    # Test that a rectangle (whose center coincides with the center-left point of the
    # shape's bounding box and intersects the origin) intesects as expected:
    left = shape.bbox().left
    rectangle_left = GeomRectangle(center=(left, 0), size=(2 * left, 2 * left))
    intersections = get_intersection_points(shape1=shape, shape2=rectangle_left, tol=rel)
    assert are_equal(intersections, expected_intersections, rel=rel)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_intersections",
    [
        (TEST_SHAPE_ARC,                []),
        (TEST_SHAPE_LINE,               [(sqrt(1 / 2), sqrt(1 / 2)), (-sqrt(1 / 2), -sqrt(1 / 2))]),  # NOQA
        (TEST_SHAPE_CROSS,              [(sqrt(1 / 2), sqrt(1 / 2)), (-sqrt(1 / 2), -sqrt(1 / 2)), (-sqrt(1 / 2), sqrt(1 / 2)), (sqrt(1 / 2), -sqrt(1 / 2))]),  # NOQA
        (TEST_SHAPE_CIRCLE,             []),
        (TEST_SHAPE_RECTANGLE,          [(1, sqrt(2)-1), (1, 1-sqrt(2)), (-1, sqrt(2)-1), (-1, 1-sqrt(2)), (sqrt(2)-1, 1), (sqrt(2)-1, -1), (1-sqrt(2), 1), (1-sqrt(2), -1)]),  # NOQA
        (TEST_SHAPE_POLYGON,            [(1, sqrt(2)-1), (1, 1-sqrt(2)), (-1, sqrt(2)-1), (-1, 1-sqrt(2)), (sqrt(2)-1, 1), (sqrt(2)-1, -1), (1-sqrt(2), 1), (1-sqrt(2), -1)]),  # NOQA
        (TEST_SHAPE_COMPOUND_POLYGON,   [(1, sqrt(2)-1), (1, 1-sqrt(2)), (-1, sqrt(2)-1), (-1, 1-sqrt(2)), (sqrt(2)-1, 1), (sqrt(2)-1, -1), (1-sqrt(2), 1), (1-sqrt(2), -1)]),  # NOQA
        (TEST_SHAPE_STADIUM,            [(sqrt(2) - 1, 1), (sqrt(2) - 1, -1), (1-sqrt(2), 1), (1-sqrt(2), -1)]),  # NOQA
        (TEST_SHAPE_CRUCIFORM,          []),
        (TEST_SHAPE_ROUND_RECTANGLE,    [(0.26776695296636893, 1.5-sqrt(2)/4), (0.26776695296636893, sqrt(2)/4-1.5), (-0.26776695296636893, 1.5-sqrt(2)/4), (-0.26776695296636893, sqrt(2)/4-1.5), (1.5-sqrt(2)/4, 0.26776695296636893), (1.5-sqrt(2)/4, -0.26776695296636893), (sqrt(2)/4-1.5, 0.26776695296636893), (sqrt(2)/4-1.5, -0.26776695296636893)]),  # NOQA
        (TEST_SHAPE_TRAPEZOID,          [(sqrt(2) - 1, 1), (sqrt(2) - 1, -1), (1-sqrt(2), 1), (1-sqrt(2), -1)]),  # NOQA
    ],
)
# fmt: on
def test_intersect_with_rotated_rectangle(
    shape: GeomShape,
    expected_intersections: list[tuple[float, float]],
    rel: float = TOL_MM,
) -> None:
    # Test that a centered unit rectangle rotated by 45° intesects as expected:
    rectangle_45 = GeomRectangle(center=(0, 0), size=(2, 2), angle=45)
    intersections = get_intersection_points(shape1=shape, shape2=rectangle_45, tol=rel)
    assert are_equal(intersections, expected_intersections, rel=rel)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_intersections",
    [
        (TEST_SHAPE_ARC,                [(3*sqrt(2)/5, 4*sqrt(2)/5), (-3*sqrt(2)/5, 4*sqrt(2)/5), (-4*sqrt(2)/5, 3*sqrt(2)/5), (-4*sqrt(2)/5, -3*sqrt(2)/5)]),  # NOQA
        (TEST_SHAPE_LINE,               []),
        (TEST_SHAPE_CROSS,              []),
        (TEST_SHAPE_CIRCLE,             [(3*sqrt(2)/5, 4*sqrt(2)/5), (-3*sqrt(2)/5, 4*sqrt(2)/5), (-4*sqrt(2)/5, 3*sqrt(2)/5), (-4*sqrt(2)/5, -3*sqrt(2)/5), (-3*sqrt(2)/5, -4*sqrt(2)/5), (3*sqrt(2)/5, -4*sqrt(2)/5), (4*sqrt(2)/5, -3*sqrt(2)/5), (4*sqrt(2)/5, 3*sqrt(2)/5)]),  # NOQA
        (TEST_SHAPE_RECTANGLE,          [(2/(2+sqrt(2)), 1), (-2/(2+sqrt(2)), 1), (-1, 2/(2+sqrt(2))), (-1, -2/(2+sqrt(2))), (-2/(2+sqrt(2)), -1), (2/(2+sqrt(2)), -1), (1, -2/(2+sqrt(2))), (1, 2/(2+sqrt(2)))]),  # NOQA
        (TEST_SHAPE_POLYGON,            [(2/(2+sqrt(2)), 1), (-2/(2+sqrt(2)), 1), (-1, 2/(2+sqrt(2))), (-1, -2/(2+sqrt(2))), (-2/(2+sqrt(2)), -1), (2/(2+sqrt(2)), -1), (1, -2/(2+sqrt(2))), (1, 2/(2+sqrt(2)))]),  # NOQA
        (TEST_SHAPE_COMPOUND_POLYGON,   [(2/(2+sqrt(2)), 1), (-2/(2+sqrt(2)), 1), (-1, 2/(2+sqrt(2))), (-1, -2/(2+sqrt(2))), (-2/(2+sqrt(2)), -1), (2/(2+sqrt(2)), -1), (1, -2/(2+sqrt(2))), (1, 2/(2+sqrt(2)))]),  # NOQA
        (TEST_SHAPE_STADIUM,            [(-1.1972803391682256, 0.9803471159633562), (-1.1972803391682256, -0.9803471159633562), (-0.5857864376269047, -1.0), (0.5857864376269047, -1.0), (1.1972803391682256, -0.9803471159633562), (1.1972803391682256, 0.9803471159633562), (0.5857864376269047, 1.0), (-0.5857864376269047, 1.0)]),  # NOQA
        (TEST_SHAPE_CRUCIFORM,          [((1+sqrt(2))/2, 1), (-(1+sqrt(2))/2, 1), (-1, (1+sqrt(2))/2), (-1, -(1+sqrt(2))/2), (-(1+sqrt(2))/2, -1), ((1+sqrt(2))/2, -1), (1, -(1+sqrt(2))/2), (1, (1+sqrt(2))/2)]),  # NOQA
        (TEST_SHAPE_ROUND_RECTANGLE,    [(0.8179861669824924, 1.1160998646777938), (-0.8179861669824924, 1.1160998646777938), (-1.1160998646777938, 0.8179861669824924), (-1.1160998646777938, -0.8179861669824924), (-0.8179861669824924, -1.1160998646777938), (0.8179861669824924, -1.1160998646777938), (1.1160998646777938, -0.8179861669824924), (1.1160998646777938, 0.8179861669824924)]),  # NOQA
        (TEST_SHAPE_TRAPEZOID,          [(-0.5857864376269047, -1.0), (0.5857864376269047, -1.0), (1.2071067811865477, -1.0), (-1.2071067811865477, -1.0), (1.1380711874576983, 0.8619288125423017), (0.5857864376269046, 1.0), (-0.5857864376269046, 1.0), (-1.1380711874576983, 0.8619288125423017)]),  # NOQA
    ],
)
# fmt: on
def test_intersect_with_conave_polygon(
    shape: GeomShape,
    expected_intersections: list[tuple[float, float]],
    rel: float = TOL_MM,
) -> None:
    # Test that a centered star-like polygon with circumradius of 2 intesects as
    # expected:
    pts: list[list[float]] = [[-1, -1], [0, -0.5], [1, -1], [0.5, 0], [1, 1], [0, 0.5], [-1, 1], [-0.5, 0]]  # fmt: skip  # NOQA
    pts2: list[list[float]] = []
    for pt in pts:
        pts2.append([sqrt(2) * pt[0], sqrt(2) * pt[1]])
    poly = GeomPolygon(shape=pts2)
    intersections = get_intersection_points(shape1=shape, shape2=poly, tol=rel)
    assert are_equal(intersections, expected_intersections, rel=rel)
