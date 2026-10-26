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
# (C) 2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

import math

import pytest

from kilibs.geom import Vector2D


def test_init() -> None:
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = Vector2D((4, 5))
    assert p2.x == 4
    assert p2.y == 5

    p3 = Vector2D({"x": 7, "y": 8})
    assert p3.x == 7
    assert p3.y == 8

    p3_empty = Vector2D({})
    assert p3_empty.x == 0
    assert p3_empty.y == 0

    p4 = Vector2D(p1)
    assert p4.x == 1
    assert p4.y == 2

    p5 = Vector2D(1, 2)
    assert p5.x == 1
    assert p5.y == 2

    # Test float datatype
    p6 = Vector2D(1.2, 2.2)
    assert p6.x == 1.2
    assert p6.y == 2.2
    p7 = Vector2D((1.2, 2.2))
    assert p7.x == 1.2
    assert p7.y == 2.2
    p8 = Vector2D([1.2, 2.2])
    assert p8.x == 1.2
    assert p8.y == 2.2
    p9 = Vector2D({"x": 1.2, "y": 2.2})
    assert p9.x == 1.2
    assert p9.y == 2.2

    # Tests if int is always converted to float
    vectors = [
        Vector2D([1, 2]),
        Vector2D((4, 5)),
        Vector2D({"x": 7, "y": 8}),
        Vector2D({}),
        Vector2D(p1),
        Vector2D(1, 2),
    ]
    for vector in vectors:
        assert isinstance(vector.x, float)
        assert isinstance(vector.y, float)


def test_round_to() -> None:
    p1 = Vector2D([1.234, 5.678]).round_to(0)
    assert p1.is_equal(Vector2D(1.234, 5.678))

    p2 = Vector2D([1.234, 5.678]).round_to(0.1)
    assert p2.is_equal(Vector2D(1.2, 5.7))

    p3 = Vector2D([1.234, 5.678]).round_to(0.01)
    assert p3.is_equal(Vector2D(1.23, 5.68))

    p4 = Vector2D([1.234, 5.678]).round_to(0.001)
    assert p4.is_equal(Vector2D(1.234, 5.678))

    p5 = Vector2D([1.234, 5.678]).round_to(0.0001)
    assert p5.is_equal(Vector2D(1.234, 5.678))


def test_add() -> None:
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = p1 + 5
    assert p2.x == 6
    assert p2.y == 7

    p3 = p1 + (-5)
    assert p3.x == -4
    assert p3.y == -3

    p4 = p1 + [4, 2]
    assert p4.x == 5
    assert p4.y == 4

    p5 = p1 + [-5, -3]
    assert p5.x == -4
    assert p5.y == -1


def test_sub() -> None:
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = p1 - 5
    assert p2.x == -4
    assert p2.y == -3

    p3 = p1 - (-5)
    assert p3.x == 6
    assert p3.y == 7

    p4 = p1 - [4, 2]
    assert p4.x == -3
    assert p4.y == 0

    p5 = p1 - [-5, -3]
    assert p5.x == 6
    assert p5.y == 5


def test_mul() -> None:
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = p1 * 5
    assert p2.x == 5
    assert p2.y == 10

    p3 = p1 * (-5)
    assert p3.x == -5
    assert p3.y == -10

    p4 = p1 * [4, 5]
    assert p4.x == 4
    assert p4.y == 10

    p5 = p1 * [-5, -3]
    assert p5.x == -5
    assert p5.y == -6


def test_div() -> None:
    p1 = Vector2D([1, 2])
    assert p1.x == 1
    assert p1.y == 2

    p2 = p1 / 5
    assert p2.x == 0.2
    assert p2.y == 0.4

    p3 = p1 / (-5)
    assert p3.x == -0.2
    assert p3.y == -0.4

    p4 = p1 / [4, 5]
    assert p4.x == 0.25
    assert p4.y == 0.4

    p5 = p1 / [-5, -2]
    assert p5.x == -0.2
    assert p5.y == -1

    # Division by zero tests:
    with pytest.raises(ZeroDivisionError):
        p1 / 0.0
    with pytest.raises(ZeroDivisionError):
        p1 / 0
    with pytest.raises(ZeroDivisionError):
        p1 / [0, 0]
    with pytest.raises(ZeroDivisionError):
        p1 / (0, 0)


