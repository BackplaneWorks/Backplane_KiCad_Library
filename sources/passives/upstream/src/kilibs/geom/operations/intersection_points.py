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

"""Intersect function."""

from __future__ import annotations

import math
from typing import cast

from kilibs.geom import (
    GeomArc,
    GeomCircle,
    GeomCompoundPolygon,
    GeomLine,
    GeomPolygon,
    GeomShapeClosed,
    GeomShapeOpen,
    GeomShapes,
    Vector2D,
)

from ..tolerances import MIN_SEGMENT_LENGTH, TOL_MM
from .geom_operation_handle import GeomOperationHandle
from .intersection_points_atomic_shapes import get_intersection_points_of_atomic_shapes


def get_intersection_points(
    shape1: GeomShapes,
    shape2: GeomShapes,
    strict_intersection: bool = True,
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> list[Vector2D]:
    """Intersect `shape1` with `shape2`.

    Args:
        shape1: One of the shapes to intersect.
        shape2: The other shape to intersect.
        strict_intersection: If `True`, then intersection points resulting from
            shapes that are tangent to another or from segments that have their
            beginning or their ending on the outline of the other shape are omitted
            from the results. If `False` then those points are included.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the cut operation is shorter than `min_segment_length`, it is
            omitted from the results.
        tol: Tolerance used to determine if the two points are equal.

    Returns:
        The `GeomOperationHandle` structure which contains information about the
        intersections.
    """
    handle = intersect_handler(
        shape1=shape1,
        shape2=shape2,
        strict_intersection=strict_intersection,
        cut_also_shape_2=True,
        min_segment_length=min_segment_length,
        tol=tol,
    )
    return handle.intersections


def intersect_handler(
    shape1: GeomShapes,
    shape2: GeomShapes,
    strict_intersection: bool = True,
    cut_also_shape_2: bool = True,
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> GeomOperationHandle:
    """Intersect `shape1` with `shape2`.

    Args:
        shape1: One of the shapes to intersect.
        shape2: The other shape to intersect.
        strict_intersection: If `True`, then intersection points resulting from
            shapes that are tangent to another or from segments that have their
            beginning or their ending on the outline of the other shape are omitted
            from the results. If `False` then those points are included.
        cut_also_shape_2: When `strict_intersection` is `True`, the `intersect()`
            operation cuts `shape1` in its segments in order to determine if an
            intersection point is a strict intersection or not. The segment that is on
            the intersection is cut in two and one part of the segment needs to be
            inside the other shape and the other part of the segment needs to be outside
            of the other shape in order for the intersection point to be considered a
            strict intersection. In case of two open shapes intersecting each other,
            the algorithm requires also that shape2 be cut into segments for a correct
            detection of strict intersections.
            When `strict_intersection` is `False`, none of the shapes is cut -
            irrespective of the value of `cut_also_shape_2`.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the cut operation is shorter than `min_segment_length`, it is
            omitted from the results.
        tol: Tolerance used to determine if the two points are equal.

    Returns:
        The `GeomOperationHandle` structure which contains information about the
        intersections.
    """
    handle = GeomOperationHandle(
        shape1=shape1,
        shape2=shape2,
        strict_intersection=strict_intersection,
        min_segment_length=min_segment_length,
        tol=tol,
    )
    # Intersect all the segments of the two shapes and add them to the list of
    # segments:
    for i, shape1 in enumerate(handle.atoms[0]):
        for j, shape2 in enumerate(handle.atoms[1]):
            intersections = get_intersection_points_of_atomic_shapes(
                shape1=shape1,
                shape2=shape2,
                exclude_tangents=handle.exclude_tangents,
                exclude_segment_ends_shape1=handle.exclude_segment_ends[0],
                exclude_segment_ends_shape2=handle.exclude_segment_ends[1],
                infinite_line=False,
                tol=tol,
            )
            handle.add_intersections(
                intersections=intersections, idx_shape1=i, idx_shape2=j
            )
    # [For each shape] cut the segments at their intersection point and check if
    # the mid-point of the newly generated segments are inside or outside of the
    # other shape. If they are on the same side, they can be merged again and the
    # intersection point can be removed - that is if `strict_intersection` is
    # `True`:
    _replace_segments_with_cuts(handle, 0)
    _test_if_segments_inside_other_shape(handle, 0)
    if strict_intersection:
        _keep_only_strict_intersections(handle, 0)
    # The keepout operation for instance only requires shape 1 to be cut:
    if cut_also_shape_2:
        _replace_segments_with_cuts(handle, 1)
        _test_if_segments_inside_other_shape(handle, 1)
        if strict_intersection:
            _keep_only_strict_intersections(handle, 1)
    return handle


def _replace_segments_with_cuts(handle: GeomOperationHandle, shape_idx: int) -> None:
    """Split the segments that have intersection points at their intersection
    points.

    Args:
        handle: The handle to the data structure for geometric operations.
        shape_idx: The index (0 or 1) of the shape whose segments shall be split.
    """
    idx_segs_intersections = 0
    idx_atoms_intersections = 0
    while idx_atoms_intersections < len(handle.atoms_intersections[shape_idx]):
        if handle.atoms_intersections[shape_idx][idx_atoms_intersections]:
            n = _replace_segment_with_cuts(
                handle=handle,
                shape_idx=shape_idx,
                segment_idx=idx_segs_intersections,
                idx_atoms_intersections=idx_atoms_intersections,
            )
            idx_segs_intersections += n
            handle.number_cuts_performed[shape_idx] += n - 1
        else:
            handle.segs_intersections[shape_idx].append([None, None])
            idx_segs_intersections += 1
        idx_atoms_intersections += 1


def _replace_segment_with_cuts(
    handle: GeomOperationHandle,
    shape_idx: int,
    segment_idx: int,
    idx_atoms_intersections: int,
) -> int:
    """Split a segment at its intersection points.

    Args:
        shape_idx: The index (0 or 1) of the shape whose segment shall be split.
        segment_idx: The index of the segment that shall be split.
        idx_atoms_intersections: The index of the segment that shall be split, but for
            the `atoms_intersections[]` list.

    Returns:
        The number of segments after the cut.
    """
    segment = handle.atoms[shape_idx][segment_idx]
    points = handle.atoms_intersections[shape_idx][idx_atoms_intersections]
    cut_segments: list[GeomArc] | list[GeomLine]
    if isinstance(segment, GeomArc):
        cut_segments, intersections = _create_arcs_from_arc_and_points(
            arc=segment,
            points=points,
            min_segment_length=handle.min_segment_length,
            tol=handle.tol,
        )
    elif isinstance(segment, GeomLine):
        cut_segments, intersections = _create_lines_from_line_and_points(
            line=segment,
            points=points,
            min_segment_length=handle.min_segment_length,
            tol=handle.tol,
        )
    else:  # isinstance(segment, GeomCircle):
        cut_segments, intersections = _create_arcs_from_circle_and_points(
            circle=segment,
            points=points,
            min_segment_length=handle.min_segment_length,
            tol=handle.tol,
        )
        # Splitting up a circle in arcs creates an equal number of segments as there
        # are cuts (unlike cutting a line or an arc, which creates +1 segments than
        # there were cuts). To account for it we add 1 cut to the counter:
        handle.number_cuts_performed[shape_idx] += 1
    # Replace the old segment with the new ones:
    num_cut_segments = len(cut_segments)
    handle.atoms[shape_idx] = (
        handle.atoms[shape_idx][:segment_idx]
        + cut_segments
        + handle.atoms[shape_idx][segment_idx + 1:]  # fmt: skip  # NOQA
    )
    handle.atoms_inside_other_shape[shape_idx] = (
        handle.atoms_inside_other_shape[shape_idx][:segment_idx]
        + [None] * num_cut_segments
        + handle.atoms_inside_other_shape[shape_idx][segment_idx + 1:]  # fmt: skip  # NOQA
    )
    handle.segs_intersections[shape_idx].extend(intersections[-num_cut_segments:])

    return num_cut_segments


def _test_if_segments_inside_other_shape(
    handle: GeomOperationHandle, shape_idx: int
) -> None:
    """Go through all segments of the given shape and check if they are inside or
    outside of the other shape.

    Args:
        shape_idx: The number of the shape (0 or 1) whose segments shall be checked.
    """
    other_shape = handle.shape[(shape_idx + 1) % 2]
    # If the other shape is open, then all our segments are outside the other shape:
    if not isinstance(other_shape, GeomShapeClosed):
        for i in range(len(handle.atoms_inside_other_shape[shape_idx])):
            handle.atoms_inside_other_shape[shape_idx][i] = False
        return
    # Test if we have a zero-shape (i.e. a shape that has been erased out because of
    # too small dimentions):
    if not len(handle.atoms[shape_idx]):
        return

    atoms_inside_other_shape = handle.atoms_inside_other_shape[shape_idx]
    segs_intersections = handle.segs_intersections[shape_idx]
    atoms = handle.atoms[shape_idx]
    seg_inside = other_shape.is_point_inside_self(
        point=atoms[0].mid, strictly_inside=True, tol=handle.tol
    )
    atoms_inside_other_shape[0] = seg_inside
    # Testing whether a point is inside another shape is a time costly operation for
    # polygons and compound polygons. For these, we minimize the number of times that
    # `is_point_inside_self()` is called by assigning all segments that are on the
    # same side (either inside or outside) of the other shape the same "inside/
    # outside" value:
    if isinstance(other_shape, GeomPolygon | GeomCompoundPolygon):
        for i in range(1, len(handle.segs_intersections[shape_idx])):
            if (
                segs_intersections[i][0] is not None
                or segs_intersections[i - 1][1] is not None
            ):
                seg_inside = other_shape.is_point_inside_self(
                    point=atoms[i].mid, strictly_inside=True, tol=handle.tol
                )
            atoms_inside_other_shape[i] = seg_inside
    else:
        for i in range(1, len(handle.segs_intersections[shape_idx])):
            atoms_inside_other_shape[i] = other_shape.is_point_inside_self(
                point=atoms[i].mid, strictly_inside=True, tol=handle.tol
            )


def _keep_only_strict_intersections(
    handle: GeomOperationHandle, shape_idx: int
) -> None:
    """Go through all segments and merge those segments that were split by an
    intersection that turns out to be not a strict intersection. These are segments
    that lie on the same side of the other shape.

    Args:
        shape_idx: The number of the shape (0 or 1) whose segments shall be
        potentially merged.
    """
    # The notion of "inside/outside" makes no sense for segment intersections.
    # In these cases we end the function here already:
    if isinstance(handle.shape[(shape_idx + 1) % 2], GeomShapeOpen):
        return
    # If there are no intersections there is nothing to be done here:
    if not handle.intersections:
        return
    # Iterate through each segment and check if the next segment is on the same side
    # (inside or outside) of the other segment. If so, merge them, if it makes
    # sense:
    i = 0
    segs_intersections = handle.segs_intersections[shape_idx]
    while i < len(segs_intersections):
        atoms_inside = handle.atoms_inside_other_shape[shape_idx]
        i2 = (i + 1) % len(segs_intersections)
        if segs_intersections[i] and segs_intersections[i2]:
            if atoms_inside[i] == atoms_inside[i2]:
                n = _merge_segments(handle, shape_idx, i, i2)
                handle.number_cuts_performed[shape_idx] -= n
                i -= n
        i += 1
        if len(segs_intersections) == 0:
            break
    # Test for special case: all segments are either inside or outside of the other
    # shape, the intersection points are just touching points and we can remove
    # them:
    atoms_inside_other_shape = handle.atoms_inside_other_shape[shape_idx]
    if all(atoms_inside_other_shape) or not any(atoms_inside_other_shape):
        handle.intersections.clear()


def _merge_segments(
    handle: GeomOperationHandle, shape_idx: int, seg_idx1: int, seg_idx2: int
) -> int:
    """Merge two segements if they are of the same type, continuous and have the
    same center and radius in the case of arcs or the same direction in the case of
    lines).

    Args:
        shape_idx: The number of the shape (0 or 1) whose segments shall be
        potentially merged.
        seg_idx1: The number of the first segment.
        seg_idx2: The number of the second segment.

    Returns:
        The number of intersections that can be removed as a result of a segment
        merge (either 0, 1 or 2). If two arcs are merged to a circle, then 2
        intersections can be removed (in `_keep_only_strict_intersections()`).
    """
    if isinstance(handle.atoms[shape_idx][seg_idx1], GeomArc) and isinstance(
        handle.atoms[shape_idx][seg_idx2], GeomArc
    ):
        return _merge_arcs(handle, shape_idx, seg_idx1, seg_idx2)
    elif isinstance(handle.atoms[shape_idx][seg_idx1], GeomLine) and isinstance(
        handle.atoms[shape_idx][seg_idx2], GeomLine
    ):
        return _merge_lines(handle, shape_idx, seg_idx1, seg_idx2)
    else:
        return 0


def _merge_arcs(
    handle: GeomOperationHandle, shape_idx: int, seg_idx1: int, seg_idx2: int
) -> int:
    """Merge two arcs if they are continuous and have the same center and radius.

    Args:
        shape_idx: The number of the shape (0 or 1) whose arcs shall be
        potentially merged.
        seg_idx1: The number of the first arc.
        seg_idx2: The number of the second arc.

    Returns:
        The number of intersections that can be removed as a result of an arcs
        merge (either 0, 1 or 2). If two arcs are merged to a circle, then 2
        intersections can be removed (in `_keep_only_strict_intersections()`).
    """
    # `_merge_segments()` already identified the two segments as being arcs:
    arc1 = cast(GeomArc, handle.atoms[shape_idx][seg_idx1])
    arc2 = cast(GeomArc, handle.atoms[shape_idx][seg_idx2])
    if (
        arc1.center.is_equal(point=arc2.center, tol=handle.tol)
        and abs(arc1.radius - arc2.radius) <= handle.tol
    ):
        if arc1.start.is_equal(point=arc2.end, tol=handle.tol):
            # Arc2 comes before arc1 when sorting clockwise.
            arc1.set_start(arc2.start)
        elif arc1.end.is_equal(point=arc2.start, tol=handle.tol):
            pass  # All good, arc1 comes before arc2 when sorting clowckwise.
        else:
            return 0  # Arc1 anc arc2 are not continuous. We cannot merge.
        arc1.angle += arc2.angle
        del handle.atoms[shape_idx][seg_idx2]
        del handle.atoms_inside_other_shape[shape_idx][seg_idx2]
        del handle.segs_intersections[shape_idx][seg_idx2]
        handle.remove_intersection(point=arc2.start)
        # Special case: the arc angle is 360°: we can make a circle and remove the
        # last intersection point from the list:
        if abs(arc1.angle - 360) <= handle.tol:
            circle = GeomCircle(shape=arc1)
            handle.atoms[shape_idx][seg_idx1] = circle
            del handle.segs_intersections[shape_idx][seg_idx1]
            handle.remove_intersection(point=arc2.end)
            return 2
        return 1
    return 0  # We cannot merge as the radius or centers differ.


def _merge_lines(
    handle: GeomOperationHandle, shape_idx: int, seg_idx1: int, seg_idx2: int
) -> int:
    """Merge two lines if they are continuous and have the same direction.

    Args:
        shape_idx: The number of the shape (0 or 1) whose lines shall be
        potentially merged.
        seg_idx1: The number of the first line.
        seg_idx2: The number of the second line.

    Returns:
        The number of intersections that can be removed as a result of a line
        merge (either 0, 1).
    """
    # `_merge_segments()` already identified the two segments as being lines:
    line1 = cast(GeomLine, handle.atoms[shape_idx][seg_idx1])
    line2 = cast(GeomLine, handle.atoms[shape_idx][seg_idx2])
    if line1.end.is_equal(
        point=line2.start, tol=handle.tol
    ) and line1.unit_direction.is_equal(point=line2.unit_direction, tol=handle.tol):
        line1.end = line2.end
        del handle.atoms[shape_idx][seg_idx2]
        del handle.atoms_inside_other_shape[shape_idx][seg_idx2]
        del handle.segs_intersections[shape_idx][seg_idx2]
        handle.remove_intersection(point=line2.start)
        return 1
    else:
        return 0


def _create_arcs_from_arc_and_points(
    arc: GeomArc,
    points: list[Vector2D],
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> tuple[list[GeomArc], list[list[Vector2D | None]]]:
    """Splits up an arc at the given (intersection) points.

    Args:
        arc: The orignial arc.
        points: The list of (intersection) points at which the arc is to be split.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the cut operation is shorter than `min_segment_length`, it is
            omitted from the results.
        tol: The distance in mm that two points are allowed to be away from each
            other and still be considered identical.

    Returns: A tuple containing the sorted list of the new arc segments and
        a list containing two points. The two points are the start and end points
        corresponding to each arc segment of the other list. If an arc does not
        start or end on an intersection point, then its corresponding start or end
        point in that list is set to `None`.
    """
    sorted_pts = arc.sort_points_relative_to_start(points, tol)
    start = arc.start
    end = arc.end
    radius = arc.radius
    insert_start = False if start.is_equal(sorted_pts[0][2]) else True
    insert_end = False if end.is_equal(sorted_pts[-1][2]) else True
    pts_or_none = cast(list[tuple[float, float, Vector2D | None]], sorted_pts)
    if insert_start:
        pts_or_none.insert(0, (radius, 0, None))
    if insert_end:
        pts_or_none.append((radius, arc.angle, None))
    arcs: list[GeomArc] = []
    intersections: list[list[Vector2D | None]] = [[None, None]] * (len(pts_or_none) - 1)
    for i in range(len(pts_or_none) - 1):
        new_arc = GeomArc(
            center=arc.center,
            start=arc.start.rotated(pts_or_none[i][1], origin=arc.center),
            angle=pts_or_none[i + 1][1] - pts_or_none[i][1],
        )
        # Only add arc segments that are equal or larger than `min_segment_length`.
        if arc.radius * abs(math.radians(new_arc.angle)) >= min_segment_length:
            arcs.append(new_arc)
            intersections[i] = [pts_or_none[i][2], pts_or_none[i + 1][2]]
    return (arcs, intersections)


def _create_arcs_from_circle_and_points(
    circle: GeomCircle,
    points: list[Vector2D],
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> tuple[list[GeomArc], list[list[Vector2D | None]]]:
    """Splits up a circle at the given (intersection) points.

    Args:
        circle: The orignial circle.
        points: The list of (intersection) points at which the circle is to be
            split.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the cut operation is shorter than `min_segment_length`, it is
            omitted from the results.
        tol: The distance in mm that two points are allowed to be away from each
            other and still be considered identical.

    Returns: A tuple containing the sorted list of the new arc segments and
        a list containing two points. The two points are the start and end points
        corresponding to each arc segment of the other list. If an arc does not
        start or end on an intersection point, then its corresponding start or end
        point in that list is set to `None`.
    """
    # From the circle, create an arc that starts in the first intersection point
    arc = GeomArc(center=circle.center, start=points[0], angle=360)
    point = points[0]
    del points[0]
    intersections: list[list[Vector2D | None]]
    if len(points):
        arcs, intersections = _create_arcs_from_arc_and_points(
            arc=arc, points=points, min_segment_length=min_segment_length, tol=tol
        )
        intersections[0][0] = point
        intersections[-1][1] = point
    else:
        arcs = [arc]
        intersections = [[point, point]]
    return (arcs, intersections)


def _create_lines_from_line_and_points(
    line: GeomLine,
    points: list[Vector2D],
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> tuple[list[GeomLine], list[list[Vector2D | None]]]:
    """Splits up a line at the given (intersection) points.

    Args:
        line: The orignial line.
        points: The list of (intersection) points at which the line is to be split.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the cut operation is shorter than `min_segment_length`, it is
            omitted from the results.
        tol: The distance in mm that two points are allowed to be away from each
            other and still be considered identical.

    Returns: A tuple containing the sorted list of the new line segments and
        a list containing two points. The two points are the start and end points
        corresponding to each line segment of the other list. If an line does not
        start or end on an intersection point, then its corresponding start or end
        point in that list is set to `None`.
    """
    sorted_pts = line.sort_points_relative_to_start(points)
    sorted_intersections: list[Vector2D | None] = [p.copy() for p in sorted_pts]
    start = line.start
    end = line.end
    if not start.is_equal(sorted_pts[0], tol):
        sorted_pts.insert(0, line.start)
        sorted_intersections.insert(0, None)
    if not end.is_equal(sorted_pts[-1], tol):
        sorted_pts.append(line.end)
        sorted_intersections.append(None)
    lines: list[GeomLine] = []
    intersections: list[list[Vector2D | None]] = []
    for i in range(len(sorted_pts) - 1):
        line = GeomLine.from_vector2d(start=sorted_pts[i], end=sorted_pts[i + 1])
        # Only add line segments that are equal or larger than `min_segment_length`.
        if line.length >= min_segment_length:
            lines.append(line)
            intersections.append([sorted_intersections[i], sorted_intersections[i + 1]])
    return (lines, intersections)
