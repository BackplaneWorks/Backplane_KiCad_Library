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

"""Class definition for a geometric circle."""

from __future__ import annotations

import math
from typing import Self

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.shapes.geom_arc import GeomArc
from kilibs.geom.shapes.geom_shape import GeomShapeClosed
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomCircle(GeomShapeClosed):
    """A geometric circle."""

    def __init__(
        self,
        shape: GeomCircle | GeomArc | None = None,
        center: Vec2DCompatible | None = None,
        radius: float | None = None,
    ) -> None:
        """Create a geometric circle.

        Args:
            shape: Shape from which to derive the parameters.
            center: Coordinates (in mm) of the center of the circle.
            radius: Radius of the circle in mm.
        """

        # Instance attributes:
        self.center: Vector2D
        """The coordinates of the center in mm."""
        self.radius: float
        """The radius in mm."""

        if shape is not None:
            self.center = Vector2D(shape.center)
            self.radius = float(shape.radius)
        elif center is not None and radius is not None:
            self.center = Vector2D(center)
            self.radius = abs(float(radius))
        else:
            raise KeyError("Either 'shape' or 'center' and 'radius' must be provided.")

    def get_atomic_shapes(self) -> list[GeomCircle]:
        """Return a list with itself in it since a line is an atomic shape."""
        return [self]

    def get_native_shapes(self) -> list[GeomCircle]:
        """Return a list with itself in it since a line is a basic shape."""
        return [self]

    def translate(self, vector: Vector2D) -> Self:
        """Move the circle.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated circle.
        """
        self.center += vector
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the circle around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated circle.
        """
        if angle:
            self.center.rotate(angle=angle, origin=origin)
        return self

    def inflate(self, amount: float, tol: float = TOL_MM) -> Self:
        """Inflate (or deflate) the circle by 'amount'.

        Args:
            amount: The amount in mm by which the circle is inflated (when amount is
                positive) or deflated (when amount is negative).
            tol: Minimum radius that a circle is allowed to have without raising a
                `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in a radius with
                negative value a `ValueError` is raised.

        Returns:
            The circle after the inflation/deflation.
        """
        if amount < 0 and -amount > self.radius - tol:
            raise ValueError(f"Cannot deflate this circle by {amount}.")
        self.radius += amount
        return self

    def is_point_on_self(
        self, point: Vector2D, exclude_segment_ends: bool = False, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on the circle's outline.

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: Parameter has no impact. It is ther for compatibility
                with the `is_point_on_self()` method of the other shapes.
            tol: Distance in mm that the point is allowed to be away from the outline
                and still be considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the circle within the given
            tolerance, `False` otherwise.
        """
        radius = math.hypot(point.x - self.center.x, point.y - self.center.y)
        return abs(self.radius - radius) <= tol

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the circle.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the circle, `False`
            otherwise.
        """
        point_to_center = (point - self.center).norm()
        if strictly_inside:
            return point_to_center < self.radius - tol
        else:
            return point_to_center <= self.radius + tol

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the circle."""
        center = self.center
        radius = self.radius
        return BoundingBox(
            Vector2D.from_floats(center.x - radius, center.y - radius),
            Vector2D.from_floats(center.x + radius, center.y + radius),
        )

    def is_equal(self, other: GeomCircle, tol: float = TOL_MM) -> bool:
        """Return wheather two circles are identical or not.

        Args:
            other: The other circle.
            tol: The maximum deviation in mm that a dimension is allowed to have to be
            still considered to be equal to the same dimension in the other circle.

        Returns:
            `True` if the circles are equal, `False` otherwise.
        """
        if abs(self.radius - other.radius) > tol:
            return False
        if not self.center.is_equal(point=other.center, tol=tol):
            return False
        return True

    @property
    def mid(self) -> Vector2D:
        """Return the midpoint on the outline of the circle (assuming it was an arc
        starting at angle=0).

        This definition seems a bit weird, but is needed to determine if the circle is
        inside or outside of another shape (typically for keepout).
        """
        return self.center + Vector2D.from_floats(self.radius, 0.0)

    @property
    def length(self) -> float:
        """The circumference of the circle (or the length of the 360° arc segment)."""
        return 2 * math.pi * self.radius

    def __repr__(self) -> str:
        """Return the string representation of the circle."""
        return f"GeomCircle(center={self.center}, radius={self.radius})"
