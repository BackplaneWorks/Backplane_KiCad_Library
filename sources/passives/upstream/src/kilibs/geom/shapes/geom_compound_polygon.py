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

"""Class definition for a geometric compound polygon."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Self

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.shapes.geom_arc import GeomArc
from kilibs.geom.shapes.geom_circle import GeomCircle
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_polygon import GeomPolygon
from kilibs.geom.shapes.geom_shape import GeomShape, GeomShapeClosed
from kilibs.geom.tolerances import MIN_SEGMENT_LENGTH, TOL_MM
from kilibs.geom.vector import Vec2DCompatible, Vector2D


class GeomCompoundPolygon(GeomShapeClosed):
    """A geometric compound polygon (polygon with arc segments)."""

    def __init__(
        self,
        shape: (
            GeomShape
            | Iterable[Vec2DCompatible]
            | Iterable[GeomPolygon | GeomLine | GeomArc]
        ),
        close: bool = True,
    ) -> None:
        """Create a geometric compound polygon.

        Args:
            shape: compound polygon, list of points, polygons, lines or arcs  from which
                to derive the compound polygon.
            close: `True` if the compound polygon shall be closed, `False` otherwise.
        """

        # Instance attributes:
        self.close: bool
        """Whether to close the compound polygon or not."""
        self._segments: list[GeomArc | GeomLine]
        """The arc and line segments the compound polygon is composed of."""
        self._bbox: BoundingBox | None
        """The bounding box."""
        self._end: Vector2D | None = None
        """Internal variable storing the coordinates of the last point added."""

        if isinstance(shape, GeomCompoundPolygon):
            self.close = shape.close
            if shape._segments:
                self._segments = [p.copy() for p in shape._segments]
            else:
                self._segments = []
            if shape._bbox:
                self._bbox = shape._bbox
            else:
                self._bbox = None
            self._end = shape._end
        elif isinstance(shape, GeomShape):
            self.close = isinstance(shape, GeomShapeClosed) and close
            atoms = shape.get_atomic_shapes()
            segments: list[GeomLine | GeomArc] = []
            for atom in atoms:
                if not isinstance(atom, GeomCircle):
                    segments.append(atom)
                else:
                    segments.append(
                        GeomArc(
                            start=atom.center + Vector2D.from_floats(atom.radius, 0.0),
                            center=atom.center,
                            angle=360,
                        )
                    )
            self._segments = segments
            self._bbox = None
            self._end = self._segments[-1].end
        else:
            self.close = close
            self._segments = []
            self._bbox = None
            self._end = None
            for geom in shape:
                self._append_geometry(geom)
            if (
                self.close
                and self._end
                and not self._segments[0].start.is_equal(self._end)
            ):
                self._append_geometry(self._segments[0].start)

    def get_atomic_shapes(self) -> list[GeomLine | GeomArc]:
        """Return the line and arc segments that form the compound polygon in clockwise
        order."""
        # Create a new list of segments instead of returning the original list, so that
        # nobody can change the original list externally:
        return self._segments

    def get_native_shapes(self) -> list[GeomCompoundPolygon]:
        """Return a list with itself in it since a compound polygon is a native shape."""
        return [self]

    def get_points_and_arcs(self) -> list[Vector2D | GeomArc]:
        """Return a list with the corner points and arcs of the compound polygon."""
        points_and_arcs: list[Vector2D | GeomArc] = []
        last_point: Vector2D | None = None
        first_point: Vector2D | None = None
        for segment in self._segments:
            if isinstance(segment, GeomArc):
                if (
                    last_point
                    and isinstance(points_and_arcs[-1], Vector2D)
                    and last_point.is_equal(segment.start)
                ):
                    del points_and_arcs[-1]
                points_and_arcs.append(segment)
                last_point = segment.end
            else:
                if not last_point:
                    points_and_arcs.append(segment.start)
                points_and_arcs.append(segment.end)
                last_point = segment.end
            if not first_point:
                first_point = segment.start
        if (
            first_point
            and last_point
            and isinstance(points_and_arcs[-1], Vector2D)
            and last_point.is_equal(first_point)
        ):
            del points_and_arcs[-1]
        return points_and_arcs

    def translate(self, vector: Vector2D) -> Self:
        """Move the compound polygon.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated compound polygon.
        """
        for segment in self._segments:
            segment.translate(vector=vector)
        self._bbox = None
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the compound polygon around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated compound polygon.
        """
        for segment in self._segments:
            segment.rotate(angle=angle, origin=origin)
        self._bbox = None
        return self

    def inflate(
        self,
        amount: float,
        tol: float = TOL_MM,
    ) -> Self:
        """Inflate or deflate the compound polygon by 'amount'.

        Args:
            amount: The amount in mm by which the compound polygon is inflated (when
                amount is positive) or deflated (when amount is negative).
            tol: Tolerance used to determine if a segment has zero length or if two
                points are equal.

        Raises:
            ValueError: If the deflation operation would result in an invalid shape a
            `ValueError` is raised.

        Warning:
            When deflating too much (when a segment length would become zero or
            negative), the resulting shape can become garbage. Since deflation is not
            a typical use-case, no safeguards have been implemented to catch such
            garbage outputs.

        Returns:
            The compound polygon after the inflation/deflation.
        """
        import kilibs.geom.operations.intersection_points_atomic_shapes as intersect_atomic_shapes
        import kilibs.geom.operations.segment_util as segment_util

        def remove_segment(index: int) -> None:
            del segments[index]
            del directions[index]
            del orthogonals[index]
            del points[index]

        def get_arc_dir_and_ortho(
            segment: GeomArc,
        ) -> tuple[list[Vector2D], list[Vector2D]]:
            radius = segment.radius
            orthogonals_arc = [
                (segment.start - segment.center) / radius,
                (segment.end - segment.center) / radius,
            ]
            directions_arc = [
                orthogonals_arc[0].orthogonal(),
                orthogonals_arc[1].orthogonal(),
            ]
            return (directions_arc, orthogonals_arc)

        if amount == 0:
            return self
        segments = self._segments
        points = [segment.start.copy() for segment in segments]
        # List of normalized direction vectors of the line segments of the polygon:
        directions: list[list[Vector2D]] = []
        # List of vectors orthogonal to the line vectors (pointing outwards):
        orthogonals: list[list[Vector2D]] = []
        # For every line segment of the polygon, calculate the orthogonal and shift the
        # line outwards, and for every arc segment of the polygon check if the arc is
        # convex or concave and increase/decrease the radius accordingly:
        i = 0
        while i < len(segments):
            segment = segments[i]
            if isinstance(segment, GeomLine):
                direction = (segment.end - segment.start).normalize()
                directions.append([direction])
                orthogonal = -direction.orthogonal()
                orthogonals.append([orthogonal])
                delta_orthogonal = orthogonal * amount
                segment.start += delta_orthogonal
                segment.end += delta_orthogonal
            else:  # isinstance(segment, GeomArc):
                segment_radius = segment.radius
                if segment.angle > 0:
                    segment_radius += amount
                else:
                    segment_radius -= amount
                if segment_radius >= 0 or segment.angle < 0:
                    dir, ortho = get_arc_dir_and_ortho(segment)
                    directions.append(dir)
                    orthogonals.append(ortho)
                    segment.radius = segment_radius
                else:
                    del segments[i]
                    del points[i]
                    i -= 1
            i += 1

        i = 0 if self.close else 1
        # For shifted every line segment, depending on the corner style, either extend
        # or shrink the segments (until they meet their neibouring segments) or connect
        # them with an arc:
        while i < len(segments):
            s1, s2 = segments[i - 1], segments[i]
            if isinstance(s1, GeomLine):
                o1, d1 = orthogonals[i - 1][0], directions[i - 1][0]
            else:  # isinstance(segment1, GeomArc)
                o1, d1 = orthogonals[i - 1][1], directions[i - 1][1]
                # For arc segments, the definition of `direction` and `orthogonal`
                # depend on which end we are looking at.
                if s1.angle < 0:
                    o1, d1 = -o1, -d1
            if isinstance(s2, GeomLine):
                o2, d2 = orthogonals[i][0], directions[i][0]
            else:  # isinstance(segment2, GeomArc)
                o2, d2 = orthogonals[i][0], directions[i][0]
                # For arc segments, the definition of `direction` and `orthogonal`
                # depend on which end we are looking at.
                if s2.angle < 0:
                    o2, d2 = -o2, -d2
            if amount > 0:
                try:
                    forward_resized = (o2 + o1).resize(new_len=amount, tol=tol)
                except ZeroDivisionError:
                    if isinstance(s1, GeomLine) and isinstance(s2, GeomLine):
                        # The two segments are colinear with oposite directions (and
                        # possibly discontinuous). They will be simplified out
                        # later, when we call `remove_self_intersections()`. So we
                        # connect the previous line with the new line and move on:
                        s1.end = s2.start
                        i += 1
                        continue
                    else:
                        # If one of the segments is an arc, it means that we have an
                        # acute angle of 0°. The forward direction is the same as the
                        # direction of the first segment:
                        forward_resized = d1.copy().resize(new_len=amount, tol=tol)
                if s1.end.is_equal(s2.start):
                    # No need to build an arc with 0 radius. We move on to the next
                    # corner:
                    i += 1
                    continue
                arc_segment = GeomArc(
                    start=s1.end,
                    mid=points[i] + forward_resized,
                    end=s2.start,
                )
                # Only arcs with positive angle are added to the list:
                if arc_segment.angle > 0:
                    segments.insert(i, arc_segment)
                    # Insert an element at position i so that when we loop through
                    # the lists we can use the same index (i) for all lists. The
                    # value of the element added doesn't matter because we will not
                    # access the list item. We choose Vector2D(Nan, Nan) so we can see
                    # where we inserted new arcs :
                    dir, ortho = get_arc_dir_and_ortho(arc_segment)
                    nan_vec = Vector2D.from_floats(math.nan, math.nan)
                    directions.insert(i, [nan_vec, nan_vec])
                    orthogonals.insert(i, [nan_vec, nan_vec])
                    points.insert(i, nan_vec)
                    i += 2
                    continue

            # If we are deflating (amount < 0) or the previously created arc has a
            # negative angle it means that the two segments that the arc is connecting
            # are intersecting. This happens in concave polygons.
            # In that case we don't add the arc to the list of segments and shorten the
            # intersecting segments, so that they meet instead of intersecting.
            ip = intersect_atomic_shapes.get_intersection_points_of_atomic_shapes(
                shape1=s1,
                shape2=s2,
                exclude_segment_ends_shape1=False,
                exclude_segment_ends_shape2=False,
                infinite_line=True,
                tol=tol,
            )
            if not ip:
                # If there is no intersection point, the inflation/deflation
                # operation is invalid:
                raise ValueError(f"Inflation by {amount} results in an invalid shape.")
            elif len(ip) == 2:
                # if we have two intersection they are unsorted. We have to pick
                # the one that's closest to the point of interest:
                mid_end = (s1.mid + s1.end) / 2
                if mid_end.distance_to(ip[0]) > mid_end.distance_to(ip[1]):
                    ip[0] = ip[1]
            dir1 = s1.direction
            dir2 = s2.direction
            s1.end = ip[0]
            s2.start = ip[0]
            # Remove flipped segments or segments of zero length:
            num_items_removed = 0
            if segment_util.is_segment_flipped_or_zero(s2, dir2, tol=tol):
                remove_segment(i)
                num_items_removed += 1
            if segment_util.is_segment_flipped_or_zero(s1, dir1, tol=tol):
                remove_segment(i - 1)
                num_items_removed += 1
            # If both lines were removed, the element at i-2 in the list might be an arc
            # that needs to be removed because it has been calculated based on the
            # intersection of two lines out of which one of them isn't there anymore:
            if len(segments) > 1:
                if num_items_removed == 2 and points[i - 2].x is math.nan:
                    remove_segment(i - 2)
                    num_items_removed += 1
            else:
                raise ValueError(f"Inflation by {amount} results in an invalid shape.")
            i += 1 - num_items_removed
            if i < 0:
                i = 0
        # If we deflated, the outcome could be a weird counter clockwise shape. If so,
        # we declare the deflation operation a failure:
        if amount < 0 and not self.is_clockwise():
            raise ValueError(f"Inflation by {amount} results in an invalid shape.")
        # If the we have segments left after this, we return either a
        # `GeomCompoundPolygon` or update this GeomPolygon and return it:
        if len(segments) > 1:
            self._bbox = None
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
            amount: The amount in mm by which the compound polygon is inflated (when
                amount is positive) or deflated (when amount is negative).
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
            The compound polygon after the inflation/deflation.
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
            The compound polygon after the simplification.
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
        return self

    def is_point_on_self(
        self,
        point: Vector2D,
        exclude_segment_ends: bool = False,
        tol: float = TOL_MM,
    ) -> bool:
        """Check if a point is on the compound polygon outline.

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: If `True`, then points within `tol` distance of the
                end points of the segments (e.g. corners of the compound polygon) are
                not considered to be on the outline.
            tol: Distance in mm that the point is allowed to be away from the outline
                and still be considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the compound polygon within the
            given tolerance, `False` otherwise.
        """
        for arc_or_polygon in self._segments:
            if arc_or_polygon.is_point_on_self(
                point=point, exclude_segment_ends=exclude_segment_ends, tol=tol
            ):
                return True
        return False

    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the compound polygon.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the compound polygon, `False`
            otherwise.
        """
        from kilibs.geom.operations.intersection_points_atomic_shapes import (
            get_intersection_points_of_upwards_ray_with_arc,
            get_intersection_points_of_upwards_ray_with_line,
        )

        segments = self._segments
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
            segment = segments[i]
            if isinstance(segment, GeomLine):
                if segment.end.x > point.x + tol:
                    return 1
                elif segment.end.x < point.x - tol:
                    return 0
                else:
                    i = (i + 1) % n
                    if i == i_start:
                        return 0
                    return is_next_segment_on_right(i, n, i_start)
            else:
                bbox = segment.bbox()
                if bbox.right > point.x + tol:
                    return 1
                else:
                    return 0

        def is_next_segment_on_left(i: int, n: int, i_start: int) -> int:
            segment = segments[i]
            if isinstance(segment, GeomLine):
                if segment.end.x < point.x - tol:
                    return 1
                elif segment.end.x > point.x + tol:
                    return 0
                else:
                    i = (i + 1) % n
                    if i == i_start:
                        return 0
                    return is_next_segment_on_left(i, n, i_start)
            else:
                bbox = segment.bbox()
                if bbox.left < point.x - tol:
                    return 1
                else:
                    return 0

        # Calculate the number of intersection points between the ray and the polygon
        # segments:
        num_intersections = 0
        n = len(segments)
        for i, segment in enumerate(segments):
            if isinstance(segment, GeomLine):
                ips = get_intersection_points_of_upwards_ray_with_line(
                    ray_start=point, line=segment, tol=tol
                )
                for ip in ips:
                    if ip.is_equal(segment.end, tol=tol):
                        if segment.start.x < point.x - tol:
                            num_intersections += is_next_segment_on_right(
                                (i + 1) % n, n, i
                            )
                        else:
                            num_intersections += is_next_segment_on_left(
                                (i + 1) % n, n, i
                            )
                    else:
                        num_intersections += 1
            else:  # isinstance(segment, GeomArc):
                ips = get_intersection_points_of_upwards_ray_with_arc(
                    ray_start=point, arc=segment, tol=tol
                )
                for ip in ips:
                    if ip.is_equal(segment.end, tol=tol):
                        bbox = segment.bbox()
                        if bbox.left < point.x - tol:
                            num_intersections += is_next_segment_on_right(
                                (i + 1) % n, n, i
                            )
                        else:
                            num_intersections += is_next_segment_on_left(
                                (i + 1) % n, n, i
                            )
                    else:
                        num_intersections += 1

        # If we have an uneven number of intersections the point is inside:
        if num_intersections % 2 == 1:
            return True
        else:
            return False

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the compound polygon."""
        if not self._bbox:
            self._bbox = BoundingBox()
            for point_or_arc in self._segments:
                self._bbox.include_bbox(point_or_arc.bbox())
        return self._bbox

    def round_to_grid(self, grid: float, outwards: bool = True) -> Self:
        """Round the compound polygon to the given grid.

        Args:
            grid: The grid to which the rounding is made.
            outwards: True if the compound polygon points shall be rounded outwards,
                i.e. away from the ccompound polygon center, thus potentially increasing
                the area.
        """
        # TODO
        return self

    def is_clockwise(self) -> bool:
        """Return whether the compound polygon points are given in clockwise order or
        not."""
        sum = 0.0
        segments = self._segments
        points: list[Vector2D] = []
        for segment in segments:
            points.append(segment.start)
            if isinstance(segment, GeomArc):
                points.append(segment.mid)
        num = len(points)
        for i, pt1 in enumerate(points):
            pt2 = points[(i + 1) % num]
            sum += (pt2.x - pt1.x) * (pt2.y + pt1.y)
        if sum < 0:
            return True
        else:
            return False

    def poly_has_any_arc(self) -> bool:
        """Return whether the compound polygon has any arc."""
        for geom in self._segments:
            if isinstance(geom, GeomArc):
                return True
        return False

    def _is_point_equal_to_last_added(
        self, point: Vector2D, tol: float = TOL_MM
    ) -> bool:
        """Check if the point is equal to the last added point."""
        if self._end:
            return self._end.is_equal(point, tol=tol)
        else:
            return False

    def _append_geometry(
        self, geom: GeomLine | GeomArc | GeomPolygon | Vec2DCompatible
    ) -> None:
        """Append a shape or point to the internal list of shapes.

        Args:
            geom: The shape or point to append.
        """
        if isinstance(geom, Vector2D | Iterable | dict):
            geom = Vector2D(geom)
            if not self._is_point_equal_to_last_added(geom):
                if self._end:
                    self._segments.append(GeomLine(start=self._end, end=geom))
                self._end = geom
        elif isinstance(geom, GeomLine | GeomArc):
            if self._is_point_equal_to_last_added(geom.start) or not self._segments:
                self._segments.append(geom.copy())
            elif self._is_point_equal_to_last_added(geom.end):
                # Start and end are reversed
                self._segments.append(geom.reverse().copy())
            else:
                raise ValueError("Geometries are not continuous!")
            self._end = geom.end
        else:  # if isinstance(geom, GeomPolygon):
            points = geom.points
            num = len(points)
            if num > 1:
                if not self._segments or self._is_point_equal_to_last_added(points[0]):
                    for start, end in zip(points[:], points[1:]):
                        self._segments.append(GeomLine(start=start, end=end))
                else:
                    raise ValueError("Geometries are not continuous!")
                if geom.close:
                    self._segments.append(GeomLine(start=points[-1], end=points[0]))
                    self._end = points[0]
                else:
                    self._end = points[-1]
            elif num == 1:
                self._append_geometry(points[0])
                self._end = points[0]
            else:
                raise ValueError("Cannot initialize with empty polygon.")

    def __repr__(self) -> str:
        """Return the string representation of the compound polygon."""
        string = f"GeomCompoundPolygon(\n"
        for geometry in self._segments:
            string += "    " + geometry.__repr__()
            string += ", \n"
        string = string.removesuffix(", \n")
        string += "\n)\n"
        return string
