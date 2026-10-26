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

import pytest

from kilibs.geom import BoundingBox, Vector2D
from tests.kilibs.geom.geom_test_shapes import POINTS
from tests.kilibs.geom.is_equal import is_equal_bboxes


def test_constructor(rel: float = 1e-10) -> None:
    bboxs: list[BoundingBox] = []
    # Test the constructor with no argument:
    bboxs.append(BoundingBox())
    # Test the include_points() function on an empty bounding box:
    for point in POINTS:
        bboxs[0].include_point(Vector2D(point))
    # Test the constructor with two corner points:
    bboxs.append(BoundingBox(POINTS[0], POINTS[2]))
    # Test the constructor with two corner points but in inverted order:
    bboxs.append(BoundingBox(POINTS[3], POINTS[1]))
    # Test the constructor with a copy of itself:
    bboxs.append(bboxs[0].copy())
    # Test that all BoundingBoxes are equal:
    for bbox in bboxs:
        assert is_equal_bboxes(bboxs[0], bbox, rel)


def test_failures() -> None:
    bb = BoundingBox()
    with pytest.raises(RuntimeError):
        bb.top
    # Must have both points or neither
    with pytest.raises(ValueError):
        BoundingBox(Vector2D(10, 20))
    with pytest.raises(ValueError):
        BoundingBox(corner1=Vector2D(10, 20))
    with pytest.raises(ValueError):
        BoundingBox(corner2=Vector2D(10, 20))


def test_bbox_include_pts() -> None:
    bb = BoundingBox(corner1=Vector2D(10, 20), corner2=Vector2D(30, 40))
    assert bb.top == 20
    assert bb.bottom == 40
    assert bb.left == 10
    assert bb.right == 30

    # including internal point should not change bbox
    bb.include_point(Vector2D(15, 25))
    assert bb.top == 20
    assert bb.bottom == 40
    assert bb.left == 10
    assert bb.right == 30

    # include point above and left
    bb.include_point(Vector2D(5, 15))
    assert bb.top == 15
    assert bb.bottom == 40
    assert bb.left == 5
    assert bb.right == 30

    # to left only
    bb.include_point(Vector2D(0, 20))
    assert bb.top == 15
    assert bb.bottom == 40
    assert bb.left == 0
    assert bb.right == 30

    # to right only
    bb.include_point(Vector2D(35, 20))
    assert bb.top == 15
    assert bb.bottom == 40
    assert bb.left == 0
    assert bb.right == 35

    # to right and below
    bb.include_point(Vector2D(45, 45))
    assert bb.top == 15
    assert bb.bottom == 45
    assert bb.left == 0
    assert bb.right == 45


def test_bbox_include_bbox() -> None:
    bb = BoundingBox(corner1=Vector2D(10, 20), corner2=Vector2D(30, 40))
    bb2 = BoundingBox(corner1=Vector2D(100, 100), corner2=Vector2D(110, 110))
    bb.include_bbox(bb2)
    assert bb.top == 20
    assert bb.bottom == 110
    assert bb.left == 10
    assert bb.right == 110
