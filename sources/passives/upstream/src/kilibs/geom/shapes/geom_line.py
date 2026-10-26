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

"""Class definition for a geometric line."""

from __future__ import annotations

from math import atan2, degrees, hypot
from typing import Self, cast

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.shapes.geom_shape import GeomShapeOpen
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomLine(GeomShapeOpen):
    """A geometric line."""

    def __init__(
        self,
        shape: GeomLine | None = None,
        start: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
    ) -> None:
        """Create a geometric line.

        Args:
            shape: Shape from which to derive the parameters of the line.
            start: Coordinates (in mm) of the start point of the line.
            end: Coordinates (in mm) of the end point of the line.
        """

        # Instance attributes:
        self.start: Vector2D
        """The coordinates of the start point in mm."""
        self.end: Vector2D
        """The coordinates of the start point in mm."""

        if shape is not None:
            self.start = shape.start.copy()
            self.end = shape.end.copy()
        elif start is not None and end is not None:
            self.start = Vector2D(start)
            self.end = Vector2D(end)
        else:
            raise KeyError("Either 'shape' or 'start' and 'end' must be provided.")

    @classmethod
    def from_vector2d(cls, start: Vector2D, end: Vector2D) -> GeomLine:
        """Create a geometric line from two points (given as Vector2D). This method is
        faster than the standard constructor, when one already has points in form of
        Vector2D.

        Args:
            start: Coordinates (in mm) of the start point of the line.
            end: Coordinates (in mm) of the end point of the line.
        """
        line = GeomLine.__new__(GeomLine)
        line.start = Vector2D.from_floats(start.x, start.y)
        line.end = Vector2D.from_floats(end.x, end.y)
        return line

    def copy(self) -> Self:
        """Create a deep copy of itself."""
        line = GeomLine.__new__(GeomLine)
        line.start = self.start.copy()
        line.end = self.end.copy()
        return cast(Self, line)

    def get_atomic_shapes(self) -> list[GeomLine]:
        """Return a list with itself in it since a line is an atomic shape."""
        return [self]

    def get_native_shapes(self) -> list[GeomLine]:
        """Return a list with itself in it since a line is a basic shape."""
        return [self]

    def translate(self, vector: Vector2D) -> Self:
        """Move the line.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated line.
        """
        self.start += vector
        self.end += vector
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the line around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated line.
        """
        self.start.rotate(angle=angle, origin=origin)
        self.end.rotate(angle=angle, origin=origin)
        return self

    def is_point_on_self(
        self,
        point: Vector2D,
        exclude_segment_ends: bool = False,
        tol: float = TOL_MM,
    ) -> bool:
        """Check if a point is on the line.

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: If `True`, then points within `tol` distance of the
                end points of the segment are not considered to be on the outline.
            tol : Distance in mm that the point is allowed to be away from the outline
                while still being considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the line segment within the given
            tolerance, `False` otherwise.
        """
        # Test if the points are on either the start or the end points of the line.
        # Note: the code is optimized for speed rather than readability. This is a
        # function that is called very frequently.
        e = self.end
        s = self.start
        se_x = e.x - s.x
        ps_x = s.x - point.x
        if abs(se_x) <= tol:
            # The line is vertical:
            if abs(ps_x) <= tol:
                if exclude_segment_ends:
                    return (s.y + tol < point.y < e.y - tol) or (
                        e.y + tol < point.y < s.y - tol
                    )
                else:
                    return (s.y - tol <= point.y <= e.y + tol) or (
                        e.y - tol <= point.y <= s.y + tol
                    )
            return False
        se_y = e.y - s.y
        ps_y = s.y - point.y
        if abs(se_y) <= tol:
            # The line is horizontal:
            if abs(ps_y) <= tol:
                if exclude_segment_ends:
                    return (s.x + tol < point.x < e.x - tol) or (
                        e.x + tol < point.x < s.x - tol
                    )
                else:
                    return (s.x - tol <= point.x <= e.x + tol) or (
                        e.x - tol <= point.x <= s.x + tol
                    )
            return False
        # The line is neither horizontal nor vertical:
        numerator = abs(se_x * ps_y - ps_x * se_y)
        seg_length = hypot(se_x, se_y)
        if numerator <= tol * seg_length:
            ps_length = hypot(ps_x, ps_y)
            pe_length = hypot(e.x - point.x, e.y - point.y)
            if seg_length + 2 * tol >= ps_length + pe_length:
                if exclude_segment_ends:
                    return not (point.is_equal(s, tol) or point.is_equal(e, tol))
                return True
        return False

    def is_point_on_self_accelerated(
        self,
        point: Vector2D,
        exclude_segment_ends: bool = False,
        tol: float = TOL_MM,
    ) -> bool:
        """Check if a point is on the segment while knowing it is a point on the line.
        This is typically used instead of `is_point_on_self()` after having established
        the intersection points of the (infinitely long) line with another object and
        wanting to check if the intersection point is also on the segment (i.e. between
        the start and the end point).

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: If `True`, then points within `tol` distance of the
                end points of the segment are not considered to be on the outline.
            tol : Distance in mm that the point is allowed to be away from the outline
                while still being considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the line segment within the given
            tolerance, `False` otherwise.
        """
        left = min(self.start.x, self.end.x)
        right = max(self.start.x, self.end.x)
        top = min(self.start.y, self.end.y)
        bottom = max(self.start.y, self.end.y)
        if (
            point.x < left - tol
            or point.x > right + tol
            or point.y < top - tol
            or point.y > bottom + tol
        ):
            return False
        else:
            if exclude_segment_ends:
                if point.is_equal(self.start, tol=tol):
                    return False
                if point.is_equal(self.end, tol=tol):
                    return False
            return True

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the line."""
        return BoundingBox(self.start, self.end)

    def is_equal(self, other: GeomLine, tol: float = TOL_MM) -> bool:
        """Return wheather two lines are identical or not.

        Args:
            other: The other line.
            tol: The maximum deviation in mm that a dimension is allowed to have to be
            still considered to be equal to the same dimension in the other line.

        Returns:
            `True` if the lines are equal, `False` otherwise.
        """
        if not self.start.is_equal(point=other.start, tol=tol):
            return False
        if not self.end.is_equal(point=other.end, tol=tol):
            return False
        return True

    def to_homogeneous(self) -> tuple[float, float, float]:
        """Return homogeneous representation of the line."""
        # What is being implemented is basically:
        # p1 = self.start.to_homogeneous()
        # p2 = self.end.to_homogeneous()
        # return p1.cross_product(p2)
        # However, to optimize for speed, it is implemented "manually":
        return (
            self.start.y - self.end.y,
            self.end.x - self.start.x,
            self.start.x * self.end.y - self.start.y * self.end.x,
        )

    def sort_points_relative_to_start(self, points: list[Vector2D]) -> list[Vector2D]:
        """Sort given points relative to start point.

        Args:
            points: The list of points to sort.

        Returns:
            The sorted list of points.
        """
        if len(points) and isinstance(points[0], list):
            points = [point.copy() for point in points]
        if len(points) < 2:
            return points

        dist_points = [(point.distance_to(self.start), point) for point in points]
        sorted_points: list[Vector2D] = []
        for _, point in sorted(dist_points):
            sorted_points.append(point)
        return sorted_points

    def reverse(self) -> GeomLine:
        """Reverse the line (start point becomes the end point and vice versa).

        Returns:
            The line after reversing it.
        """
        temp = self.start
        self.start = self.end
        self.end = temp
        return self

    @property
    def length(self) -> float:
        """The length of the line."""
        return (self.start - self.end).norm()

    @property
    def mid(self) -> Vector2D:
        """The mid point of the line."""
        # Note: this function is optimized for speed and therefore uses "manual"
        # implementations for this function:
        return Vector2D.from_floats(
            (self.start.x + self.end.x) / 2, (self.start.y + self.end.y) / 2
        )

    @property
    def direction(self) -> Vector2D:
        """The direction of the line."""
        return Vector2D.from_floats(
            self.end.x - self.start.x, self.end.y - self.start.y
        )

    @property
    def unit_direction(self) -> Vector2D:
        """The unit direction of the line."""
        return self.direction.normalize()

    @property
    def angle(self) -> float:
        """The unit direction of the line."""
        dir = self.direction
        return degrees(atan2(dir.y, dir.x))

    def __repr__(self) -> str:
        """The string representation of the line."""
        return f"GeomLine(start={self.start}, end={self.end})"
