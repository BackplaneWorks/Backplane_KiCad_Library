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
# (C) 2016-2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

import pytest

from kilibs.geom import Vector3D


def test_init() -> None:
    p1 = Vector3D([1, 2, 3])
    assert p1.x == 1
    assert p1.y == 2
    assert p1.z == 3

    p1_xy = Vector3D([1, 2])
    assert p1_xy.x == 1
    assert p1_xy.y == 2
    assert p1_xy.z == 0

    p2 = Vector3D((4, 5, 6))
    assert p2.x == 4
    assert p2.y == 5
    assert p2.z == 6

    p2_xy = Vector3D((4, 5))
    assert p2_xy.x == 4
    assert p2_xy.y == 5
    assert p2_xy.z == 0

    p3 = Vector3D({"x": 7, "y": 8, "z": 9})
    assert p3.x == 7
    assert p3.y == 8
    assert p3.z == 9

    p3_xy = Vector3D({"x": 7, "y": 8})
    assert p3_xy.x == 7
    assert p3_xy.y == 8
    assert p3_xy.z == 0

    p3_empty = Vector3D({})
    assert p3_empty.x == 0
    assert p3_empty.y == 0
    assert p3_empty.z == 0

    p4 = Vector3D(p1)
    assert p4.x == 1
    assert p4.y == 2
    assert p4.z == 3

    p5 = Vector3D(1, 2, 3)
    assert p5.x == 1
    assert p5.y == 2
    assert p5.z == 3

    p5_xy = Vector3D(1, 2)
    assert p5_xy.x == 1
    assert p5_xy.y == 2
    assert p5_xy.z == 0

    # TODO: test float datatype
    # TODO: invalid type tests
    # TODO: tests if int is always converted to float


def test_round_to() -> None:
    p1 = Vector3D([1.234, 5.678, 9.012]).round_to(0)
    assert p1.x == pytest.approx(1.234)
    assert p1.y == pytest.approx(5.678)
    assert p1.z == pytest.approx(9.012)

    p2 = Vector3D([1.234, 5.678, 9.012]).round_to(0.1)
    assert p2.x == pytest.approx(1.2)
    assert p2.y == pytest.approx(5.7)
    assert p2.z == pytest.approx(9)

    p3 = Vector3D([1.234, 5.678, 9.012]).round_to(0.01)
    assert p3.x == pytest.approx(1.23)
    assert p3.y == pytest.approx(5.68)
    assert p3.z == pytest.approx(9.01)

    p4 = Vector3D([1.234, 5.678, 9.012]).round_to(0.001)
    assert p4.x == pytest.approx(1.234)
    assert p4.y == pytest.approx(5.678)
    assert p4.z == pytest.approx(9.012)

    p5 = Vector3D([1.234, 5.678, 9.012]).round_to(0.0001)
    assert p5.x == pytest.approx(1.234)
    assert p5.y == pytest.approx(5.678)
    assert p5.z == pytest.approx(9.012)


def test_add() -> None:
    p1 = Vector3D([1, 2, 3])
    assert p1.x == 1
    assert p1.y == 2
    assert p1.z == 3

    p2 = p1 + 5
    assert p2.x == 6
    assert p2.y == 7
    assert p2.z == 8

    p3 = p1 + (-5)
    assert p3.x == -4
    assert p3.y == -3
    assert p3.z == -2

    p4 = p1 + [4, 2, -2]
    assert p4.x == 5
    assert p4.y == 4
    assert p4.z == 1

    p5 = p1 + [-5, -3]
    assert p5.x == -4
    assert p5.y == -1
    assert p5.z == 3

    # TODO: invalid type tests


def test_sub() -> None:
    p1 = Vector3D([1, 2, 3])
    assert p1.x == 1
    assert p1.y == 2
    assert p1.z == 3

    p2 = p1 - 5
    assert p2.x == -4
    assert p2.y == -3
    assert p2.z == -2

    p3 = p1 - (-5)
    assert p3.x == 6
    assert p3.y == 7
    assert p3.z == 8

    p4 = p1 - [4, 2, -2]
    assert p4.x == -3
    assert p4.y == 0
    assert p4.z == 5

    p5 = p1 - [-5, -3]
    assert p5.x == 6
    assert p5.y == 5
    assert p5.z == 3

    # TODO: invalid type tests


def test_mul() -> None:
    p1 = Vector3D([1, 2, 3])
    assert p1.x == 1
    assert p1.y == 2
    assert p1.z == 3

    p2 = p1 * 5
    assert p2.x == 5
    assert p2.y == 10
    assert p2.z == 15

    p3 = p1 * (-5)
    assert p3.x == -5
    assert p3.y == -10
    assert p3.z == -15

    p4 = p1 * [4, 5, -2]
    assert p4.x == 4
    assert p4.y == 10
    assert p4.z == -6

    p5 = p1 * [-5, -3]
    assert p5.x == -5
    assert p5.y == -6
    assert p5.z == 0

    # TODO: invalid type tests


def test_div() -> None:
    p1 = Vector3D([1, 2, 3])
    assert p1.x == 1
    assert p1.y == 2
    assert p1.z == 3

    p2 = p1 / 5
    assert p2.x == 0.2
    assert p2.y == 0.4
    assert p2.z == 0.6

    p3 = p1 / (-5)
    assert p3.x == -0.2
    assert p3.y == -0.4
    assert p3.z == -0.6

    p4 = p1 / [4, 5, -2]
    assert p4.x == 0.25
    assert p4.y == 0.4
    assert p4.z == -1.5

    # TODO: division by zero tests
    # TODO: invalid type tests
