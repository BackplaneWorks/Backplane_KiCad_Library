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

"""Class definition for a geometric cruciform."""

from __future__ import annotations

from typing import Self

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.shapes.geom_polygon import GeomPolygon
from kilibs.geom.shapes.geom_rectangle import GeomRectangle
from kilibs.geom.shapes.geom_shape import GeomShapeClosed
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomCruciform(GeomShapeClosed):
    """A geometric cruciform."""

    def __init__(
        self,
        shape: GeomCruciform | None = None,
        overall_w: float | None = None,
        overall_h: float | None = None,
        tail_w: float | None = None,
        tail_h: float | None = None,
        center: Vec2DCompatible = (0, 0),
        angle: float = 0.0,
    ) -> None:
        """Create a geometric cruciform.

        A cruciform is a cross-shaped object that is basically two rectangles
        that intersect at their centers.

        It looks like this:

        .. aafig::
                +-------+   -------------
                |       |               ^
            +---+       +---+ ----      |
            |               |    ^      |
            |       o       |    | t h  | overall h
            |               |    v      |
            +---+       +---+ ----      |
                |       |               v
            |   +-------+   +------------
            |   |<-t w->|   |
            |               |
            |<- overall w ->|

        Args:
            shape: Shape from which to derive the parameters of the cruciform.
            overall_w: Overall width of the cruciform in mm.
            overall_h: Overall height of the cruciform in mm.
            tail_w: Width of the tail of the cruciform in mm.
            tail_h: Height of the tail of the cruciform in mm.
            center: Coordinates of the center point of the cruciform in mm.
            angle: Rotation angle of the cruciform in degrees.
        """

        # Instance attributes:
        self.overall_w: float
        """Overall width of the cruciform in mm."""
        self.overall_h: float
        """Overall height of the cruciform in mm."""
        self.tail_w: float
        """Width of the tail in mm."""
        self.tail_h: float
        """Height of the tail in mm."""
        self.center: Vector2D
        """Coordinates of the center in mm."""
        self.angle: float
        """Rotation angle of the shape in degrees."""
        self._shape: GeomPolygon | GeomRectangle | None
        """KiCad native shape that describes this cruciform."""

        if shape is not None:
            self.overall_w = shape.overall_w
            self.overall_h = shape.overall_h
            self.tail_w = shape.tail_w
            self.tail_h = shape.tail_h
            self.center = Vector2D(shape.center)
            self.angle = shape.angle
        elif (
            overall_w is not None
            and overall_h is not None
            and tail_w is not None
            and tail_h is not None
        ):
            self.overall_w = float(overall_w)
            self.overall_h = float(overall_h)
            self.tail_w = float(tail_w)
            self.tail_h = float(tail_h)
            self.center = Vector2D(center)
            self.angle = angle
            if overall_w < tail_w:
                raise ValueError("overall_w must be greater than tail_w")
            if overall_h < tail_h:
                raise ValueError("overall_h must be greater than tail_h")
        else:
            raise KeyError(
                "Either `shape` or `overall_w`, `overall_h`, `tail_w` and `tail_h` must be provided."
            )
        self._shape = None

    def get_shapes(self) -> list[GeomPolygon | GeomRectangle]:
        """Return a list of the shapes that this shape is composed of."""
        if self._shape:
            return [self._shape]
        if self.overall_w == self.tail_w or self.overall_h == self.tail_h:
            size = Vector2D(self.overall_w, self.overall_h)
            self._shape = GeomRectangle(
                center=self.center,
                size=size,
                angle=self.angle,
            )
        else:
            r1_size_2 = Vector2D(self.overall_w, self.tail_h) / 2
            r2_size_2 = Vector2D(self.tail_w, self.overall_h) / 2
            poly_pts = [
                Vector2D(-r1_size_2.x, -r1_size_2.y) + self.center,
                Vector2D(-r1_size_2.x, r1_size_2.y) + self.center,
                Vector2D(-r2_size_2.x, r1_size_2.y) + self.center,
                Vector2D(-r2_size_2.x, r2_size_2.y) + self.center,
                Vector2D(r2_size_2.x, r2_size_2.y) + self.center,
                Vector2D(r2_size_2.x, r1_size_2.y) + self.center,
                Vector2D(r1_size_2.x, r1_size_2.y) + self.center,
                Vector2D(r1_size_2.x, -r1_size_2.y) + self.center,
                Vector2D(r2_size_2.x, -r1_size_2.y) + self.center,
                Vector2D(r2_size_2.x, -r2_size_2.y) + self.center,
                Vector2D(-r2_size_2.x, -r2_size_2.y) + self.center,
                Vector2D(-r2_size_2.x, -r1_size_2.y) + self.center,
                Vector2D(-r1_size_2.x, -r1_size_2.y) + self.center,
            ]
            self._shape = GeomPolygon(shape=poly_pts)
            if self.angle:
                self._shape.rotate(angle=self.angle)
        return [self._shape]

    def translate(self, vector: Vector2D) -> Self:
        """Move the cruciform.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated cruciform.
        """
        self.center.translate(vector=vector)
        self._shape = None
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the cruciform around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated cruciform.
        """
        if angle:
            self.center.rotate(angle=angle, origin=origin)
            self._shape = None
        return self

    def inflate(self, amount: float, tol: float = TOL_MM) -> Self:
        """Increase or decrease the radius of the cruciform by 'amount'.

        Args:
            amount: The amount in mm by which the cruciform is inflated (when amount is
                positive) or deflated (when amount is negative).
            tol: Maximum negative dimension in mm that a segment of the shape is allowed
                to have after the deflation without causing a `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in segments with
                negative dimensions a `ValueError` is raised.

        Returns:
            The cruciform after the inflation/deflation.
        """
        if amount < 0 and -2 * amount > min(self.tail_h, self.tail_w) - tol:
            raise ValueError(f"Inflation by {amount} results in an invalid shape.")
        self.tail_h += 2 * amount
        self.tail_w += 2 * amount
        self.overall_h += 2 * amount
        self.overall_w += 2 * amount
        # More precise and faster to recalculate the shape than to inflate a polygon:
        self._shape = None
        return self

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the cruciform.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the cruciform, `False`
            otherwise.
        """
        if self.is_point_on_self(point=point, tol=tol):
            return not strictly_inside
        # We could defer to the `is_point_inside_self()`` function of GeomPolygon,
        # howerver, it is faster if we just check with 2 rectangles:
        rect1 = GeomRectangle(
            center=self.center,
            size=Vector2D(self.tail_w, self.overall_h),
            angle=self.angle,
        )
        if rect1.is_point_inside_self(
            point=point, strictly_inside=strictly_inside, tol=tol
        ):
            return True
        rect2 = GeomRectangle(
            center=self.center,
            size=Vector2D(self.overall_w, self.tail_h),
            angle=self.angle,
        )
        if rect2.is_point_inside_self(
            point=point, strictly_inside=strictly_inside, tol=tol
        ):
            return True
        return False

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the cruciform."""
        # Reimplementing stock `bbox()` method for performance gain.
        return self.get_shapes()[0].bbox()

    def __repr__(self) -> str:
        """Return the string representation of the cruciform."""
        return (
            f"GeomCruciform(center={self.center}, overall=({self.overall_w},"
            + f"{self.overall_h}), tail=({self.tail_w}, {self.tail_h}), angle="
            + f"{self.angle}"
        )
