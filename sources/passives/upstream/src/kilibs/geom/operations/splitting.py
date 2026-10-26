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

"""Divide function."""

from kilibs.geom import GeomShapes

from ..tolerances import MIN_SEGMENT_LENGTH, TOL_MM
from .intersection_points import intersect_handler


def split(
    shape_to_split: GeomShapes,
    splitting_shape: GeomShapes,
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> list[GeomShapes]:
    """Split `shape_to_split` with `splitting_shape`.

    Args:
        splitting_shape: The shape that splits.
        shape_to_split: The shape that is to be split.
        strict_intersection: If `True`, then intersection points resulting from
            shapes that are tangent to another or from segments that have their
            beginning or their ending on the outline of the other shape are omitted
            from the results. If `False` then those points are included.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the split operation is shorter than `min_segment_length`, it is
            omitted from the results.
        tol: Tolerance used to determine if the two points are equal.
    Returns:
        A list containing the fragments of the split shape.
        If the shape has been split, the resulting line and arc segments are returned
        sorted by their proximity to the starting point of the segment.
    """
    # For the cut() operation we only need shape 1 to be cut:
    handle = intersect_handler(
        shape1=shape_to_split,
        shape2=splitting_shape,
        strict_intersection=True,
        cut_also_shape_2=False,
        min_segment_length=min_segment_length,
        tol=tol,
    )
    if handle.intersections:
        return list(handle.atoms[0])
    else:
        return [shape_to_split]
