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

"""Utility functions for line and arc segments."""

from kilibs.geom.shapes.geom_arc import GeomArc
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.tolerances import MIN_SEGMENT_LENGTH, TOL_MM, tol_deg
from kilibs.geom.vector import Vector2D


def are_lines_parallel(
    line1: GeomLine,
    line2: GeomLine,
    tol: float = TOL_MM,
) -> bool:
    """Check if two lines are parallel.

    Args:
        line1: The first line.
        line2: The other line.
        tol: Tolerance in mm used to determine if two segments are parallel.

    Returns:
        `True` if the lines are parallel, `False` otherwise.
    """
    # Note: The code is optimized for speed and thus uses "manual" implementations
    # of the various functions.
    # We use homogeneous coordinates here:
    l1_x, l1_y = (line1.start.y - line1.end.y, line1.end.x - line1.start.x)
    l2_x, l2_y = (line2.start.y - line2.end.y, line2.end.x - line2.start.x)

    # Cross product:
    ip_z = l1_x * l2_y - l1_y * l2_x

    if abs(ip_z) <= tol:
        return True
    else:
        return False


def are_arcs_on_same_circle(
    arc1: GeomArc,
    arc2: GeomArc,
    tol: float = TOL_MM,
) -> bool:
    """Check if two arcs line on the same circle..

    Args:
        arc1: The first arc.
        arc2: The other arc.
        tol: Tolerance in mm used to determine if two arcs share the same center
            and have the same radius.

    Returns:
        `True` if the lines are parallel, `False` otherwise.
    """
    # Note: The code is optimized for speed and thus uses "manual" implementations
    # of the various functions.
    if (
        abs(arc1.center.x - arc2.center.x) > tol
        or abs(arc1.center.y - arc2.center.y) > tol
        or abs(arc1.radius - arc2.radius) > tol
    ):
        return False
    else:
        return True


def remove_zero_length_segments(
    segments: list[GeomLine] | list[GeomLine | GeomArc],
    min_segment_length: float = MIN_SEGMENT_LENGTH,
) -> None:
    """Find the segments that have a lenght smaller than `min_segment_length` and remove
    them from the list

    Args:
        segments: The list of segments.
        min_semgent_length: Lines shorter than this are removed.
    """
    i = 0
    while i < len(segments):
        if segments[i].length < min_segment_length:
            del segments[i]
        else:
            i += 1


