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

from math import radians, sqrt

import pytest

from kilibs.geom import (
    BoundingBox,
    GeomArc,
    GeomCircle,
    GeomCompoundPolygon,
    GeomCross,
    GeomCruciform,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomRoundRectangle,
    GeomShape,
    GeomShapeClosed,
    GeomShapeOpen,
    GeomStadium,
    GeomTrapezoid,
    Vec2DCompatible,
    Vector2D,
)
from kilibs.geom.tolerances import TOL_MM
from tests.kilibs.geom.geom_test_shapes import (
    CENTER,
    POINTS,
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
from tests.kilibs.geom.is_equal import is_equal_bboxes, is_equal_geom_shapes


def test_constructors(rel: float = TOL_MM) -> None:
    centers: list[Vec2DCompatible] = []
    centers.append([0, 0])
    centers.append((0, 0))
    centers.append(Vector2D(0, 0))

    ###    GeomArc   ###################################################################
    arcs: list[GeomArc] = []
    # Test different types for the points (Vector2D, tuple, list)
    # At the same time test the constructor with 2 different points + angle:
    arcs.append(GeomArc(center=centers[0], start=POINTS[0], angle=-180))
    arcs.append(GeomArc(center=centers[1], mid=POINTS[3], angle=-180))
    arcs.append(GeomArc(center=centers[2], end=POINTS[2], angle=-180))
    # Test the copy constructor with and without the "shape=" parameter:
    arcs.append(GeomArc(arcs[0]))
    arcs.append(GeomArc(shape=arcs[0]))
    # Test the constructor using 3 points:
    arcs.append(GeomArc(center=centers[0], start=POINTS[0], end=POINTS[2]))
    # Test the constructor using 3 points specifying "long_way" = False:
    arcs.append(GeomArc(start=POINTS[0], mid=POINTS[3], end=POINTS[2], long_way=False))
    # Test the a copy of itself:
    arcs.append(arcs[0].copy())
    # Test that all GeomArcs are equal:
    for arc in arcs:
        assert is_equal_geom_shapes(arcs[0], arc, rel)

    ###    GeomLine   ##################################################################
    lines: list[GeomLine] = []
    # Test the constructor with a start and end point:
    lines.append(GeomLine(start=POINTS[0], end=POINTS[2]))
    # Test the constructor with a anoher line:
    lines.append(GeomLine(lines[0]))
    # Test the constructor with a copy of itself:
    lines.append(lines[0].copy())
    # Test that all GeomLines are equal:
    for line in lines:
        assert is_equal_geom_shapes(lines[0], line, rel)

    ###    GeomCross   #################################################################
    crosses: list[GeomCross] = []
    # Test the constructor with a start and end point:
    crosses.append(GeomCross(center=CENTER, size=(2, 2)))
    # Test the constructor with a anoher line:
    crosses.append(GeomCross(crosses[0]))
    # Test the constructor with a copy of itself:
    crosses.append(crosses[0].copy())
    # Test that all GeomCross are equal:
    for cross in crosses:
        assert is_equal_geom_shapes(crosses[0], cross, rel)

    ###    GeomCircle   ################################################################
    circles: list[GeomCircle] = []
    # Test the constructor with center and radius:
    circles.append(GeomCircle(center=centers[0], radius=arcs[0].radius))
    # Test the constructor with another circle:
    circles.append(GeomCircle(circles[0]))
    # Test the constructor with an arc:
    circles.append(GeomCircle(arcs[0]))
    # Test the constructor with a copy of itself:
    circles.append(circles[0].copy())
    # Test that all GeomCircles are equal:
    for circle in circles:
        assert is_equal_geom_shapes(circles[0], circle, rel)

    ###    GeomRectangle   #############################################################
    rectangles: list[GeomRectangle] = []
    # Test the constructor with a center and size argument:
    rectangles.append(GeomRectangle(center=centers[0], size=[2, 2]))
    # Test the constructor with a anoher rectangle:
    rectangles.append(GeomRectangle(rectangles[0]))
    # Test the constructor with a bounding box:
    rectangles.append(GeomRectangle(rectangles[0].bbox()))
    # Test the constructor with a start and end point:
    rectangles.append(GeomRectangle(start=POINTS[0], end=POINTS[2]))
    # Test the constructor with a end and a start point:
    rectangles.append(GeomRectangle(start=POINTS[3], end=POINTS[1]))
    # Test the constructor with a start point and the size:
    rectangles.append(GeomRectangle(start=POINTS[0], size=rectangles[0].size))
    # Test the constructor with a copy of itself:
    rectangles.append(rectangles[0].copy())
    # Test that all GeomRectangles are equal:
    for rectangle in rectangles:
        assert is_equal_geom_shapes(rectangles[0], rectangle, rel)

    ###    GeomPolygon   ###############################################################
    polygons: list[GeomPolygon] = []
    polygons.append(GeomPolygon(POINTS))
    # Test the constructor with a anoher polygon:
    polygons.append(GeomPolygon(polygons[0]))
    # Test the constructor with a rectangle:
    polygons.append(GeomPolygon(rectangles[0]))
    # Test the constructor with a bounding box:
    polygons.append(GeomPolygon(rectangles[0].bbox()))
    # Test the constructor with a copy of itself:
    polygons.append(polygons[0].copy())
    # Test that all GeomPolygons are equal:
    for polygon in polygons:
        assert is_equal_geom_shapes(polygons[0], polygon, rel)

    ###    GeomCompoundPolygon   #######################################################
    comp_polygons: list[GeomCompoundPolygon] = []
    # Test the constructor with a list of points:
    comp_polygons.append(GeomCompoundPolygon(POINTS))
    # Test the constructor with a anoher compound polygon:
    comp_polygons.append(GeomCompoundPolygon(comp_polygons[0]))
    # Test the constructor with a list of lines:
    comp_polygons.append(GeomCompoundPolygon(rectangles[0].get_atomic_shapes()))
    # Test the constructor with a copy of itself:
    comp_polygons.append(comp_polygons[0].copy())
    # Test that all GeomCompoundPolygons are equal:
    for comp_polygon in comp_polygons:
        assert is_equal_geom_shapes(comp_polygons[0], comp_polygon, rel)

    ###    GeomStadium   ###############################################################
    stadiums: list[GeomStadium] = []
    stadiums.append(GeomStadium(center_1=(-1, 0), center_2=(1, 0), radius=0.5))
    # Test the constructor with a anoher stadium:
    stadiums.append(GeomStadium(stadiums[0]))
    # Test the constructor with a rectangle inscription:
    stadiums.append(GeomStadium(shape=GeomRectangle(center=(0, 0), size=(3, 1))))
    # Test the constructor with a copy of itself:
    stadiums.append(stadiums[0].copy())
    # Test that all GeomStadiums are equal:
    for stadium in stadiums:
        assert is_equal_geom_shapes(stadiums[0], stadium, rel)

    ###    GeomRoundRectangle   ########################################################
    round_rects: list[GeomRoundRectangle] = []
    round_rects.append(GeomRoundRectangle(size=(4, 2), center=(0, 0), corner_radius=1))
    # Test the constructor with a anoher round rectangle:
    round_rects.append(GeomRoundRectangle(round_rects[0]))
    # Test the constructor with a start position:
    round_rects.append(GeomRoundRectangle(start=(-2, -1), size=(4, 2), corner_radius=1))
    # Test the constructor with a copy of itself:
    round_rects.append(round_rects[0].copy())
    # Test that all GeomStadiums are equal:
    for round_rect in round_rects:
        assert is_equal_geom_shapes(round_rects[0], round_rect, rel)

    ###    GeomTrapezoid   #############################################################
    trapezoids: list[GeomTrapezoid] = []
    trapezoids.append(GeomTrapezoid(size=(4,2), center=(0, 0), corner_radius=0.5, side_angle=-10))  # fmt: skip
    # Test the constructor with a anoher round rectangle:
    trapezoids.append(GeomTrapezoid(trapezoids[0]))
    # Test the constructor with a start position:
    trapezoids.append(GeomTrapezoid(size=(4,2), start=(-2, -1), corner_radius=0.5, side_angle=-10))  # fmt: skip
    # Test the constructor with a copy of itself:
    trapezoids.append(trapezoids[0].copy())
    # Test that all GeomTrapezoid are equal:
    for trapezoid in trapezoids:
        assert is_equal_geom_shapes(trapezoids[0], trapezoid, rel)

    ###    GeomCruciform   #############################################################
    cruciforms: list[GeomCruciform] = []
    cruciforms.append(GeomCruciform(overall_w=4, overall_h=4, tail_w=2, tail_h=2, center=(0, 0)))  # fmt: skip
    # Test the constructor with a anoher round rectangle:
    cruciforms.append(GeomCruciform(cruciforms[0]))
    # Test the constructor with a copy of itself:
    cruciforms.append(cruciforms[0].copy())
    # Test that all GeomCruciform are equal:
    for cruciform in cruciforms:
        assert is_equal_geom_shapes(cruciforms[0], cruciform, rel)


@pytest.mark.parametrize("shape", TEST_SHAPES)
def test_copy(shape: GeomShape, rel: float = TOL_MM) -> None:
    copied_shape = shape.copy()
    translated_copy = copied_shape.copy().translate(Vector2D(1.2345, 0))
    # Test that when modifying a copied shape, the original remains the same.
    # (We are testing that the deep copy works correctly). To do so, we modify
    # one of the copies, test that it is different, and that the original is equal
    # to the copy that has not been modified.
    assert not is_equal_geom_shapes(shape, translated_copy, rel=rel)
    assert is_equal_geom_shapes(shape, copied_shape, rel=rel)


@pytest.mark.parametrize("shape", TEST_SHAPES)
def test_translate(shape: GeomShape, rel: float = TOL_MM) -> None:
    translated_shape = shape.copy()

    vectors: list[Vec2DCompatible] = []
    vectors.append(Vector2D(1, 0))
    vectors.append(Vector2D(0, 1))
    vectors.append(Vector2D(-1, 0))
    vectors.append(Vector2D(0, -1))

    # Perform vector translations and test that the shapes are not equal anymore:
    for vector in vectors[:-1]:
        translated_shape.translate(vector=vector)
        assert not is_equal_geom_shapes(shape, translated_shape, rel)

    # Perform vector translation back to origin and test that the shapes are equal:
    translated_shape.translate(vector=vectors[-1])
    assert is_equal_geom_shapes(shape, translated_shape, rel)

    # Perform x-axis translations and test that the shapes are not equal anymore
    # until the last translation is performed which undoes the previous ones:
    values: list[float] = [-1, -2.5, 3.5]
    for i, value in enumerate(values):
        translated_shape.translate(Vector2D(value, 0))
        if i < len(values) - 1:
            assert not is_equal_geom_shapes(shape, translated_shape, rel)
        else:
            assert is_equal_geom_shapes(shape, translated_shape, rel)

    # Perform y-axis translations and test that the shapes are not equal anymore
    # until the last translation is performed which undoes the previous ones:
    values = [-1, -2.5, 3.5]
    for i, value in enumerate(values):
        translated_shape.translate(Vector2D(0, value))
        if i < len(values) - 1:
            assert not is_equal_geom_shapes(shape, translated_shape, rel)
        else:
            assert is_equal_geom_shapes(shape, translated_shape, rel)


@pytest.mark.parametrize("shape", TEST_SHAPES)
def test_rotate(shape: GeomShape, rel: float = TOL_MM) -> None:
    rotated_shape = shape.copy()
    origin = Vector2D(1, -1)
    angle_degs = [90, 120, 160, -10]

    # Perform rotations in degrees and test that the shapes are not equal anymore:
    for angle_deg in angle_degs[:-1]:
        rotated_shape.rotate(angle=angle_deg, origin=origin)
        assert not is_equal_geom_shapes(shape, rotated_shape, rel)

    # Perform a rotation in degrees back to origin and test that the shapes are equal:
    rotated_shape.rotate(angle=angle_degs[-1], origin=origin)
    assert is_equal_geom_shapes(shape, rotated_shape, rel)


@pytest.mark.parametrize("shape", TEST_SHAPES_CLOSED)
def test_inflate(shape: GeomShapeClosed, rel: float = TOL_MM) -> None:
    amounts = [0.2, 0.3, -0.5]
    inflated_shape = shape.copy()

    # Perform inflations and test that the shapes are not equal anymore until the
    # last inflation is performed.
    for i, amount in enumerate(amounts):
        inflated_shape.inflate(amount=amount)
        if i < len(amounts) - 1:
            assert not is_equal_geom_shapes(shape, inflated_shape, rel)
        else:
            assert is_equal_geom_shapes(shape, inflated_shape, rel)

    # Test that if shapes are deflated to zero or beyond `None` is returned.
    # Note that the GeomPolygon is a special case where this does not work as there,
    # due to the implementation, negative polygons are possible.
    if not isinstance(shape, GeomPolygon | GeomCompoundPolygon):
        with pytest.raises(ValueError):
            inflated_shape.inflate(amount=-sqrt(2))


@pytest.mark.parametrize("shape", TEST_SHAPES)
def test_is_point_on_self(
    shape: GeomShapeClosed | GeomShapeOpen, rel: float = TOL_MM
) -> None:
    points = [Vector2D(1, 1), Vector2D(-1, -1)]

    # Test if the points are on the shapes:
    for point in points:
        assert shape.is_point_on_self(point=point, tol=rel)

    # Test if the following point is also on the shapes (for an arc this is the mid
    # point):
    point = Vector2D(-1, 1)
    if not isinstance(shape, GeomLine):
        assert shape.is_point_on_self(point=point, tol=rel)

    # Test if the tolerance implementation works for points within tolerance:
    points = [
        Vector2D(1 + 0.5 * rel, 1 + 0.5 * rel),
        Vector2D(-1 - 0.5 * rel, -1 - 0.5 * rel),
    ]
    for point in points:
        assert shape.is_point_on_self(point=point, tol=rel)

    # Test if the tolerance implementation works for points outside tolerance:
    points = [
        Vector2D(1 + 1.5 * rel, 1 + 1.5 * rel),
        Vector2D(-1 - 1.5 * rel, -1 - 1.5 * rel),
    ]
    for point in points:
        assert not shape.is_point_on_self(point=point, tol=rel)


# fmt: off
@pytest.mark.parametrize(
    "shape, expected_bbox",
    [
        (TEST_SHAPE_ARC, BoundingBox([-sqrt(2), -1], (1, sqrt(2)))),
        (TEST_SHAPE_LINE, BoundingBox([1, 1], (-1, -1))),
        (TEST_SHAPE_CROSS, BoundingBox([1, 1], (-1, -1))),
        (TEST_SHAPE_CIRCLE, BoundingBox([sqrt(2), sqrt(2)], (-sqrt(2), -sqrt(2)))),
        (TEST_SHAPE_RECTANGLE, BoundingBox([1, 1], (-1, -1))),
        (TEST_SHAPE_POLYGON, BoundingBox([1, 1], (-1, -1))),
        (TEST_SHAPE_COMPOUND_POLYGON, BoundingBox([1, 1], (-1, -1))),
        (TEST_SHAPE_STADIUM, BoundingBox([2, 1], (-2, -1))),
        (TEST_SHAPE_CRUCIFORM, BoundingBox([2, 2], (-2, -2))),
        (TEST_SHAPE_ROUND_RECTANGLE,BoundingBox([1.5 - sqrt(2) / 4, 1.5 - sqrt(2) / 4], (sqrt(2) / 4 - 1.5, sqrt(2) / 4 - 1.5))),  # NOQA
        (TEST_SHAPE_TRAPEZOID, BoundingBox([-3, -1], (3, 1))),
    ],
)
# fmt: on
def test_bbox(
    shape: GeomShape, expected_bbox: BoundingBox, rel: float = TOL_MM
) -> None:
    print(shape)
    # Test if the returned bounding boxes are equal to the expected ones:
    assert is_equal_bboxes(shape.bbox(), expected_bbox, rel)


@pytest.mark.parametrize("shape", TEST_SHAPES_CLOSED)
def test_is_point_inside_self(shape: GeomShapeClosed, rel: float = TOL_MM) -> None:
    points = [
        Vector2D(0, 0),
        Vector2D(1, 1),
        Vector2D(-1, -1),
        Vector2D(1 + 0.5 * rel, 1 + 0.5 * rel),
        Vector2D(-1 - 0.5 * rel, -1 - 0.5 * rel),
    ]

    # Test that all the points are inside (not strictly) the closed shapes:
    for point in points:
        assert shape.is_point_inside_self(point=point, strictly_inside=False, tol=rel)

    # Test that all the points (except the origin) are not strictly inside the closed
    # shapes:
    for point in points[1:]:
        assert not shape.is_point_inside_self(
            point=point, strictly_inside=True, tol=rel
        )

    # Test that all the points are outside of the closed shape (stricly and not):
    points = [
        Vector2D(1 + 1.5 * rel, 1 + 1.5 * rel),
        Vector2D(-1 - 1.5 * rel, -1 - 1.5 * rel),
    ]
    for point in points:
        assert not shape.is_point_inside_self(
            point=point, strictly_inside=False, tol=rel
        )
        assert not shape.is_point_inside_self(
            point=point, strictly_inside=True, tol=rel
        )