def test_polar() -> None:
    p1 = Vector2D.from_polar(math.sqrt(2), 45)
    assert p1.is_equal(Vector2D(1, 1))

    p1 = Vector2D.from_polar(2, -90, origin=(6, 1))
    assert p1.is_equal(Vector2D(6, -1))

    r, a = p1.to_polar(origin=(6, 1))
    assert r == pytest.approx(2)
    assert a == pytest.approx(-90)

    p1.rotate(90, origin=Vector2D(6, 1))
    assert p1.is_equal(Vector2D(8, 1))

    p1 = Vector2D.from_polar(math.sqrt(2), 135)
    assert p1.is_equal(Vector2D(-1, 1))

    p1.rotate(90, origin=Vector2D(0, 0))
    assert p1.is_equal(Vector2D(-1, -1))

    r, a = p1.to_polar()
    assert r == pytest.approx(math.sqrt(2))
    assert a == pytest.approx(-135)


def test_right_mul() -> None:
    p = 3 * Vector2D(1, 2)
    assert p.is_equal(Vector2D(3, 6))


def test_norm_arg() -> None:
    assert Vector2D(1, 1).norm() == pytest.approx(math.sqrt(2))
    assert Vector2D(1, 1).arg() == pytest.approx(45)
    assert Vector2D(-1, -1).arg() == pytest.approx(-135)


def test_inner_product() -> None:
    v1 = Vector2D(2, 3)
    v2 = Vector2D(4, 5)

    assert v1.dot_product(v2) == 23
    assert v2.dot_product(v1) == 23

    v2 = v1.orthogonal()
    assert v1.dot_product(v2) == 0
    assert v1.dot_product(-v2) == 0


def test_normalize() -> None:
    v = Vector2D(0, 0)
    with pytest.raises(ZeroDivisionError):
        n = Vector2D.normalize(v)

    v = Vector2D(math.sin(math.pi / 6), math.cos(math.pi / 6))
    n = Vector2D.normalize(v)
    assert n.norm() == 1

    n1 = Vector2D(1, 2).normalize()
    n2 = Vector2D(0.1, 0.2).normalize()
    assert n1.norm() == 1
    assert n2.norm() == 1
    assert (n1 - n2).norm() == pytest.approx(0)


def test_min_max() -> None:
    v1 = Vector2D(3, 2)
    v2 = Vector2D(1, 4)

    v = v1.max(v2)
    assert v.x == 3
    assert v.y == 4
    v = v2.max(v1)
    assert v.x == 3
    assert v.y == 4

    v = v1.min(v2)
    assert v.x == 1
    assert v.y == 2
    v = v2.min(v1)
    assert v.x == 1
    assert v.y == 2

    # check for iterables
    v = Vector2D.min((3, 2), (1, 4))
    assert v.x == 1
    assert v.y == 2


SQRT2 = math.sqrt(2)


@pytest.mark.parametrize(
    "v1, v2, exp",
    [
        ((0, 0), (0, 1), 1),
        ((0, 0), (1, 0), 1),
        ((0, 0), (1, 1), SQRT2),
    ],
)
def test_distance(v1, v2, exp):
    v1 = Vector2D(v1)
    v2 = Vector2D(v2)
    assert v1.distance_to(v2) == pytest.approx(exp)
    assert v2.distance_to(v1) == pytest.approx(exp)


@pytest.mark.parametrize(
    "v1, v2, exp",
    [
        ((0, 0),           (0, 0), True),
        ((0, 0.000000001), (0, 0), True),
        ((0, 0.1),         (0, 0), False),
        ((0.1, 0),         (0, 0), False),
    ],
)  # fmt: skip
def test_is_equal(v1, v2, exp):
    v1 = Vector2D(v1)
    v2 = Vector2D(v2)

    assert v1.is_equal(v2) == exp
    assert v2.is_equal(v1) == exp
