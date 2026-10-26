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

"""Unite function."""

from typing import cast

from kilibs.geom import (
    GeomArc,
    GeomCompoundPolygon,
    GeomLine,
    GeomPolygon,
    GeomShapesClosed,
    Vector2D,
)

from ..tolerances import MIN_SEGMENT_LENGTH, TOL_MM
from .geom_operation_handle import GeomOperationHandle
from .intersection_points import intersect_handler
from .segment_util import has_arcs


def unite(
    shape1: GeomShapesClosed,
    shape2: GeomShapesClosed,
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> list[GeomShapesClosed]:
    r"""Unite two shapes.

    Args:
        shape1: One of the 2 shapes to unite.
        shape2: The other shape to unite with the first one.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the `unite()` operation is shorter than `min_segment_length`, it is
            omitted from the resulting shape.
        tol: Tolerance used to determine if the two points are equal.

    Returns:
        A list containing a polygon or compound polygon (if there are arcs in the
        resulting shape) describing the outline of the union of the two shapes. If there
        is no overlap between the two shapes the list contains both shapes. If there is
        full overlap (e.g. one shape is fully inside another shape) the shape with the
        larger outline is returned in the list.

    Example:
        When `unite()` is called with two rounded rectangles as argument:

    .. aafig::
        /--------------\
        |              |
        |        /-----+-----\
        |        |     |     |
        \--------+-----/     |
                 |           |
                 |           |
                 \-----------/

    The result would be:

    .. aafig::
        /--------------\
        |              |
        |              +-----\
        |                    |
        \--------+           |
                 |           |
                 |           |
                 \-----------/
    """
    # For the unite() operation we need both shapes to be cut up:
    handle = intersect_handler(
        shape1=shape1,
        shape2=shape2,
        strict_intersection=False,
        cut_also_shape_2=True,
        min_segment_length=min_segment_length,
        tol=tol,
    )
    # If there is only one or zero intersections between the two shapes the two
    # shapes are either disjunct (in which case we return a list containing both
    # shapes) or one shape is inside the other (in which case we return the outer
    # shape):
    if not handle.intersections or len(handle.intersections) == 1:
        if handle.atoms_inside_other_shape[0][0]:
            return [shape2]
        elif handle.atoms_inside_other_shape[1][0]:
            return [shape1]
        return [shape1, shape2]
    # At this point we know that there are 2 or more intersections. This means that if
    # one of the shapes was a circle, it would have been decomposed into arcs.
    handle.segs = cast(list[list[GeomArc | GeomLine]], handle.atoms)
    return _unite_segments_from_both_shapes(handle, shape1, shape2)


def _unite_segments_from_both_shapes(
    handle: GeomOperationHandle,
    shape1: GeomShapesClosed,
    shape2: GeomShapesClosed,
) -> list[GeomShapesClosed]:
    """Unite the segments of both shapes.

    Args:
        handle: The handle to the geometric operations.
        shape1: The first shape.
        shape2: The second shape.

    Returns:
        A list containing a polygon or compound polygon (if there are arcs in the
        resulting shape) describing the outline of the union of the two shapes. If there
        is no overlap between the two shapes the list contains both shapes. If there is
        full overlap (e.g. one shape is fully inside of the other shape) the shape with
        the larger outline is returned in the list.
    """
    segments: list[GeomLine | GeomArc] = []
    first_point = _find_first_point_outside_other_shape(handle, 0)
    # If `None` is returned it means that all segments are either outside or inside
    # of the other shape.
    if first_point is None:
        if handle.atoms_inside_other_shape[0][0]:
            return [shape2]
        elif handle.atoms_inside_other_shape[1][0]:
            return [shape1]
        # Both shapes are fully outside but there are still intersection points.
        # This means that the shapes must be touching:
        else:
            get_segments_func = _get_all_outside_segments_till_next_intersection
            first_point = _find_first_point_that_is_not_an_intersection(handle, 0)
            if first_point is None:
                # If we have several intersection points and all segments of both
                # shapes are outside of one another, we must have a superposition of
                # two identical shapes:
                return [shape1]
    else:
        get_segments_func = _get_all_outside_segments_after_point
    # We expect to have as many segments in the solution as we have segments that
    # are outside of the "other" shape:
    total_expected_number_of_segments = handle.atoms_inside_other_shape[0].count(
        False
    ) + handle.atoms_inside_other_shape[1].count(False)
    # Join all the segments together that are outside of the "other" shape:
    idx_current_shape = 0
    point = first_point
    while True:
        new_segments = get_segments_func(
            handle,
            idx_shape=idx_current_shape,
            point=point,
            first_point=first_point,
        )
        # If no new segments are returned, we have all the segments that there were to
        # get. Wee can end the while loop.
        if new_segments is None:
            if handle.is_point_an_intersection(segments[-1].end):
                break
            else:
                raise RuntimeError(
                    "An intersection point could not be found in the other shape. "
                    "This shouldn't happen - it's an implementation error, or one of "
                    "the shapes is not returning its segments in clockwise order."
                )
        segments += new_segments
        point = segments[-1].end
        idx_current_shape = (idx_current_shape + 1) % 2
        num_segments = len(segments)
        if (
            point.is_equal(first_point, handle.tol)
            or num_segments >= total_expected_number_of_segments
        ):
            if num_segments > total_expected_number_of_segments:
                segments = _remove_doubles(segments)
            break
    segments = _merge_colinear_segments(segments)
    shape: GeomCompoundPolygon | GeomPolygon
    if has_arcs(segments):
        shape = GeomCompoundPolygon(shape=segments)
    else:
        shape = GeomPolygon(shape=cast(list[GeomLine], segments))
    if not shape.is_clockwise():
        # We unfortunately started off from a point that turned out to be part
        # of an enclave (negative area inside the real area we want to get).
        # Since we removed the segments of this enclave already from the
        # internal segments list, we can just call this function again and it
        # will start off from a different point:
        return _unite_segments_from_both_shapes(handle, shape1, shape2)
    return [shape]


def _remove_doubles(
    segments: list[GeomArc | GeomLine], tol: float = TOL_MM
) -> list[GeomArc | GeomLine]:
    """Find segments that appear more than once in the list and remove them.

    Args:
        segments: The list containing the segments.
        tol: Tolerance in mm used to determine if two segments are identical.

    Returns:
        The list with the segments without doubles.
    """
    i = 1
    while i < len(segments):
        j = 0
        while j < i:
            seg1 = segments[i]
            seg2 = segments[j]
            if isinstance(seg1, GeomLine) and isinstance(seg2, GeomLine):
                if seg1.is_equal(seg2, tol=tol):
                    del segments[i]
                    i -= 1
                    break
            elif isinstance(seg1, GeomArc) and isinstance(seg2, GeomArc):
                if seg1.is_equal(seg2, tol=tol):
                    del segments[i]
                    i -= 1
                    break
            else:
                j += 1
        i += 1
    return segments


def _merge_colinear_segments(
    segments: list[GeomArc | GeomLine], tol: float = TOL_MM
) -> list[GeomArc | GeomLine]:
    """Merge neighbouring line segments that are colinear or neighbouring arc segments
    that lie on the same circle.

    Args:
        segments: The list of segments.
        tol: The tolerance in mm used to determine if two line segments are colinear or
            if two arc segments are on the same circle.

    Returns:
        The list of segments after merging.
    """
    unit_directions: list[Vector2D] = []
    for segment in segments:
        if isinstance(segment, GeomLine):
            unit_directions.append(segment.unit_direction)
        else:
            unit_directions.append(segment.center)
    i = 0
    while i < len(segments):
        seg1 = segments[i - 1]
        seg2 = segments[i]
        if isinstance(seg1, GeomLine) and isinstance(seg2, GeomLine):
            if unit_directions[i - 1].is_equal(unit_directions[i], tol=tol):
                seg1.end = seg2.end
                del segments[i]
                del unit_directions[i]
                i -= 1
        elif isinstance(seg1, GeomArc) and isinstance(seg2, GeomArc):
            if unit_directions[i - 1].is_equal(unit_directions[i], tol=tol):
                seg1.angle += seg2.angle
                del segments[i]
                del unit_directions[i]
                i -= 1
        i += 1
    return segments


def _find_first_point_that_is_not_an_intersection(
    handle: GeomOperationHandle, idx_shape: int
) -> Vector2D | None:
    """Return the first point that is not on an intersection. If none is found `None` is
    returned.

    Args:
        handle: The handle to the intersection data.
        idx_shape: The index of the shape (either 0 or 1) on which the point shall be
            searched.
    """
    for segment in handle.segs[idx_shape]:
        start_is_on_intersection = False
        for point in handle.intersections:
            if segment.start.is_equal(point, handle.tol):
                start_is_on_intersection = True
                continue
        if not start_is_on_intersection:
            return segment.start
    return None


def _find_first_point_outside_other_shape(
    handle: GeomOperationHandle, idx_shape: int
) -> Vector2D | None:
    """Return the first point that is outside of the other shape. If none is found or if
    all points of the shape are outside of the other shape, `None` is returned.

    Args:
        handle: The handle to the intersection data.
        idx_shape: The index of the shape (either 0 or 1) on which the point shall be
            earched.
    """
    i = 0
    num = len(handle.atoms_inside_other_shape[idx_shape])
    # If the first point is inside the other shape, iterate forward to find the
    # first point outside of the shape:
    if handle.atoms_inside_other_shape[idx_shape][0]:
        i += 1
        while handle.atoms_inside_other_shape[idx_shape][i]:
            i += 1
            if i == num:
                return None
        segment = handle.segs[idx_shape][i]
        return segment.start
    # If the first point is outside of the other shape, iterate backwards to find
    # the beginning of the sequence of segments that are outside:
    else:
        i = num - 1
        while not handle.atoms_inside_other_shape[idx_shape][i]:
            i -= 1
            if i == -1:
                return None
        segment = handle.segs[idx_shape][i]
        return segment.end


def _get_all_outside_segments_after_point(
    handle: GeomOperationHandle, idx_shape: int, point: Vector2D, first_point: Vector2D
) -> list[GeomArc | GeomLine] | None:
    """Return the sequence of the segments that start on `point` and are outside of the
    other shape.

    Args:
        handle: The handle to the intersection data.
        idx_shape: The index (0 or 1) of the shape from which the segments are returned.
        point: The point.
        first_point: The starting point of the union. Currently not used.

    Returns:
        The list of segments, or `None` if the point is not part of the selected shape.
    """
    # Find the index of the point given for the selected shape (idx_shape):
    i = 0
    num = len(handle.segs[idx_shape])
    segment = handle.segs[idx_shape][i]
    while not segment.start.is_equal(point=point, tol=handle.tol):
        i += 1
        if i == num:
            return None
        segment = handle.segs[idx_shape][i]
    # Find all the segments after the point that are outside of the other shape:
    segments: list[GeomArc | GeomLine] = []
    while not handle.atoms_inside_other_shape[idx_shape][i]:
        segment = handle.segs[idx_shape][i]
        segments.append(segment)
        del handle.segs[idx_shape][i]
        del handle.atoms_inside_other_shape[idx_shape][i]
        if not handle.segs[idx_shape]:
            return segments
        if i == len(handle.segs[idx_shape]):
            i = 0
    return segments


def _get_all_outside_segments_till_next_intersection(
    handle: GeomOperationHandle, idx_shape: int, point: Vector2D, first_point: Vector2D
) -> list[GeomArc | GeomLine] | None:
    """Return the sequence of the segments that start on `point` until an intersection
    point is reached.

    Args:
        handle: The handle to the intersection data.
        idx_shape: The index (0 or 1) of the shape from which the segments are
            returned.
        point: The starting point.
        first_point: The starting point of the union.

    Returns:
        The list of segments or `None` if the point is not part of the selected
        shape.
    """
    # Find the index of the point given for the selected shape (idx_shape):
    i = 0
    num = len(handle.segs[idx_shape])
    segment = handle.segs[idx_shape][i]
    while not segment.start.is_equal(point=point, tol=handle.tol):
        i += 1
        if i == num:
            return None
        segment = handle.segs[idx_shape][i]
    # Find all the segments after the point until we hit the next intersection point:
    segments: list[GeomArc | GeomLine] = []
    while True:
        if handle.atoms_inside_other_shape[idx_shape][i]:
            return segments
        segment = handle.segs[idx_shape][i]
        segments.append(segment)
        del handle.segs[idx_shape][i]
        del handle.atoms_inside_other_shape[idx_shape][i]
        if i == len(handle.segs[idx_shape]):
            i = 0
            segment = handle.segs[idx_shape][i]
        if not handle.segs[idx_shape]:
            return segments
        if segment.end.is_equal(first_point, tol=handle.tol):
            return segments
        for point in handle.intersections:
            if segment.end.is_equal(point, tol=handle.tol):
                return segments
