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

"""Class definition for a geometric round rectangle."""

from __future__ import annotations

from typing import Self

from kilibs.geom.shapes.geom_arc import GeomArc
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_rectangle import GeomRectangle
from kilibs.geom.shapes.geom_shape import GeomShapeClosed
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomRoundRectangle(GeomShapeClosed):
    """A geometric rectangle with rounded corners."""

    def __init__(
        self,
        shape: GeomRoundRectangle | None = None,
        size: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        corner_radius: float | None = None,
        angle: float = 0.0,
    ) -> None:
        r"""Create a geometric round rectangle. That is a rectangle with all four
        corners rounded:

        .. aafig::
            :rounded:

              /--------\
              |        |
              |        |
              |        |
              |        |
              |        |
              \--------/

        Args:
            shape: Shape from which to derive the parameters of the round rectangle.
            size: Width and height of the roundrect in mm.
            center: Coordinates of the center point of the round rectangle in mm.
            start: Coordinates of the first corner of the (round) rectangle in mm.
            corner_radius: Radius of the rounding of the corners in mm.
            angle: Rotation angle of the round rectangle in degrees.
        """

        # Instance attributes:
        self.size: Vector2D
        """The size in mm."""
        self.center: Vector2D
        """The coordinates of the center in mm."""
        self.corner_radius: float
        """The radius of the round corners in mm."""
        self.angle: float
        """The rotation angle of the shape."""
        self._shapes: list[GeomLine | GeomArc | GeomRectangle]
        """The list of the shapes the rounded rectangle is composed of."""

        if shape is not None:
            self.size = Vector2D(shape.size)
            self.center = Vector2D(shape.center)
            self.corner_radius = shape.corner_radius
            self.angle = shape.angle
        elif size is not None and corner_radius is not None:
            self.size = Vector2D(size)
            self.corner_radius = corner_radius
            if corner_radius < 0:
                raise ValueError("Corner_radius must be >= 0.")
            self.angle = angle
            if center is not None:
                self.center = Vector2D(center)
            elif start is not None:
                self.center = Vector2D(start) + self.size / 2
            else:
                raise KeyError("You must provide either `start` or `center`.")
        else:
            raise KeyError(
                "Either `shape` or `size`, `corner_radius` and `start/center` must be provided."
            )
        self._shapes = []

    def get_shapes(self) -> list[GeomLine | GeomArc | GeomRectangle]:
        """Return a list containing the shapes that this shape is composed of in clockwise order."""
        if self._shapes:
            return self._shapes
        cr = self.corner_radius
        size = self.size
        at = self.center - self.size / 2
        self._shapes = []
        if self.corner_radius == 0:
            self._shapes = [GeomRectangle(start=at, end=[at.x + size.x, at.y + size.y])]
        else:
            # fmt: off
            self._shapes = [
                GeomLine(start=[at.x + cr, at.y],                   end=[at.x + size.x - cr, at.y]),                                # NOQA
                GeomArc(start=[at.x + size.x - cr, at.y],           center=[at.x + size.x - cr, at.y + cr],             angle=90),  # NOQA
                GeomLine(start=[at.x + size.x, at.y + cr],          end=[at.x + size.x, at.y + size.y - cr]),                       # NOQA
                GeomArc(start=[at.x + size.x, at.y + size.y - cr],  center=[at.x + size.x - cr, at.y + size.y - cr],    angle=90),  # NOQA
                GeomLine(start=[at.x + size.x - cr, at.y + size.y], end=[at.x + cr, at.y + size.y]),                                # NOQA
                GeomArc(start=[at.x + cr, at.y + size.y],           center=[at.x + cr, at.y + size.y - cr],             angle=90),  # NOQA
                GeomLine(start=[at.x, at.y + size.y - cr],          end=[at.x, at.y + cr]),                                         # NOQA
                GeomArc(start=[at.x, at.y + cr],                    center=[at.x + cr, at.y + cr],                      angle=90),  # NOQA
            ]
            # fmt: on
            if self.angle:
                for child in self._shapes:
                    child.rotate(angle=self.angle, origin=self.center)
        return self._shapes

    def translate(self, vector: Vector2D) -> Self:
        """Move the round rectangle.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated round rectangle.
        """
        self.center += vector
        self._shapes = []
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the round rectangle around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated round rectangle.
        """
        if angle:
            self.center.rotate(angle=angle, origin=origin)
            self._shapes = []
        return self

    def inflate(self, amount: float, tol: float = TOL_MM) -> Self:
        """Inflate or deflate the round rectangle by 'amount'.

        Args:
            amount: The amount in mm by which the round rectangle is inflated (when
                amount is positive) or deflated (when amount is negative).
            tol: Maximum negative dimension in mm that a segment of the round rectangle
                is allowed to have after the deflation without raising a `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in segments with
                negative dimensions a `ValueError` is raised.

        Returns:
            The round rectangle after the inflation/deflation.
        """
        min_dimension = min(self.size.x, self.size.y)
        if amount < 0 and -amount > min_dimension / 2 - tol:
            raise ValueError(f"Cannot deflate this shape by {amount}.")
        self.size += 2 * amount
        self.corner_radius += amount
        if self.corner_radius < 0:
            self.corner_radius = 0
        self._shapes = []
        return self

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the round rectangle.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the round rectangle, `False`
            otherwise.
        """
        shapes = self.get_shapes()
        if self.is_point_on_self(point=point, tol=tol):
            return not strictly_inside
        if isinstance(shapes[0], GeomRectangle):
            return shapes[0].is_point_inside_self(
                point=point, strictly_inside=strictly_inside, tol=tol
            )
        # Check if the point is inside the four circles of the round rectangle:
        for segment in shapes:
            if isinstance(segment, GeomArc):
                if (point - segment.center).norm() <= (self.corner_radius + tol):
                    return True
        # Check if the point is in the two rectangles that can be formed when cutting
        # off the rounded sides:
        rect1 = GeomRectangle(
            center=self.center,
            size=Vector2D(self.size.x, self.size.y - 2 * self.corner_radius),
            angle=self.angle,
        )
        if rect1.is_point_inside_self(
            point=point, strictly_inside=strictly_inside, tol=tol
        ):
            return True
        rect2 = GeomRectangle(
            center=self.center,
            size=Vector2D(self.size.x - 2 * self.corner_radius, self.size.y),
            angle=self.angle,
        )
        if rect2.is_point_inside_self(
            point=point, strictly_inside=strictly_inside, tol=tol
        ):
            return True
        return False

    def __repr__(self) -> str:
        """Return the string representation of the round rectangle."""
        return (
            f"GeomRoundRectangle("
            f"center={self.center}, "
            f"size={self.size}, "
            f"corner_radius={self.corner_radius}, "
            f"angle={self.angle}"
        )
