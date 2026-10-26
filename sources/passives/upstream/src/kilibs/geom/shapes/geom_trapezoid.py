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

"""Class definition for a geometric trapezoid."""

from __future__ import annotations

import math
from typing import Self

from kilibs.geom.shapes.geom_arc import GeomArc
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_polygon import GeomPolygon
from kilibs.geom.shapes.geom_rectangle import GeomRectangle
from kilibs.geom.shapes.geom_round_rectangle import GeomRoundRectangle
from kilibs.geom.shapes.geom_shape import GeomShapeClosed
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomTrapezoid(GeomShapeClosed):
    """A geometric trapezoid."""

    def __init__(
        self,
        shape: GeomTrapezoid | None = None,
        size: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        corner_radius: float | None = None,
        side_angle: float | None = None,
        rotation_angle: float = 0.0,
    ) -> None:
        r"""Create a geometric isosceles trapezoid. That is a trapezoid with a symmetry
        axis. It has the option to round its corners.

        .. aafig::
            :rounded:

            angle<0
                  +---------------------+     ^
                 /                       \    |
                /            o            \  size.y
               /                           \  |
              +-----------------------------+ v
              <------------size.x----------->

        Args:
            shape: Shape from which to derive the parameters of the trapezoid.
            size: Width and height of the trapezoid in mm.
            center: Coordinates of the center point of the trapezoid in mm.
            start: Coordinates of the top left corner of the trapezoid in mm.
            corner_radius: Radius of the rounding of the corners in mm. Defaults to zero
                if `None`.
            side_angle: Angle as depicted in the figure above in degrees.
            rotation_angle: Rotation angle of the trapezoid in degrees.
        """

        # Instance attributes:
        self.size: Vector2D
        """The size in mm."""
        self.center: Vector2D
        """The coordinates of the center in mm."""
        self.corner_radius: float
        """The radius of the round corners in mm."""
        self.side_angle: float
        """The angle of the sides in degrees."""
        self.rotation_angle: float
        """The rotation angle of the shape."""
        self._shapes: list[
            GeomRectangle | GeomPolygon | GeomRoundRectangle | GeomArc | GeomLine
        ]
        """The list of the shapes the trapezoid is composed of."""

        if shape is not None:
            self.size = Vector2D(shape.size)
            self.center = Vector2D(shape.center)
            self.corner_radius = shape.corner_radius
            self.side_angle = shape.side_angle
            self.rotation_angle = shape.rotation_angle
        elif size is not None and side_angle is not None:
            self.size = Vector2D(size)
            if center is not None:
                self.center = Vector2D(center)
                assert start is None, "`start` and `center` cannot be used together."
            else:
                assert start is not None, "`start` or `center` must be provided."
                start = Vector2D(start)
                self.center = start + self.size / 2
            self.corner_radius = 0 if corner_radius is None else corner_radius
            if self.corner_radius < 0:
                raise ValueError("`corner_radius` must be >= 0.")
            self.side_angle = side_angle
            self.rotation_angle = rotation_angle
        else:
            raise KeyError(
                "Either `shape` or `size` and `start/center` must be provided."
            )
        self._shapes = []

    def get_shapes(
        self,
    ) -> list[GeomRectangle | GeomPolygon | GeomRoundRectangle | GeomArc | GeomLine]:
        """Return a list containing the atomic shapes that this shape is composed of in
        clockwise order."""
        if self._shapes:
            return self._shapes

        at = self.center - self.size / 2
        size = self.size
        aa = math.fabs(self.side_angle)

        dx = self.size.y * math.tan(math.radians(aa))
        cr = self.corner_radius

        if cr == 0:
            if self.side_angle == 0:
                self._shapes = [GeomRectangle(size=self.size, center=self.center)]
            elif self.side_angle < 0:
                corners = [
                    [at.x + dx, at.y],
                    [at.x + size.x - dx, at.y],
                    [at.x + size.x, at.y + size.y],
                    [at.x, at.y + size.y],
                ]
                self._shapes = [GeomPolygon(shape=corners)]
            elif self.side_angle > 0:
                corners = [
                    [at.x, at.y],
                    [at.x + size.x, at.y],
                    [at.x + size.x - dx, at.y + size.y],
                    [at.x + dx, at.y + size.y],
                ]
                self._shapes = [GeomPolygon(shape=corners)]
        else:
            dx = size[1] * math.tan(math.radians(aa))
            dx2 = cr * math.tan(math.radians((90 - aa) / 2))
            dx3 = cr / math.tan(math.radians((90 - aa) / 2))
            ds2 = cr * math.sin(math.radians(aa))
            dc2 = cr * math.cos(math.radians(aa))

            # fmt: off
            if self.side_angle == 0:
                self._shapes = [GeomRoundRectangle(size=size, start=at, corner_radius=cr)]

            elif self.side_angle < 0:
                ctl = Vector2D(at.x + dx + dx2,          at.y + cr)
                ctr = Vector2D(at.x + size.x - dx - dx2, at.y+cr)
                cbr = Vector2D(at.x + size.x - dx3,      at.y + size.y - cr)
                cbl = Vector2D(at.x + dx3,               at.y + size.y - cr)

                self._shapes = [
                    GeomArc(start=[ctl.x - dc2, ctl.y - ds2],   center=ctl,          angle=(90 - aa)),   # NOQA
                    GeomLine(start=[ctl.x, at.y],               end=[ctr.x, at.y]),
                    GeomArc(start=[ctr.x, at.y],                center=ctr,          angle=(90 - aa)),   # NOQA
                    GeomLine(start=[ctr.x + dc2, ctr.y - ds2],  end=[cbr.x + dc2, cbr.y - ds2]),         # NOQA
                    GeomArc(start=[cbr.x + dc2, cbr.y - ds2],   center=cbr,          angle=(90 + aa)),   # NOQA
                    GeomLine(start=[cbr.x, at.y + size.y],      end=[cbl.x, at.y + size.y]),             # NOQA
                    GeomArc(start=[cbl.x, at.y + size.y],       center=cbl,          angle=(90 + aa)),   # NOQA
                    GeomLine(start=[cbl.x - dc2, cbl.y - ds2],  end=[ctl.x - dc2, ctl.y - ds2]),         # NOQA
                ]
            else:
                ctl = Vector2D(at.x + dx3,               at.y + cr)
                ctr = Vector2D(at.x + size.x - dx3,      at.y + cr)
                cbr = Vector2D(at.x + size.x - dx - dx2, at.y + size.y - cr)
                cbl = Vector2D(at.x + dx + dx2,          at.y + size.y - cr)

                self._shapes = [
                    GeomArc(start=[ctl.x - dc2, ctl.y + ds2],   center=ctl,         angle=(90 + aa)),   # NOQA
                    GeomLine(start=[ctl.x, at.y],               end=[ctr.x, at.y]),
                    GeomArc(start=[ctr.x, at.y],                center=ctr,         angle=(90 + aa)),   # NOQA
                    GeomLine(start=[ctr.x + dc2, ctr.y + ds2],  end=[cbr.x + dc2, cbr.y + ds2]),        # NOQA
                    GeomArc(start=[cbr.x + dc2, cbr.y + ds2],   center=cbr,         angle=(90 - aa)),   # NOQA
                    GeomLine(start=[cbr.x, at.y + size.y],      end=[cbl.x, at.y + size.y]),            # NOQA
                    GeomArc(start=[cbl.x, at.y + size.y],       center=cbl,         angle=(90 - aa)),   # NOQA
                    GeomLine(start=[cbl.x - dc2, cbl.y + ds2],  end=[ctl.x - dc2, ctl.y + ds2]),        # NOQA
                ]
            # fmt: on

        if self.rotation_angle:
            for shape in self._shapes:
                shape.rotate(angle=self.rotation_angle, origin=self.center)
        return self._shapes

    def translate(self, vector: Vector2D) -> Self:
        """Move the trapezoid.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated trapezoid.
        """
        self.center += vector
        self._shapes = []
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the trapezoid around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated trapezoid.
        """
        if angle:
            self.center.rotate(angle=angle, origin=origin)
            self._shapes = []
        return self

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the trapezoid.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the trapezoid, `False`
            otherwise.
        """
        if self.is_point_on_self(point=point, tol=tol):
            return not strictly_inside
        # Check if the underlying shape is a simpler shape and if so use their method:
        if len(self._shapes) == 1 and isinstance(self._shapes[0], GeomShapeClosed):
            return self._shapes[0].is_point_inside_self(
                point=point, strictly_inside=strictly_inside, tol=tol
            )
        # Check if the point is inside the four circles of the trapezoid:
        for segment in self._shapes:
            if isinstance(segment, GeomArc):
                if (point - segment.center).norm() <= (self.corner_radius + tol):
                    return True
        # Check if the point is inside the polygon that is defined by all the line
        # segments:
        pts: list[Vector2D] = []
        for segment in self._shapes:
            if isinstance(segment, GeomLine | GeomArc):
                pts.append(segment.start)
        poly = GeomPolygon(shape=pts)
        # We have already checked if the point is on the outline (the first instruction
        # in this method). To accelerate the computation, we can set `strictly_inside`
        # to `False`.
        return poly.is_point_inside_self(point=point, strictly_inside=False, tol=tol)

    def inflate(self, amount: float, tol: float = TOL_MM) -> Self:
        """Inflate or deflate the trapezoid by 'amount'.

        Args:
            amount: The amount in mm by which the trapezoid is inflated (when amount is
                positive) or deflated (when amount is negative).
            tol: Maximum negative dimension in mm that a segment of the shape is allowed
                to have after the deflation without raising a `ValueError`.

        Returns:
            The trapezoid after the inflation/deflation.
        """
        if amount < 0:
            segment_lengths: list[float] = []
            for segment in self.get_atomic_shapes():
                if isinstance(segment, GeomLine):
                    segment_lengths.append(segment.length)
            min_dimension = min(segment_lengths)
            if -amount > min_dimension / 2 - tol:
                raise ValueError(f"Inflation by {amount} results in an invalid shape.")
        self.size.y += 2 * amount
        angle = math.radians(self.side_angle)
        self.size.x += 2 * (abs(math.tan(angle)) + 1 / abs(math.cos(angle))) * amount
        self._shapes = []
        return self

    def __repr__(self) -> str:
        """Return the string representation of the trapezoid."""
        return (
            f"GeomTrapezoid("
            f"center={self.center}, "
            f"size={self.size}, "
            f"corner_radius={self.corner_radius}, "
            f"side_angle={self.rotation_angle}, "
            f"rotation_angle={self.rotation_angle})"
        )
