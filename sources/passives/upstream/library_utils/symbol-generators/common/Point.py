# KiCadSymbolGenerator ia part of the kicad-library-utils script collection.
# It is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KiCadSymbolGenerator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-library-utils. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2017 by Rene Poeschl

import math
from copy import copy
from typing import Optional


class Point:
    def __init__(
        self,
        coordinates=None,
        y=None,
        grid: Optional[float] = None,
        distance: Optional[float] = None,
        angle: Optional[float] = None,
    ):
        if distance is not None and angle is not None:
            angle = math.radians(angle)
            self.x: int = int(round(distance * math.cos(angle)))
            self.y: int = int(round(distance * math.sin(angle)))
        elif coordinates is None:
            self.x: int = 0
            self.y: int = 0
        elif type(coordinates) in [int, float]:
            if y is not None:
                self.x: int = int(coordinates)
                self.y: int = int(y)
            else:
                raise TypeError("you have to give x and y coordinates")

        elif isinstance(coordinates, Point):
            self.x: int = coordinates.x
            self.y: int = coordinates.y

        elif type(coordinates) is dict:
            self.x: int = int(coordinates.get("x", 0))
            self.y: int = int(coordinates.get("y", 0))
        else:
            TypeError(
                "unsupported type, Must be dict, point or coordinates given as number"
            )

        self.grid = grid
        if grid is not None:
            self.roundToGrid()

    def rotate(self, angle, origin={"x": 0, "y": 0}, **kwargs):
        point = self if not kwargs.get("apply_on_copy", False) else copy(self)
        point.grid = kwargs.get("new_grid", point.grid)

        op = Point(origin)

        angle = math.radians(angle)

        temp = int(
            op.x
            + math.cos(angle) * (point.x - op.x)
            - math.sin(angle) * (point.y - op.y)
        )
        point.y = int(
            op.y
            + math.sin(angle) * (point.x - op.x)
            + math.cos(angle) * (point.y - op.y)
        )
        point.x = temp

        if point.grid is not None:
            point.roundToGrid()
        return point

    def translate(self, distance, **kwargs):
        point = self if not kwargs.get("apply_on_copy", False) else copy(self)
        point.grid = kwargs.get("new_grid", point.grid)

        dist = Point(distance)
        point.x += dist.x
        point.y += dist.y
        if point.grid is not None:
            point.roundToGrid()
        return point

    def mirrorHorizontal(self, **kwargs) -> "Point":
        point = self if not kwargs.get("apply_on_copy", False) else copy(self)
        point.grid = kwargs.get("new_grid", point.grid)

        point.x = -point.x
        if point.grid is not None:
            point.roundToGrid()
        return point

    def mirrorVertical(self, **kwargs) -> "Point":
        point = self if not kwargs.get("apply_on_copy", False) else copy(self)
        point.grid = kwargs.get("new_grid", point.grid)

        point.y = -point.y
        if point.grid is not None:
            point.roundToGrid()
        return point

    @staticmethod
    def roundCoordinateToGrid(value: float, base: int, apply_on_copy: bool = False):
        if value >= 0:
            return math.floor(value / base) * base
        return math.ceil(value / base) * base

    def roundToGrid(self, base: Optional[float] = None):
        if base is None:
            base = self.grid

        if base is None:
            return

        self.x = Point.roundCoordinateToGrid(self.x, base)
        self.y = Point.roundCoordinateToGrid(self.y, base)

    def __repr__(self) -> str:
        return "Point ({x:d}, {y:d})".format(x=int(self.x), y=int(self.y))

    def __str__(self) -> str:
        return "{x:d} {y:d}".format(x=int(self.x), y=int(self.y))

    def __format__(self, format: str) -> str:
        if format == "s":
            return str(self)
        elif format == "r":
            return repr(self)

    def __eq__(self, other) -> bool:
        """Overrides the default implementation"""

        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False
