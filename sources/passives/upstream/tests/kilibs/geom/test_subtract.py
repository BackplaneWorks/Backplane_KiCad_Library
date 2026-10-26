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
"""Tests for the graphical keepout classes.

These are not intended to be exhaustive, but mostly for a demonstration of how to use
the classes, as well as a place to put some simple tests to catch fiddly edge cases if
needed.

Exhaustive tests are high maintenance, and regressions will normally be much more
obvious by the visual diffs of the generated graphics than by delicate stacks of
numerical tests.
"""

from itertools import product

import pytest

from generators.tools.footprint.drawing_tools import applyKeepouts
from kilibs.geom import (
    GeomArc,
    GeomCircle,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomShape,
    GeomShapeClosed,
    Vec2DCompatible,
)
from kilibs.geom.operations import subtract
from kilibs.geom.tolerances import TOL_MM
from tests.kilibs.geom.geom_test_shapes import TEST_SHAPES
from tests.kilibs.geom.is_equal import is_equal

# Some numbers to use for adding to integers to make sure you try round and non-round
# values in floating point values (0.1 can't be expressed exactly in FP).
FLOATING_POINT_OFFSETS = [0.0, 0.1, -0.1]


@pytest.mark.parametrize(
    "center, size, line_start, line_end, expected_segs",
    [
        # Centred square, line from origin
        ((0, 0), (100, 100), (0, 0), (10, 10), []),  # Fully inside
        ((0, 0), (100, 100), (0, 0), (50, 50), []),  # Touching line
        ((0, 0), (100, 100), (0, 0), (50, 50), []),  # Touching corner
        # Centred square, line from origin to outside
        ((0, 0), (100, 100), (0, 0), (100, 0), [[(50, 0), (100, 0)]]),
    ],
)
def test_keepout_rect_vs_line(
    center: Vec2DCompatible,
    size: Vec2DCompatible,
    line_start: Vec2DCompatible,
    line_end: Vec2DCompatible,
    expected_segs: list[list[tuple[float, float]]],
) -> None:
    """Simple test for keepout rectangle vs line."""
    ko = GeomRectangle(center=center, size=size)
    line = GeomLine(start=line_start, end=line_end)
    new_items = subtract(line, ko)
    assert len(new_items) == len(expected_segs)
    for i, seg in enumerate(expected_segs):
        gseg = GeomLine(start=seg[0], end=seg[1])
        assert is_equal(new_items[i], gseg)


@pytest.mark.parametrize(
    "fp_fudge_x",
    FLOATING_POINT_OFFSETS,
)
def test_keepout_rect_coincident_line(fp_fudge_x: float) -> None:
    """Simple test for keepout rectangle vs line that lies on the keepout.

    These lines should NOT be trimmed, as they're common when computing
    offsets exactly on the keepout line.
    """
    ko = GeomRectangle(center=(0 + fp_fudge_x, 0), size=(100, 100))
    lines = [
        GeomLine(start=(-50 + fp_fudge_x, 50), end=(50 + fp_fudge_x, 50)),
        GeomLine(start=(-50 + fp_fudge_x, -50), end=(50 + fp_fudge_x, -50)),
        GeomLine(start=(50 + fp_fudge_x, -50), end=(50 + fp_fudge_x, 50)),
        GeomLine(start=(-50 + fp_fudge_x, -50), end=(-50 + fp_fudge_x, 50)),
    ]
    for line in lines:
        new_items = subtract(line, ko)
        assert is_equal(line, new_items[0])


def test_apply_keepout_1() -> None:
    # Four lines:
    # - Two cut by the keepout
    # - One fully inside - deleted
    # - One fully outside - retained
    #
    # Leaving 3 lines after keepout application
    items: list[GeomShape] = [
        GeomLine(start=(0, 0), end=(100, 0)),
        GeomLine(start=(0, 0), end=(0, 100)),
        GeomLine(start=(10, 10), end=(20, 20)),  # Inside
        GeomLine(start=(60, 60), end=(70, 70)),  # Outside
    ]
    ko = GeomRectangle(center=(0, 0), size=(100, 100))
    new_items = applyKeepouts(items, [ko])
    assert len(new_items) == 3


def test_apply_circles_to_circle() -> None:
    # Two circular keeouts, at 0 and 180
    # Should split the circle into two arcs
    items: list[GeomShape] = [
        GeomCircle(center=(0, 0), radius=1000),
    ]
    kos: list[GeomShapeClosed] = [
        GeomCircle(center=(-1000, 0), radius=100),
        GeomCircle(center=(1000, 0), radius=100),
    ]
    new_items = applyKeepouts(items, kos)
    assert len(new_items) == 2


@pytest.mark.parametrize(
    "fp_fudge_r, fp_fudge_x",
    list(product(FLOATING_POINT_OFFSETS, repeat=2)),
)
def test_arc_tangent_to_circle(fp_fudge_r: float, fp_fudge_x: float) -> None:
    # If an arc just touches the circle, it's one intersection,
    # which can upset the odd/even splitting if not handled
    items: list[GeomShape] = [
        GeomArc(
            start=(fp_fudge_x, 200 + fp_fudge_r),
            mid=(200 + fp_fudge_x + fp_fudge_r, 0),
            end=(fp_fudge_x, -200 - fp_fudge_r),
        ),
    ]
    kos: list[GeomShapeClosed] = [
        GeomCircle(
            center=(100 + fp_fudge_x, 0),
            radius=100 + fp_fudge_r,
        ),
    ]
    new_items = applyKeepouts(items, kos)
    assert len(new_items) == 1
    # The arc should be untouched
    assert new_items[0] == items[0]