def keep_only_outer_outline(
    segments: list[GeomLine] | list[GeomLine | GeomArc],
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> bool:
    """Find the segments that are fully enclosed by the outer outline of the closed
    shape and remove them from the list.

    Args:
        segments: The list of segments that describe a closed shape in clockwise
            order, but potentially contain a segments that are fully enclosed by
            other segments. This list is modified in-situ, thus this function does
            not return anything.
        min_semgent_length: Lines shorter than this are also removed.
        tol: The tolerance in mm used to determine if the lines are parallel
            or if an intersection point close to one of the ends the segments is
            still considered to be on the segment or not.

    Returns:
        `True` if the outline is valid, `False` otherwise.
    """
    from .intersection_points_atomic_shapes import (
        get_intersection_points_of_atomic_shapes,
    )

    if len(segments) < 2:
        return False

    # Find the a segment that is certainly on the outer outline:
    bboxes = [segment.bbox() for segment in segments]
    left_most_segment_idx = 0
    left_most_segment_coordinate = bboxes[0].left
    for i, bbox in enumerate(bboxes):
        if bbox.left < left_most_segment_coordinate:
            left_most_segment_coordinate = bbox.left
            left_most_segment_idx = i
    # Iterate through all segment combinations (upper triangle without diagonal) and
    # find segments intersecting each other:
    i = 1
    while i < len(segments):
        j = 0
        while j < i:
            if i - j == 1 or (i == (len(segments) - 1) and j == 0):
                # For neighboring segments we are only interested in the strict
                # intersections:
                strict_intersection = True
            else:
                strict_intersection = False
            pt = get_intersection_points_of_atomic_shapes(
                segments[i],
                segments[j],
                exclude_tangents=False,
                exclude_segment_ends_shape1=strict_intersection,
                exclude_segment_ends_shape2=strict_intersection,
                infinite_line=False,
                tol=tol,
            )
            if pt:
                point = pt[0]
                # There are two ways that we could cut and remove the segments:
                # - either we remove all segments between j+1 (incl) and i (excl),
                # - or we remove all segments between i+1 (incl) and j (excl).
                # To know which way to cut and remove, we just have to make sure that
                # the outermost segment is part of the solution:
                if j < left_most_segment_idx and left_most_segment_idx < i:
                    segments[j].start = point
                    segments[i].end = point
                    if not strict_intersection:
                        # Only remove segments if we are currently analyzing
                        # non-neighbouring segments:
                        del segments[i+1:len(segments)]  # fmt: skip # NOQA
                        del segments[0:j]  # fmt: skip # NOQA
                        left_most_segment_idx -= j
                    i -= j
                    j = 1
                else:
                    segments[j].end = point
                    segments[i].start = point
                    if not strict_intersection:
                        # Only remove segments if we are currently analyzing
                        # non-neighbouring segments:
                        del segments[j+1:i]  # fmt: skip # NOQA
                    i = j + 1
                    j += 1
                if len(segments) <= 1:
                    return False
            else:
                j += 1
        i += 1
    return True


def merge_segments(
    segments: list[GeomLine] | list[GeomLine | GeomArc], tol: float = TOL_MM
) -> bool:
    """Merge colinear lines (i.e. lines that are just an extension of another
    line).

    Args:
        segments: The list of lines and arcs that define a closed shape in
            clockwise direction. This list is modified in-situ, thus this function
            does not return anything.
        tol: The tolerance in mm used to determine if the lines are parallel
            or if an intersection point close to one of the ends the segments is
            still considered to be on the segment or not.

    Returns:
        `True` if the outline is valid, `False` otherwise.
    """
    i = 0
    while i < len(segments):
        seg1, seg2 = segments[i - 1], segments[i]
        if isinstance(seg1, GeomLine) and isinstance(seg2, GeomLine):
            if are_lines_parallel(line1=seg1, line2=seg2, tol=tol):
                seg1.end = seg2.end
                del segments[i]
                if len(segments) <= 2:
                    return False
            else:
                i += 1
        elif isinstance(seg1, GeomArc) and isinstance(seg2, GeomArc):
            if are_arcs_on_same_circle(arc1=seg1, arc2=seg2, tol=tol):
                seg1.angle += seg2.angle
                del segments[i]
                if len(segments) <= 2:
                    return False
            else:
                i += 1
        else:
            i += 1
    return True


def is_segment_flipped_or_zero(
    seg: GeomLine | GeomArc, dir: Vector2D | int, tol: float
) -> bool:
    """Return whether a segment is flipped with respect to a given direction (Vector2D
    for `GeomLine` and `float` for `GeomArc`).

    Args:
        seg: The segment.
        dir: The direction.
        tol: The tolerance in mm used to determine if a segment has a zero length.

    Returns:
        `True` if the the segment is flipped or of zero length, `False` otherwise.
    """
    if isinstance(seg, GeomLine) and isinstance(dir, Vector2D):
        new_dir = seg.direction
        if abs(new_dir.x) > abs(new_dir.y):
            if new_dir.x * dir.x <= 0 or abs(new_dir.x) <= tol:
                return True
        else:
            if new_dir.y * dir.y <= 0 or abs(new_dir.y) <= tol:
                return True
    elif isinstance(seg, GeomArc) and isinstance(dir, int):
        if seg.angle * dir <= 0:
            return True
        tol_d = tol_deg(tol=tol, radius=seg.radius)
        if not tol_d:
            return True
        if abs(seg.angle) <= tol_d:
            return True
    return False


def has_arcs(segments: list[GeomLine | GeomArc]) -> bool:
    """Check if a list contains arc segments.

    Args:
        segments: The list containing the segments to analyze.

    Return:
        `True` if the list contains an arc segment, `False` otherwise.
    """
    for segment in segments:
        if isinstance(segment, GeomArc):
            return True
    return False
