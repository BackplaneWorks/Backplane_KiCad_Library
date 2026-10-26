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

"""Class definition for a geometric cross."""

from __future__ import annotations

from typing import Self

from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_shape import GeomShapeOpen
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomCross(GeomShapeOpen):
    """A geometric cross."""

    def __init__(
        self,
        shape: GeomCross | None = None,
        center: Vec2DCompatible | None = None,
        size: Vec2DCompatible | float | None = None,
        angle: float = 0.0,
    ) -> None:
        """Create a geometric cross.

        Args:
            shape: Shape from which to derive the parameters of the cross.
            center: Coordinates (in mm) of the center point of the cross.
            size: Size in mm of the cross.
            angle: Angle of the cross in degrees.
        """

        # Instance attributes:
        self.center: Vector2D
        """The coordinates of the center in mm."""
        self.size: Vector2D
        """The size in mm."""
        self.angle: float
        """The rotation angle."""
        self._shapes: list[GeomLine]
        """KiCad native shape that describes this cross."""

        if shape is not None:
            self.center = Vector2D(shape.center)
            self.size = Vector2D(shape.size)
            self.angle = shape.angle
        elif center is not None and size is not None:
            self.center = Vector2D(center)
            if isinstance(size, float):
                self.size = Vector2D(size, size)
            else:
                self.size = Vector2D(size)
            self.angle = angle
        else:
            raise KeyError("Either 'shape' or 'center' and 'size' must be provided.")
        self._shapes = []

    def get_shapes(self) -> list[GeomLine]:
        """Return a list containing the two lines of the cross."""
        if self._shapes:
            return self._shapes
        points = [
            Vector2D(-self.size.x / 2, 0),
            Vector2D(self.size.x / 2, 0),
            Vector2D(0, -self.size.y / 2),
            Vector2D(0, self.size.y / 2),
        ]
        points = [
            p.rotated(self.angle, origin=self.center) + self.center for p in points
        ]
        self._shapes = [
            GeomLine(start=points[0], end=points[1]),
            GeomLine(start=points[2], end=points[3]),
        ]
        return self._shapes

    def translate(self, vector: Vector2D) -> Self:
        """Move the cross.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated cross.
        """
        self.center += vector
        self._shapes = []
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the cross around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated cross.
        """
        if angle:
            self.center.rotate(angle=angle, origin=origin)
            self._shapes = []
        return self

    def __repr__(self) -> str:
        return f"GeomCross(center={self.center}, size={self.size}, angle={self.angle})"
