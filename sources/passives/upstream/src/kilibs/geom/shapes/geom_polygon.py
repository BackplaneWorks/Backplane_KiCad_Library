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

"""Class definition for a geometric polygon."""

from __future__ import annotations

import warnings
from collections.abc import Callable, Iterable
from typing import Self, TypeAlias

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_rectangle import GeomRectangle
from kilibs.geom.shapes.geom_shape import GeomShapeClosed
from kilibs.geom.tolerances import MIN_SEGMENT_LENGTH, TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomPolygon(GeomShapeClosed):
    """A gemoetric polygon."""

    def __init__(
        self,
        shape: (
            GeomPolygon
            | GeomRectangle
            | BoundingBox
            | Iterable[Vec2DCompatible]
            | Iterable[GeomLine]
        ),
        x_mirror: float | None = None,
        y_mirror: float | None = None,
        close: bool = True,
    ) -> None:
        """Create a geometric polygon.

        Args:
            shape: polygon, rectangle, bounding box or list of points from which to
                derive the polygon.
            x_mirror: Mirror the points on the y-axis offset by `x_mirror` mm.
            y_mirror: Mirror the points on the x-axis offset by `y_mirror` mm.
            close: If `True` the polygon will form a closed shape. If `False` there
                won't be any connecting line between the last and the first point.
                This argument is ignored when constructing from a `BoundingBox` or a
                `GeomRectangle`.
        """

        # Instance attributes:
        self.close: bool
        """Whether the polygon is closed or not."""
        self.points: list[Vector2D]
        """Coordintes of the corner points of the polygon in mm."""
        self._segments: list[GeomLine]
        """List of segments the polygon is made of."""

        self.close = close
        self.points = []
        if isinstance(shape, GeomPolygon):
            for point in shape.points:
                self.points.append(point.copy())
            self.close = shape.close
        elif isinstance(shape, list | tuple) and len(shape):
            for point_or_line in shape:
                if isinstance(point_or_line, GeomLine):
                    self.points.append(point_or_line.start.copy())
                else:
                    self.points.append(Vector2D(point_or_line))
            self._remove_zero_length_segments()
        elif isinstance(shape, GeomRectangle):
            for point in shape.points:
                self.points.append(point.copy())
            self.close = True
            self._remove_zero_length_segments()
        elif isinstance(shape, BoundingBox):
            self.points = [
                Vector2D.from_floats(shape.left, shape.top),
                Vector2D.from_floats(shape.right, shape.top),
                Vector2D.from_floats(shape.right, shape.bottom),
                Vector2D.from_floats(shape.left, shape.bottom),
            ]
            self.close = True
            self._remove_zero_length_segments()
        else:
            raise TypeError("Type for 'source' not supported.")

        if x_mirror is not None:
            for point in self.points:
                point.x = 2 * x_mirror - point.x
        if y_mirror is not None:
            for point in self.points:
                point.y = 2 * y_mirror - point.y
        self._segments = []

    def get_atomic_shapes(self) -> list[GeomLine]:
        """Return a list of the lines that compose this polygon."""
        return self.segments

    def get_native_shapes(self) -> list[GeomPolygon]:
        """Return a list with itself in it since a line is a basic shape."""
        return [self]

    def translate(self, vector: Vector2D) -> Self:
        """Move the polygon.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated polygon.
        """
        for point in self.points:
            point += vector
        self._segments = []
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the cross around a given point.

        Args:
            angle: Rotation angle in degrees.

        Returns:
            The rotated cross.
        """
        if angle:
            for point in self.points:
                point.rotate(angle=angle, origin=origin)
        self._segments = []
        return self

    def inflate(
        self,
        amount: float,
        tol: float = TOL_MM,
    ) -> Self:
        """Inflate or deflate the polygon by 'amount'.

        Args:
            amount: The amount in mm by which the polygon is inflated (when amount is
                positive) or deflated (when amount is negative).
            tol: Maximum negative dimension in mm that a segment of the shape is allowed
                to have after the deflation without causing a `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in segments with
                negative dimensions a `ValueError` is raised.

        Warning:
            When deflating too much (when a segment length would become zero or
            negative), the resulting shape can become garbage. Since deflation is not
            a typical use-case, no safeguards have been implemented to catch such
            garbage outputs.

        Returns:
            The polygon after the inflation/deflation.
        """
        import kilibs.geom.operations.intersection_points_atomic_shapes as intersect_atomic_shapes

        def remove_segment(index: int) -> None:
            del segments[index]
            del directions[index]
            del orthogonals[index]
            del points[index]

        segments: list[GeomLine] = [line for line in self.segments]
        points = self.points
        # List of normalized direction vectors of the line segments of the polygon:
        directions: list[Vector2D] = []
        # List of vectors orthogonal to the line vectors (pointing outwards):
        orthogonals: list[Vector2D] = []
        # For every line segment of the polygon, calculate the orthogonal and shift the
        # line outwards:
        for i, segment in enumerate(segments):
            direction = segment.unit_direction
            directions.append(direction)
            orthogonal = -direction.orthogonal()
            orthogonals.append(orthogonal)
            delta_orthogonal = orthogonal * amount
            segment.start += delta_orthogonal
            segment.end += delta_orthogonal

        needs_simplification = False
        if self.close:
            i = 0
        else:
            i = 1
        # For shifted every line segment, depending on the corner style, either extend
        # or shrink the segments (until they meet their neibouring segments) or connect
        # them with an arc:
        while i < len(segments):
            # Check if the two segments form an acute angle between each other. For
            # that we use the property of the dot produt:
            # * If the dot product is > 0 the anle is acute,
            # * If the dot product is < 0 the angle is obtuse,
            # * If the dot product is = 0 the angle is 90°.
            if directions[i].dot_product(directions[i - 1]) <= -tol:
                needs_simplification = True
                if amount > 0:
                    try:
                        forward = (orthogonals[i] + orthogonals[i - 1]).normalize(
                            tol=tol
                        )
                    except ZeroDivisionError:
                        raise ValueError(
                            f"Inflation by {amount} results in an invalid shape."
                        )
                    forward_orthogonal = forward.orthogonal()
                    new_line_start = self.points[i] + forward.resize(
                        new_len=amount, tol=tol
                    )
                    new_line_end = new_line_start + forward_orthogonal
                    new_line = GeomLine(start=new_line_start, end=new_line_end)
                    segments.insert(i, new_line)
                    directions.insert(i, forward_orthogonal)
                    orthogonals.insert(i, forward)
                    # Again, we add a dummy value to points, just so that we can iterate
                    # through all the lists with the same index value. The exact value of
                    # the point does not matter, hence we just add the first point:
                    points.insert(i, points[0])
            pt = intersect_atomic_shapes.get_intersection_points_of_lines(
                line1=segments[i - 1],
                line2=segments[i],
                infinite_line=True,
                tol=tol,
            )
            if not pt:  # lines coincide
                segments[i - 1].end = segments[i].end
                remove_segment(i)
            else:
                segment = segments[i - 1]
                segment.end = pt[0]
                segments[i].start = pt[0]
                # Remove lines of zero length:
                if (
                    abs(segment.start.x - segment.end.x) <= tol
                    and abs(segment.start.y - segment.end.y) <= tol
                ):
                    remove_segment(i - 1)
                    i -= 1
                i += 1
                if i < 0:
                    i = 0

        # If we deflated, the outcome could be a weird counter clockwise shape. If so,
        # we declare the deflation operation a failure:
        if amount < 0:
            if not self.is_clockwise():
                raise ValueError(f"Inflation by {amount} results in an invalid shape.")
            import kilibs.geom.operations.segment_util as segment_util

            segment_util.remove_zero_length_segments(segments=segments)
        # If the we have segments left after this, we return either a
        # `GeomCompoundPolygon` or update this GeomPolygon and return it:
        if len(segments) > 2:
            # convert the lines back to vertices
            self.points.clear()
            for segment in segments:
                self.points.append(segment.start)
            if not self.close:
                self.points.append(segments[-1].end)
            self._segments = segments
            if needs_simplification:
                self.simplify()
            return self
        else:
            raise ValueError(f"Inflation by {amount} results in an invalid shape.")

    def inflated(
        self,
        amount: float,
        tol: float = TOL_MM,
    ) -> Self:
        """Create a copy and inflate or deflate it by 'amount'.

        Args:
            amount: The amount in mm by which the polygon is inflated (when amount is
                positive) or deflated (when amount is negative).
            tol: Maximum negative dimension in mm that a segment of the shape is allowed
                to have after the deflation without causing a `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in segments with
                negative dimensions a `ValueError` is raised.

        Warning:
            When deflating too much (when a segment length would become zero or
            negative), the resulting shape can become garbage. Since deflation is not
            a typical use-case, no safeguards have been implemented to catch such
            garbage outputs.

        Returns:
            The polygon after the inflation/deflation. If the polygon is inflated with
            corner_style = ROUND, a `GeomCompoundPolygon` is returned instead and the
            original polygon remains unaffected.
        """
        return self.copy().inflate(
            amount=amount,
            tol=tol,
        )

    def simplify(
        self, min_segment_length: float = MIN_SEGMENT_LENGTH, tol: float = TOL_MM
    ) -> Self:
        """Simplify the outline by removing segments that are inside the outer outline,
        by removing segments that are too short (shorter than `min_segment_length`) and
        by unifying colinear lines as well as arcs that lie on the same circle.

        Args:
            min_segment_length: Segments shorter than this are removed from the outline.
            tol: Maximum distance in mm that two points can be away from each other and
                still be considered identical.

        Raises:
            ValueError: If the outline resulting from the simplification is not valid.

        Returns:
            The polygon after the simplification.
        """
        import kilibs.geom.operations.segment_util as segment_util

        segment_util.remove_zero_length_segments(
            segments=self._segments, min_segment_length=min_segment_length
        )
        if not segment_util.keep_only_outer_outline(
            segments=self._segments, min_segment_length=min_segment_length, tol=tol
        ):
            raise ValueError(f"`simplify()` results in an invalid shape.")
        if not segment_util.merge_segments(segments=self._segments, tol=tol):
            raise ValueError(f"`simplify()` results in an invalid shape.")
        self.points.clear()
        for segment in self._segments:
            self.points.append(segment.start)
        if not self.close:
            self.points.append(self._segments[-1].end)
        return self

    def round_to_grid(self, grid: float, outwards: bool = True) -> Self:
        """Round the polygon to the given grid.

        Args:
            grid: The grid to which the rounding is made.
            outwards: True if the polygon points shall be rounded outwards, i.e.
                away from the polygon center, thus potentially increasing the area.
        """
        import kilibs.geom.operations.rounding as rounding

        if outwards is False:
            for i, pt in enumerate(self.points):
                pt.x = rounding.round_to_grid_nearest(pt.x, grid)
                pt.y = rounding.round_to_grid_nearest(pt.y, grid)
        else:
            if self.is_clockwise():
                round_up = rounding.round_to_grid_up
                round_down = rounding.round_to_grid_down
            else:
                round_down = rounding.round_to_grid_up
                round_up = rounding.round_to_grid_down
            num = len(self.points)
            for i, pt1 in enumerate(self.points):
                pt2 = self.points[(i + 1) % num]
                if pt1.x < pt2.x:  # going right
                    pt1.y = round_down(pt1.y, grid, grid / 100)
                    pt2.y = round_down(pt2.y, grid, grid / 100)
                elif pt1.x > pt2.x:  # going left
                    pt1.y = round_up(pt1.y, grid, grid / 100)
                    pt2.y = round_up(pt2.y, grid, grid / 100)
                if pt1.y > pt2.y:  # going up
                    pt1.x = round_down(pt1.x, grid, grid / 100)
                    pt2.x = round_down(pt2.x, grid, grid / 100)
                elif pt1.y < pt2.y:  # going down
                    pt1.x = round_up(pt1.x, grid, grid / 100)
                    pt2.x = round_up(pt2.x, grid, grid / 100)
        self._segments = []
        return self

    def is_point_on_self(
        self,
        point: Vector2D,
        exclude_segment_ends: bool = False,
        tol: float = TOL_MM,
    ) -> bool:
        """Check if a point is on the polygon outline.

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: If `True`, then points within `tol` distance of the
                end points of the segments (corners of the polygon) are not considered
                to be on the outline.
            tol: Distance in mm that the point is allowed to be away from the outline
                and still be considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the polygon within the given
            tolerance, `False` otherwise.
        """
        for segment in self.segments:
            if segment.is_point_on_self(
                point=point, exclude_segment_ends=exclude_segment_ends, tol=tol
            ):
                return True
        return False

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the polygon.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the polygon, `False`
            otherwise.
        """
        from kilibs.geom.operations.intersection_points_atomic_shapes import (
            get_intersection_points_of_upwards_ray_with_line,
        )

        segments = self.segments
        # Check if the point is on the outline:
        for segment in segments:
            if segment.is_point_on_self(
                point=point, exclude_segment_ends=False, tol=tol
            ):
                return not strictly_inside
        # As per the Ray casting algorithm, one simple way of finding whether the point
        # is inside or outside a simple polygon is to test how many times a ray,
        # starting from the point and going in any fixed direction, intersects the
        # edges of the polygon. If the point is on the outside of the polygon the ray
        # will intersect its edge an even number of times. If the point is on the
        # inside of the polygon then it will intersect the edge an odd number of times.

        def is_next_segment_on_right(i: int, n: int, i_start: int) -> int:
            if segments[i].end.x > point.x + tol:
                return 1
            elif segments[i].end.x < point.x - tol:
                return 0
            else:
                i = (i + 1) % n
                if i == i_start:
                    return 0
                return is_next_segment_on_right(i, n, i_start)

        def is_next_segment_on_left(i: int, n: int, i_start: int) -> int:
            if segments[i].end.x < point.x - tol:
                return 1
            elif segments[i].end.x > point.x + tol:
                return 0
            else:
                i = (i + 1) % n
                if i == i_start:
                    return 0
                return is_next_segment_on_left(i, n, i_start)

        # Calculate the number of intersection points between the ray and the polygon
        # segments:
        num_intersections = 0
        n = len(segments)
        for i, segment in enumerate(segments):
            ip = get_intersection_points_of_upwards_ray_with_line(
                ray_start=point, line=segment, tol=tol
            )
            if ip:
                if ip[0].is_equal(segment.end, tol=tol):
                    if segment.start.x < point.x - tol:
                        num_intersections += is_next_segment_on_right((i + 1) % n, n, i)
                    else:
                        num_intersections += is_next_segment_on_left((i + 1) % n, n, i)
                else:
                    num_intersections += 1

        # If we have an uneven number of intersections the point is inside:
        if num_intersections % 2 == 1:
            return True
        else:
            return False

    def bbox(self) -> BoundingBox:
        r"""Calculate the bounding box of the polygon points."""
        bbox = BoundingBox()
        for n in self.points:
            bbox.include_point(n)
        return bbox

    def cut_with_polygon(
        self, other_polygon: GeomPolygon
    ) -> None:  # Currently only used in old unit tests.
        """Cut other polygon points from self.

        As kicad has no native support for cutting one polygon from the other,
        the cut is done by connecting the nearest points of the two polygons
        with two lines on top of each other.

        This function assumes that the other polygon is fully within this one.
        It also assumes that connecting the two nearest points creates a valid
        polygon. (There are no geometry checks)

        Args:
            other_polygon: The polygon defining the cutting shape.
        """

        warnings.warn(
            "No geometry checks are implement for cutting polygons.\n"
            "Make sure the second polygon is fully inside the main polygon\n"
            "Check resulting polygon carefully.",
            Warning,
        )

        def find_nearest_points(other: GeomPolygon) -> tuple[int, int]:
            """Find the two points for both polygons that are nearest to each other.

            Args:
                other: The other polygon

            Returns:
                A tuple with the indexes of the two points:
                (point in self, point in other)
            """
            min_distance = self.points[0].distance_to(other.points[0])
            pi = 0
            pj = 0
            for i in range(len(self.points)):
                for j in range(len(other.points)):
                    d = self.points[i].distance_to(other.points[j])
                    if d < min_distance:
                        pi = i
                        pj = j
                        min_distance = d
            return (pi, pj)

        idx_self, idx_other = find_nearest_points(other_polygon)
        self.points.insert(idx_self + 1, self.points[idx_self])
        for i in range(len(other_polygon.points)):
            self.points.insert(
                idx_self + 1,
                other_polygon.points[(i + idx_other) % len(other_polygon.points)],
            )
        self.points.insert(idx_self + 1, other_polygon.points[idx_other])
        self._segments = []

    def is_clockwise(self) -> bool:
        """Return whether the polygon points are given in clockwise order or not."""
        sum = 0.0
        num = len(self.points)
        for i, pt1 in enumerate(self.points):
            pt2 = self.points[(i + 1) % num]
            sum += (pt2.x - pt1.x) * (pt2.y + pt1.y)
        if sum < 0:
            return True
        else:
            return False

    def make_clockwise(self) -> None:
        """Reorder the polygon points if necessary so that they define a closed shape
        in clockwise order.
        """
        if not self.is_clockwise():
            self.points.reverse()
            self._segments = []

    PointTransformFunc: TypeAlias = Callable[[Vec2DCompatible], Vector2D]
    """
    A callable that takes a Vector2D and returns a transformed Vector2D.
    This is used to apply transformations to the polygon points.
    """

    def transform_points(self, transform: PointTransformFunc) -> None:
        """Apply a transformation to the polygon points in place.

        Args:
            transform: The transformation function to apply to each point in turn
        """
        for i, point in enumerate(self.points):
            self.points[i] = transform(point)
        self._segments = []

    @property
    def segments(self) -> list[GeomLine]:
        """The line segments that define the polygon."""
        if self._segments:
            return self._segments
        else:
            self._segments = []
            num = len(self.points)
            num_lines = num if self.close else num - 1
            for i in range(num_lines):
                self._segments.append(
                    GeomLine.from_vector2d(
                        start=self.points[i], end=self.points[(i + 1) % num]
                    )
                )
        return self._segments

    def _remove_zero_length_segments(self, tol: float = TOL_MM) -> None:
        """Remove points from the list that would otherwise create segments of zero
        length.
        """
        # Open polygons don't have the line from the last point to the first point
        i = 0 if self.close else 1
        while i < len(self.points) and len(self.points) > 1:
            if self.points[i].is_equal(self.points[i - 1], tol=tol):
                del self.points[i - 1]
            else:
                i += 1

    def __repr__(self) -> str:
        """Return the string representation of the polygon."""
        string = "GeomPolygon("
        for point in self.points:
            string += f"{point}, "
        string = string.removesuffix(", ")
        string += ")"
        return string
