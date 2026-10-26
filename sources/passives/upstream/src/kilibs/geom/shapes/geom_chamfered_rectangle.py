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

"""Class definition for a geometric chamfered rectangle."""

from __future__ import annotations

import math
from typing import Self

from kilibs.geom.corner_selection import CornerSelection
from kilibs.geom.shapes.geom_polygon import GeomPolygon
from kilibs.geom.shapes.geom_rectangle import GeomRectangle
from kilibs.geom.shapes.geom_shape import GeomShapeClosed
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomChamferedRectangle(GeomShapeClosed):
    """A geometric chamfered rectangle."""

    def __init__(
        self,
        shape: GeomChamferedRectangle | None = None,
        size: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        angle: float = 0.0,
        chamfer_size: float = 0.0,
        corners: CornerSelection | None = None,
    ) -> None:
        """Create a chamfered rectangle.

        Args:
            shape: Shape from which to derive the parameters of the chamfered rectangle.
            size: Width and height of the chamfered rectangle in mm.
            center: Coordinates of the center point of the chamfered rectangle in mm.
            angle: Rotation angle of the chamfered rectangle in degrees.
            chamfer_size: The size of the chamfer(s) in mm.
            corners: The corners to chamfer.
        """

        # Instance attributes:
        self.size: Vector2D
        """The size in mm."""
        self.center: Vector2D
        """The coordinates of the center in mm."""
        self.chamfer_size: float
        """The size of the chamfers in mm."""
        self.angle: float
        """The rotation angle of the shape."""
        self.corners: CornerSelection
        """The corners to chamfer."""
        self._shape: GeomPolygon | GeomRectangle | None
        """The shape of the chamfered rectangle."""

        if shape is not None:
            self.size = shape.size.copy()
            self.center = shape.center.copy()
            self.chamfer_size = shape.chamfer_size
            self.corners = shape.corners
            self.angle = shape.angle
            self._shape = None
        elif size is not None and center is not None and corners is not None:
            self.size = Vector2D(size)
            self.center = Vector2D(center)
            self.chamfer_size = chamfer_size
            if chamfer_size < 0:
                raise ValueError("chamfer_size must be >= 0.")
            self.corners = corners
            self.angle = angle
            self._shape = None
        else:
            raise KeyError(
                "Either `shape` or `size`, `center` and `corner` must be provided."
            )

    def _create_shape(self) -> GeomRectangle | GeomPolygon:
        pts: list[Vector2D] = []
        tl = self.center - self.size / 2
        br = self.center + self.size / 2
        shape: GeomRectangle | GeomPolygon
        if self.corners.is_any_selected():
            if self.corners.top_left:
                pts.append(Vector2D(tl.x + self.chamfer_size, tl.y))
            if self.corners.top_right:
                pts.append(Vector2D(br.x - self.chamfer_size, tl.y))
                pts.append(Vector2D(br.x, tl.y + self.chamfer_size))
            else:
                pts.append(Vector2D(br.x, tl.y))
            if self.corners.bottom_right:
                pts.append(Vector2D(br.x, br.y - self.chamfer_size))
                pts.append(Vector2D(br.x - self.chamfer_size, br.y))
            else:
                pts.append(br)
            if self.corners.bottom_left:
                pts.append(Vector2D(tl.x + self.chamfer_size, br.y))
                pts.append(Vector2D(tl.x, br.y - self.chamfer_size))
            else:
                pts.append(Vector2D(tl.x, br.y))
            if self.corners.top_left:
                pts.append(Vector2D(tl.x, tl.y + self.chamfer_size))
            else:
                pts.append(tl)
            shape = GeomPolygon(shape=pts)
            if self.angle:
                shape.rotate(self.angle, self.center)
        else:
            shape = GeomRectangle(center=self.center, size=self.size, angle=self.angle)
        return shape

    def get_shapes(self) -> list[GeomPolygon | GeomRectangle]:
        """Return a list containing the shapes that this shape is composed of in
        clockwise order.
        """
        if self._shape is None:
            self._shape = self._create_shape()
        return [self._shape]

    def translate(self, vector: Vector2D) -> Self:
        """Move the chamfered rectangle.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated chamfered rectangle.
        """
        self.center += vector
        self._shape = None
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the chamfered rectangle around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated chamfered rectangle.
        """
        if angle:
            self.center.rotate(angle=angle, origin=origin)
            self._shape = None
        return self

    def inflate(self, amount: float, tol: float = TOL_MM) -> Self:
        """Inflate or deflate the chamfered rectangle by 'amount'.

        Args:
            amount: The amount in mm by which the chamfered rectangle is inflated (when
                amount is positive) or deflated (when amount is negative).
            tol: Maximum negative dimension in mm that a segment of the chamfered rectangle
                is allowed to have after the deflation without raising a `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in segments with
                negative dimensions a `ValueError` is raised.

        Returns:
            The chamfered rectangle after the inflation/deflation.
        """
        min_dimension = min(self.size.x, self.size.y)
        if amount < 0 and -amount > min_dimension / 2 - tol:
            raise ValueError(f"Cannot deflate this shape by {amount}.")
        self.size += 2 * amount
        self.chamfer_size += amount * math.sqrt(2)
        if self.chamfer_size < 0.0:
            self.chamfer_size = 0.0
        self._shape = None
        return self

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the chamfered rectangle.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the chamfered rectangle, `False`
            otherwise.
        """
        if self._shape is None:
            self._shape = self._create_shape()
        return self._shape.is_point_inside_self(point, strictly_inside, tol)

    def __repr__(self) -> str:
        """Return the string representation of the chamfered rectangle."""
        return (
            f"ChamferedRectangle("
            f"center={self.center}, "
            f"size={self.size}, "
            f"chamfer_size={self.chamfer_size}, "
            f"angle={self.angle}"
        )
