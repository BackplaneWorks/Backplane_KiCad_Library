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

"""Keepout function."""

from collections.abc import Iterable

from kilibs.geom import (
    GeomArc,
    GeomCircle,
    GeomLine,
    GeomRectangle,
    GeomShapes,
)

from ..tolerances import MIN_SEGMENT_LENGTH, TOL_MM
from .intersection_points import intersect_handler

_subtract_bypass_use = True
"""Stores whether the subtract bypass shall be used or not."""

_subtract_bypass_hits = 0
"""Stores how many times the bypass successfully reduced the computational effort."""

_subtract_bypass_misses = 0
"""Stores how many times the bypass failed to reduce the computational effort."""


def subtract_many(
    subject_shape: GeomShapes,
    clip_shapes: Iterable[GeomShapes],
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> list[GeomShapes]:
    r"""Subtract one or several shapes from the subject shape.

    Args:
        subject_shape: The shape to clipped by the operation.
        clip_shapes: The shapes that are used to clip the subject shape.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the subtract operation is shorter than `min_segment_length`, it is
            omitted from the results.
        tol: Tolerance used to dertemine if the two points are equal.

    Returns:determine
        If the subject shape is fully outside of the clip shapes, then the subject shape
        is returned. If the subject shape is fully inside of the clip shapes, then
        nothing is returned.
        Otherwise, the subject shape is decomposed to its atomic shapes and a list
        containing the parts of the atomic shapes that are not inside of the clip shapes
        is returned.

    Example:
        When the subject shape is a line and the clip shapes are 2 rectangles :

    .. aafig::
            +----+      +----+
            |    |      |    |
        ----+----+------+----+-----
            |    |      |    |
            +----+      +----+

    The result would be:

    .. aafig::
        ----      ------      -----
    """
    shapes = [subject_shape]
    for ko in clip_shapes:
        kept_out_shapes: list[GeomShapes] = []
        for shape in shapes:
            kept_out_shapes.extend(subtract(shape, ko, min_segment_length, tol))
        shapes = kept_out_shapes
    return shapes


def subtract(
    subject_shape: GeomShapes,
    clip_shape: GeomShapes,
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> list[GeomShapes]:
    r"""Subtract one shape from another one.

    Args:
        subject_shape: The shape to clipped by the operation.
        clip_shape: The shape that is used to clip the other shape (subject shape).
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the subtract operation is shorter than `min_segment_length`, it is
            omitted from the results.
        tol: Tolerance used to dertemine if the two points are equal.

    Returns:determine
        If `subject_shape` is fully outside of `clip_shape`, then a list containing
        `subject_shape` is returned. If `subject_shape` is fully inside of `clip_shape`,
        then an empty list is returned. Otherwise, `subject_shape` is decomposed to its
        atomic shapes and a list containing the parts of the atomic shapes that are not
        inside of `clip_shape` is returned.

    Example:
        When `subtract()` is called on 3 different lines with a clip shape in the form
        of a rectangle:

    .. aafig::
        +--------------+
        |   -----(A)   |
      --+--------------+---(B)
        |              |   -----(C)
        +--------------+

    The result would be:

    .. aafig::
        +--------------+
        |              |
      --+              +---(B)
        |              |   -----(C)
        +--------------+
    """
    # For the subtract() operation we only need shape 1 to be cut:

    # Check if there are obvious bypasses to accelerate the subtract operation:
    global _subtract_bypass_use
    if _subtract_bypass_use:
        ret = _subtract_bypasses(subject_shape, clip_shape, tol)
        if ret is not None:
            return ret
    handle = intersect_handler(
        shape1=subject_shape,
        shape2=clip_shape,
        strict_intersection=True,
        cut_also_shape_2=False,
        min_segment_length=min_segment_length,
        tol=tol,
    )
    if handle.number_cuts_performed[0] == 0 and not handle.intersections:
        if handle.atoms_inside_other_shape[0][0] is False:
            handle.kept_out_shapes = [handle.shape[0]]
        else:
            handle.kept_out_shapes = []
    else:
        for i, inside in enumerate(handle.atoms_inside_other_shape[0]):
            if not inside:
                handle.kept_out_shapes.append(handle.atoms[0][i])
    return handle.kept_out_shapes


def _subtract_bypasses(
    shape_to_keep_out: GeomShapes,
    subtract: GeomShapes,
    tol: float = TOL_MM,
) -> list[GeomShapes] | None:
    """Simple checks that accelerate the subtraction testing.

    Returns:
        `None` if the accelerated tests could not determine whether the suctraction
        impacts the other shape or not, or, if an accelerated test was successful,
        then the shape that's kept out is returned.
    """
    global _subtract_bypass_hits
    global _subtract_bypass_misses
    global _subtract_bypass_use
    if isinstance(subtract, GeomRectangle):
        bb_rect = subtract.bbox()
        if bb_rect.min is None or bb_rect.max is None:
            return [shape_to_keep_out]
        if isinstance(shape_to_keep_out, GeomLine):
            if shape_to_keep_out.start.x < shape_to_keep_out.end.x:
                left = shape_to_keep_out.start.x
                right = shape_to_keep_out.end.x
            else:
                right = shape_to_keep_out.start.x
                left = shape_to_keep_out.end.x
            if shape_to_keep_out.start.y < shape_to_keep_out.end.y:
                top = shape_to_keep_out.start.y
                bottom = shape_to_keep_out.end.y
            else:
                bottom = shape_to_keep_out.start.y
                top = shape_to_keep_out.end.y
            if (
                bb_rect.min.x + tol >= right
                or bb_rect.max.x - tol <= left
                or bb_rect.min.y + tol >= bottom
                or bb_rect.max.y - tol <= top
            ):
                _subtract_bypass_hits += 1
                return [shape_to_keep_out]
        elif isinstance(shape_to_keep_out, GeomArc | GeomCircle):
            radius = shape_to_keep_out.radius
            if (
                bb_rect.min.x + tol >= shape_to_keep_out.center.x + radius
                or bb_rect.max.x - tol <= shape_to_keep_out.center.x - radius
                or bb_rect.min.y + tol >= shape_to_keep_out.center.y + radius
                or bb_rect.max.y - tol <= shape_to_keep_out.center.y - radius
            ):
                _subtract_bypass_hits += 1
                return [shape_to_keep_out]
    _subtract_bypass_misses += 1
    # Turn off the bypass if we see that for this generator it is not useful:
    if (
        _subtract_bypass_misses > 20
        and _subtract_bypass_hits / _subtract_bypass_misses < 2
    ):
        _subtract_bypass_use = False
    return None
