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

"""Class definition for a geometric rectangle."""

from __future__ import annotations

from typing import Self

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_shape import GeomShapeClosed
from kilibs.geom.tolerances import TOL_MM, tol_deg
from kilibs.geom.vector import Vec2DCompatible, Vector2D

# import kilibs.geom.operations.rounding  # imported inside the code


class GeomRectangle(GeomShapeClosed):
    """A geometric rectangle with rounded corners."""

    def __init__(
        self,
        shape: GeomRectangle | BoundingBox | None = None,
        center: Vec2DCompatible | None = None,
        size: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
        angle: float = 0.0,
    ) -> None:
        """Create a geometric rectangle.

        Args:
            shape: Shape from which to derive the parameters of the rectangle.
            center: Coordinates (in mm) of the center point of the rectangle.
            size: Size in mm of the rectangle.
            start: Coordinates (in mm) of the top left corner of the rectangle.
            stop: Coordinates (in mm) of the bottom right corner of the rectangle.
            angle: Rotation angle of the rectangle in degrees.
        """

        # Instance attributes:
        self.size: Vector2D
        """The size in mm."""
        self.center: Vector2D
        """The coordinates of the center in mm."""
        self.corner_radius: float
        """The radius of the round corners in mm."""
        self._angle: float
        """The rotation angle of the shape."""
        self._corner_pts: list[Vector2D] | None
        """The corners of the rectangle."""
        self._bbox: BoundingBox | None
        """The bounding box of the rectangle."""

        self._corner_pts = None
        self._bbox = None
        self._update_angle(angle)
        if center is not None and size is not None:
            self.center = Vector2D(center)
            self.size = Vector2D(size).positive()
        elif shape is not None:
            self.center = shape.center.copy()
            self.size = shape.size.copy()
            if isinstance(shape, GeomRectangle):
                self._angle = shape._angle
                self._bbox = shape._bbox.copy() if shape._bbox else None
                if shape._corner_pts:
                    self._corner_pts = [p.copy() for p in shape._corner_pts]
                else:
                    self._corner_pts = None
        elif start is not None:
            start = Vector2D(start)
            if end is not None:
                end = Vector2D(end)
                self.center = (start + end) / 2
                self.size = (end - start).positive()
            if size is not None:
                self.size = Vector2D(size)
                self.center = start + self.size / 2
                self.size = self.size.positive()
        else:
            raise KeyError(
                "Either 'center' and 'size', 'shape', 'start' and 'end',"
                " or 'start' and 'size' need to be provided."
            )

    def get_atomic_shapes(self) -> list[GeomLine]:
        """Return the four lines of the rectangle in clockwise order."""
        c = self.points
        return [
            GeomLine.from_vector2d(start=c[i], end=c[(i + 1) % 4])
            for i in range(len(c))
        ]

    def get_native_shapes(self) -> list[GeomRectangle]:
        """Return a list with itself in it."""
        return [self]

    def translate(self, vector: Vector2D) -> Self:
        """Move the rectangle.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated rectangle.
        """
        self.center += vector
        self._corner_pts = None
        self._bbox = None
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the rectangle around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated rectangle.
        """
        if angle:
            self.center.rotate(angle=angle, origin=origin)
            self._update_angle(angle + self.angle)
            self._corner_pts = None
            self._bbox = None
        return self

    def inflate(self, amount: float, tol: float = TOL_MM) -> Self:
        """Inflate (or deflate) the rectangle by 'amount'.

        Args:
            amount: The amount in mm by which the rectangle is inflated (when amount is
                positive) or deflated (when amount is negative).
            tol: Minimum dimension that a rectangle is allowed to have without raising a
                `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in a radius with
                negative value a `ValueError` is raised.

        Returns:
            The rectangle after the inflation/deflation.
        """
        min_dimension = min(self.size.x, self.size.y)
        if amount < 0 and -amount > min_dimension / 2 - tol:
            raise ValueError(f"Cannot deflate this rectangle by {amount}.")
        self.size += 2 * amount
        self._corner_pts = None
        self._bbox = None
        return self

    def is_point_on_self(
        self,
        point: Vector2D,
        exclude_segment_ends: bool = False,
        tol: float = TOL_MM,
    ) -> bool:
        """Check if a point is on the rectangle outline.

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: If `True`, then points within `tol` distance of the
                end points of the segments (corners of the rectangle) are not considered
                to be on the outline.
            tol: Distance in mm that the point is allowed to be away from the outline
                and still be considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the rectangle within the given
            tolerance, `False` otherwise.
        """
        for line in self.get_atomic_shapes():
            if line.is_point_on_self(
                point=point, exclude_segment_ends=exclude_segment_ends, tol=tol
            ):
                return True
        return False

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the rectangle.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the rectangle, `False`
            otherwise.
        """
        if not self.angle:
            if strictly_inside:
                if (
                    point.x > self.left + tol
                    and point.x < self.right - tol
                    and point.y > self.top + tol
                    and point.y < self.bottom - tol
                ):
                    return True
            else:
                if (
                    point.x >= self.left - tol
                    and point.x <= self.right + tol
                    and point.y >= self.top - tol
                    and point.y <= self.bottom + tol
                ):
                    return True
            return False
        else:
            # Check if the given point is always on the right side of its lines when the
            # lines are defining the rectangle in clockwise direction.
            lines = self.get_atomic_shapes()
            for line in lines:
                # check if the point is on the line
                if line.is_point_on_self(
                    point=point, exclude_segment_ends=False, tol=tol
                ):
                    return not strictly_inside
                cp = line.direction.cross_product(point - line.start)
                if cp.z < 0:
                    return False
            return True

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the rectangle."""
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox

    def round_to_grid(self, grid: float, outwards: bool = True) -> Self:
        """Round the rectangle to the given grid.

        Args:
            grid: The grid to which the rounding is made.
            outwards: True if the rectangle points shall be rounded outwards, i.e.
                away from the crectangle center, thus potentially increasing the area.
        """
        import kilibs.geom.operations.rounding as rounding

        pts = self.points
        if not outwards:
            for pt in pts:
                # TODO: change from rounding inwards to rounding to nearest again.
                # pt.x = rounding.round_to_grid_nearest(pt.x, grid)
                # pt.y = rounding.round_to_grid_nearest(pt.y, grid)
                epsilon = 0  # TOL_MM  # epsilong = grid/100 is a good alternative
                if abs(pt.x - self.center.x) < epsilon:
                    pt.x = rounding.round_to_grid_nearest(pt.x, grid)
                elif pt.x > self.center.x:
                    pt.x = rounding.round_to_grid_down(pt.x, grid, epsilon)
                else:
                    pt.x = rounding.round_to_grid_up(pt.x, grid, epsilon)
                if abs(pt.y - self.center.y) < epsilon:
                    pt.y = rounding.round_to_grid_nearest(pt.y, grid)
                elif pt.y > self.center.y:
                    pt.y = rounding.round_to_grid_down(pt.y, grid, epsilon)
                else:
                    pt.y = rounding.round_to_grid_up(pt.y, grid, epsilon)
        else:
            epsilon = 0  # TOL_MM  # epsilong = grid/100 is a good alternative
            for pt in pts:
                if abs(pt.x - self.center.x) < epsilon:
                    pt.x = rounding.round_to_grid_nearest(pt.x, grid)
                elif pt.x > self.center.x:
                    pt.x = rounding.round_to_grid_up(pt.x, grid, epsilon)
                else:
                    pt.x = rounding.round_to_grid_down(pt.x, grid, epsilon)
                if abs(pt.y - self.center.y) < epsilon:
                    pt.y = rounding.round_to_grid_nearest(pt.y, grid)
                elif pt.y > self.center.y:
                    pt.y = rounding.round_to_grid_up(pt.y, grid, epsilon)
                else:
                    pt.y = rounding.round_to_grid_down(pt.y, grid, epsilon)
        pt1 = pts[0]  # 1. opposed corner
        pt2 = pts[2]  # 2. opposed corner
        self.center = (pt1 + pt2) / 2
        if self.angle:
            pt1.rotate(-self.angle, origin=self.center)
            pt2.rotate(-self.angle, origin=self.center)
        self.size = (pt1 - pt2).positive()
        self._bbox = None
        return self

    @property
    def points(self) -> list[Vector2D]:
        """The four corners of the rectangle."""
        if not self._corner_pts:
            self._corner_pts = self._get_corner_points()
        return self._corner_pts

    @property
    def min_dimension(self) -> float:
        """The smaller dimension among width and height."""
        return min(self.size.x, self.size.y)

    @property
    def max_dimension(self) -> float:
        """The larger dimension among width and height."""
        return max(self.size.x, self.size.y)

    @property
    def left(self) -> float:
        """The left-most coordinate of the rectangle."""
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.left

    @property
    def right(self) -> float:
        """The right-most coordinate of the rectangle."""
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.right

    @property
    def top(self) -> float:
        """The top-most coordinate of the rectangle."""
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.top

    @property
    def bottom(self) -> float:
        """The bottom-most coordinate of the rectangle."""
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.bottom

    @property
    def top_left(self) -> Vector2D:
        """The top-left coordinate of the rectangle or, in case of angle != 0,
        of the bounding box of the rotated rectangle.
        """
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.top_left

    @property
    def top_right(self) -> Vector2D:
        """The top-right coordinate of the rectangle or, in case of angle != 0,
        of the bounding box of the rotated rectangle.
        """
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.top_right

    @property
    def bottom_right(self) -> Vector2D:
        """The bottom-right coordinate of the rectangle or, in case of angle != 0,
        of the bounding box of the rotated rectangle.
        """
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.bottom_right

    @property
    def bottom_left(self) -> Vector2D:
        """The bottom-left coordinate of the rectangle or, in case of angle != 0,
        of the bounding box of the rotated rectangle.
        """
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.bottom_left

    @property
    def right_midpoint(self) -> Vector2D:
        """The right mid-point of the rectangle or, in case of angle != 0,
        of the bounding box of the rotated rectangle.
        """
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.right_midpoint

    @property
    def left_midpoint(self) -> Vector2D:
        """The left mid-point of the rectangle or, in case of angle != 0,
        of the bounding box of the rotated rectangle.
        """
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.left_midpoint

    @property
    def top_midpoint(self) -> Vector2D:
        """The top mid-point of the rectangle or, in case of angle != 0,
        of the bounding box of the rotated rectangle.
        """
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.top_midpoint

    @property
    def bottom_midpoint(self) -> Vector2D:
        """The bottom mid-point of the rectangle or, in case of angle != 0,
        of the bounding box of the rotated rectangle.
        """
        if not self._bbox:
            self._bbox = self._get_bbox()
        return self._bbox.bottom_midpoint

    @property
    def angle(self) -> float:
        """The angle of the rectangle in degrees."""
        return self._angle

    @angle.setter
    def angle(self, angle: float) -> None:
        """The angle of the rectangle in degrees."""
        self._update_angle(angle)
        self._corner_pts = None
        self._bbox = None

    def _update_angle(self, angle: float) -> None:
        """Update the angle property of the rectangle. May affect also its size
        property.

        Args:
            The angle in degrees.
        """
        self._angle = (angle + 180) % 360 - 180
        if (n := self._number_of_90_deg_rotations(self._angle)) is not None:
            self._angle = 0
            if (n + 2) % 2 == 1:
                temp = self.size.x
                self.size.x = self.size.y
                self.size.y = temp

    def _get_corner_points(self) -> list[Vector2D]:
        """Update the corner points of the rectangle."""
        vector_to_pt1 = -self.size / 2
        vector_to_pt2 = Vector2D.from_floats(-vector_to_pt1.x, vector_to_pt1.y)
        if self._angle:
            origin = Vector2D.from_floats(0.0, 0.0)
            vector_to_pt1 = vector_to_pt1.rotate(angle=self._angle, origin=origin)
            vector_to_pt2 = vector_to_pt2.rotate(angle=self._angle, origin=origin)
        return [
            self.center + vector_to_pt1,
            self.center + vector_to_pt2,
            self.center - vector_to_pt1,
            self.center - vector_to_pt2,
        ]

    def _get_bbox(self) -> BoundingBox:
        """Update the bounding box of the rectangle."""
        if not self._angle:
            dx = self.size.x / 2.0
            dy = self.size.y / 2.0
            min = Vector2D.from_floats(self.center.x - dx, self.center.y - dy)
            max = Vector2D.from_floats(self.center.x + dx, self.center.y + dy)
            return BoundingBox.from_vector2d(min, max)
        else:
            pts = self.points
            bbox = BoundingBox()
            for pt in pts:
                bbox.include_point(pt)
            return bbox

    def _number_of_90_deg_rotations(
        self, angle_in_deg: float | int, tol: float = TOL_MM
    ) -> None | int:
        """Return the number of 90 rotations that the given angle represents, or `None`
        if the given angle is not a multiple of 90°.

        Args:
            angle_in_deg: The angle in degrees.
            tol: The distance in mm that a corner of the rectangle is allowed to deviate
                from the location it would have if the rotation was a perfect 90°. If
                for all 4 corners the deviation is smaller than `tol` the rotation is
                considered to be a full multiple of 90°.

        Returns:
            The multiple of 90° rotation that the given angle corresponds to, or `None`
            if the given anlge is not a multiple of 90°.
        """
        if self._bbox is None:
            return None
        tol_d = tol_deg(tol=tol, radius=(self.bbox().size.norm() / 2))
        if tol_d is None:
            return None
        if abs(angle_in_deg % 90) <= tol_d:
            num_90_deg_rotations = int(round(angle_in_deg, 0)) // 90
            return num_90_deg_rotations
        else:
            return None

    def __repr__(self) -> str:
        """Return the string representation of the rectangle."""
        return (
            f"GeomRectangle(center={self.center}, size={self.size}, angle={self.angle})"
        )
