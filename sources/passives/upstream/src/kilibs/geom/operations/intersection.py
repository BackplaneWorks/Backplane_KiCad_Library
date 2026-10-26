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

"""Intersection function."""

from typing import cast

from kilibs.geom import (
    GeomArc,
    GeomCircle,
    GeomCompoundPolygon,
    GeomLine,
    GeomPolygon,
    GeomShapesAtomic,
    GeomShapesClosed,
)

from ..tolerances import MIN_SEGMENT_LENGTH, TOL_MM
from .intersection_points import intersect_handler
from .segment_util import has_arcs


def intersect(
    shape1: GeomShapesClosed,
    shape2: GeomShapesClosed,
    min_segment_length: float = MIN_SEGMENT_LENGTH,
    tol: float = TOL_MM,
) -> list[GeomShapesClosed]:
    r"""Intersect two shapes.

    Args:
        shape1: One of the 2 shapes to intersect.
        shape2: The other shape to intersect with the first one.
        min_segment_length: The minimum length of a segment. If a segment resulting
            from the `intersect()` operation is shorter than `min_segment_length`, it is
            omitted from the resulting shape.
        tol: Tolerance used to determine if the two points are equal.

    Returns:
        A list containing a polygon or compound polygon (if there are arcs in the
        resulting shape) describing the outline of the intersection of the two shapes.
        If the intersection area is composed of multiple, disconnected regions (e.g., if
        one or both input shapes are concave), the list will contain one resulting shape
        for each region.

    Example:
        When `intersect()` is called with two rounded rectangles as argument:

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
                 /-----+
                 |     |
                 +-----/
    """
    # For the intersect() operation we need both shapes to be cut up:
    handle = intersect_handler(
        shape1=shape1,
        shape2=shape2,
        strict_intersection=False,
        cut_also_shape_2=True,
        min_segment_length=min_segment_length,
        tol=tol,
    )
    cohesive_shapes: list[GeomShapesClosed] = []

    # We keep only the atoms that are inside the other shape as well as all segments of
    # both shapes that perfectly overlap (they are not counted as "inside the other
    # shape"):
    atoms_inside: list[GeomShapesAtomic] = []
    for i, atom in enumerate(handle.atoms[0]):
        if handle.atoms_inside_other_shape[0][i]:
            atoms_inside.append(atom)
        else:
            atom_type = type(atom)
            for other_atom in handle.atoms[1]:
                other_atom_type = type(other_atom)
                if atom_type == other_atom_type:
                    if atom.is_equal(other_atom):  # type: ignore
                        atoms_inside.append(other_atom)
                        break
    for i, atom in enumerate(handle.atoms[1]):
        if handle.atoms_inside_other_shape[1][i]:
            atoms_inside.append(atom)

    # Extract all circles:
    cohesive_shapes = [atom for atom in atoms_inside if isinstance(atom, GeomCircle)]

    # Extract all line and arc segments:
    segments = [atom for atom in atoms_inside if not isinstance(atom, GeomCircle)]

    # Extract cohesive shapes from the atoms:
    while segments:
        previous_segment = segments.pop()
        new_shape: list[GeomLine | GeomArc] = [previous_segment]
        while segments:
            # Find the next arc or line that describes a continuous contour:
            no_continuous_outline_found = True
            for i, segment in enumerate(segments):
                if segment.start.is_equal(previous_segment.end):
                    new_shape.append(segments.pop(i))
                    previous_segment = segment
                    no_continuous_outline_found = False
                    break
            if no_continuous_outline_found:
                raise RecursionError("No continous outline was found!")
            if new_shape[0].start.is_equal(new_shape[-1].end):
                if has_arcs(new_shape):
                    cohesive_shapes.append(GeomCompoundPolygon(new_shape))
                else:
                    cohesive_shapes.append(GeomPolygon(cast(list[GeomLine], new_shape)))
                break

    return cohesive_shapes