@pytest.mark.parametrize(
    "fp_fudge_r, fp_fudge_cx",
    list(product(FLOATING_POINT_OFFSETS, repeat=2)),
)
def test_circle_tangent_to_circle(fp_fudge_r: float, fp_fudge_cx: float) -> None:
    # As for arc-circle, one circle just touching shouldn't clip.
    items: list[GeomShape] = [
        GeomCircle(center=(fp_fudge_cx, 0), radius=200 + fp_fudge_r),
    ]
    kos: list[GeomShapeClosed] = [
        GeomCircle(center=(100 + fp_fudge_cx, 0), radius=100 + fp_fudge_r),
    ]
    new_items = applyKeepouts(items, kos)
    assert len(new_items) == 1
    # The arc should be untouched
    assert new_items[0] == items[0]


@pytest.mark.parametrize(
    "fp_fudge_r, fp_fudge_cx",
    list(product(FLOATING_POINT_OFFSETS, repeat=2)),
)
def test_circle_tangent_to_rect(fp_fudge_r: float, fp_fudge_cx: float) -> None:
    # If a circle just touches the rectangle, it's one intersection,
    # and we reject it as a clip point
    items: list[GeomShape] = [
        GeomCircle(
            center=(200 + fp_fudge_cx, 0),
            radius=100 + fp_fudge_r,
        ),
    ]
    kos: list[GeomShapeClosed] = [
        GeomRectangle(
            center=(0 + fp_fudge_cx, 0),
            size=(100 + fp_fudge_r, 100 + fp_fudge_r),
        ),
    ]
    new_items = applyKeepouts(items, kos)
    assert len(new_items) == 1
    # The arc should be untouched
    assert new_items[0] == items[0]


def test_arc_to_circle_ko_reverse_angle() -> None:
    # Test a 180 arc with positive and negative angle
    # (in PCB land: 6-oclock to 12-oclock, mdpoint at 3-oclock)
    #
    # Cut it with a keepout circle such that the intersections are +-60 degrees
    # from the horizontal. Check that we do get two 30-degree chunks in both directions
    #
    # This exposes problems with angle ordering if not properly handled.
    def check_results(new_items: list[GeomShape]) -> None:
        assert len(new_items) == 2
        for item in new_items:
            assert isinstance(item, GeomArc)
            assert abs(abs(item.angle) - 30) <= TOL_MM

    # Left side
    arc_l = GeomArc(start=(0, 100), end=(0, -100), mid=(-100, 0))
    ko_l = GeomCircle(center=(-100, 0), radius=100)
    new_items = applyKeepouts([arc_l], [ko_l])
    check_results(new_items)

    # Right side (opposite angle)
    arc_r = GeomArc(start=(0, 100), end=(0, -100), mid=(100, 0))
    ko_r = GeomCircle(center=(100, 0), radius=100)

    # check that the angles are indeed opposite, or this test is bogus
    assert abs(arc_l.angle + arc_r.angle) <= TOL_MM
    new_items = applyKeepouts([arc_r], [ko_r])
    check_results(new_items)


@pytest.mark.parametrize(
    "fp_fudge_x",
    FLOATING_POINT_OFFSETS,
)
def test_arc_with_endpoint_on_ko_bound(fp_fudge_x: float) -> None:
    """Make sure we don't flub the case where the end/startpoint of the arc is also
    an intersection with the keepout.

    Add some fudge to the x coordinate to make sure we test with +/- FP roundoffs.
    """
    arc = GeomArc(
        start=(fp_fudge_x, 100),
        end=(fp_fudge_x, -100),
        mid=(100 + fp_fudge_x, 0),
    )
    ko_outside = GeomRectangle(
        center=(-100 + fp_fudge_x, 0),
        size=(200, 200),
    )
    # Check that the start point is indeed on the keepout edge
    assert is_equal(ko_outside.right, arc.start.x)
    new_items = applyKeepouts([arc], [ko_outside])
    assert len(new_items) == 1
    assert is_equal(abs(new_items[0].angle), 180)

    # and the other case where the arc is inside and touches
    # the keepout rectangle at the start/end points
    ko_inside = GeomRectangle(
        center=(100 + fp_fudge_x, 0),
        size=(200, 200),
    )

    # Check that the start point is indeed on the keepout edge
    assert is_equal(ko_inside.left, arc.start.x)
    new_items = applyKeepouts([arc], [ko_inside])
    assert len(new_items) == 0


@pytest.mark.parametrize("shape", TEST_SHAPES)
def test_keepout_with_rectangle(shape: GeomShape, rel: float = TOL_MM) -> None:
    # Keepout with a rectangle (whose center coincides with the center-left point of the
    # shape's bounding box and intersects the origin):
    left = shape.bbox().left
    rectangle_left = GeomRectangle(center=(left, 0), size=(left, left))
    kept_out = subtract(subject_shape=shape, clip_shape=rectangle_left, tol=rel)
    if isinstance(shape, GeomLine):
        assert is_equal(shape, kept_out[0], rel)
    elif isinstance(shape, GeomArc):
        assert len(kept_out) == 2
    elif isinstance(shape, GeomCircle):
        assert len(kept_out) == 1
    elif isinstance(shape, GeomRectangle | GeomPolygon):
        assert len(kept_out) == 5
