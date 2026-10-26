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

"""Class definition for a handle for geometric operations."""

from __future__ import annotations

from dataclasses import dataclass

from kilibs.geom import (
    GeomArc,
    GeomLine,
    GeomShapeOpen,
    GeomShapes,
    GeomShapesAtomic,
    Vector2D,
)
from kilibs.geom.tolerances import MIN_SEGMENT_LENGTH, TOL_MM


@dataclass
class GeomOperationHandle:
    """A handle class for geometric operations."""

    # Instance attributes:
    min_segment_length: float
    """Minimum length a segment is allowed to have. Segments smaller than that are
    removed from the solution space."""
    tol: float
    """Tolerance in mm used among other things to determine if two points are
    identical."""
    intersections: list[Vector2D]
    """List of intersection points."""
    shape: list[GeomShapes]
    """List containing the two shapes on which the geometric operations are
    performed."""
    atoms: list[list[GeomShapesAtomic]]
    """[For each shape] [a list containing the atomic shapes that the shape is composed
    of]."""
    segs: list[list[GeomArc | GeomLine]]
    """[For each shape] [a list containing the segments that the shape is composed of.
    This list is only used in the `unite()` operation after having ruled out the
    presence of GeomCircle elements in `atoms`.]"""
    atoms_intersections: list[list[list[Vector2D]]]
    """[For each shape] [for each atom] [the intersection points of that atom]."""
    segs_intersections: list[list[list[Vector2D | None]]]
    """[For each shape] [for each segment] [a list of two points]. If the segment's
    start point lies on an intersection, the first point (of the two points) is equal to
    the intersection point. Otherwise it is set to `None`. If the end point lies on an
    intersection, the second point (of the two points) is equal to the intersection
    point. Otherweise it is set to `None`.
    end point of the segment) c]."""
    atoms_inside_other_shape: list[list[bool | None]]
    """[For each shape] [for each atom of that shape] [whether that atom is inside or
    outside of the other shape]."""
    number_cuts_performed: list[int]
    """For each shape, the number of cuts performed on its segments during the geometric
    operation."""
    kept_out_shapes: list[GeomShapes]
    """Used by `keepout()`. It's a list containing the geometric shapes that are kept
    out."""
    strict_intersection: bool
    """Whether during the `intersect()` operation only strict intersections shall be
    considered or if also non-strict intersections shall be returned."""
    exclude_tangents: bool
    """Whether during the `intersect()` operation tangent points shall be excluded from
    the solution space or not."""
    exclude_segment_ends: list[bool]
    """Whether during the `intersect()` operation intersection points lying on the
    end points of the segments shall be excluded from the solution space or not."""

    def __init__(
        self,
        shape1: GeomShapes,
        shape2: GeomShapes,
        strict_intersection: bool = True,
        min_segment_length: float = MIN_SEGMENT_LENGTH,
        tol: float = TOL_MM,
    ) -> None:
        """Initialize an instance of `GeomOperationHandle`.

        Args:
            shape1: First shape to perform arithmetics on.
                For `cut()`, this is the shape that is cut.
                For `keepout()`, this is the shape that is to be kept out.
            shape2: Second shape to perform arithmetics on.
                For `cut()`, this is the shape that cuts.
                For `keepout()`, this is the shape that is used as keepout.
            strict_intersection: If `True`, then intersection points resulting from
                shapes that are tangent to another or from segments that have their
                beginning or their ending on the outline of the other shape are omitted
                from the results. If `False` then those points are included.
            min_segment_length: The minimum length of a segment. If a segment resulting
                from the cut operation is shorter than `min_segment_length`, it is
                omitted from the results.
            tol: Tolerance used to determine if the two points are equal.
        """
        self.min_segment_length = min_segment_length
        self.tol = tol
        self.intersections = []
        self.shape = [shape1, shape2]
        self.atoms = []
        self.segs = []
        for i in (0, 1):
            atoms = self.shape[i].get_atomic_shapes()
            # Create a new list (since we will modify it in here):
            self.atoms.append(list(atoms))
        # [For each shape] [for each segment of that shape] [the intersection points of
        # that segment]:
        self.atoms_intersections = [
            [[] for _ in range(len(self.atoms[0]))],
            [[] for _ in range(len(self.atoms[1]))],
        ]
        self.segs_intersections = [[], []]
        # [For each shape] [for each segment of that shape] whether that segment is
        # inside the other shape or not:
        self.atoms_inside_other_shape = [
            [None] * len(self.atoms[0]),
            [None] * len(self.atoms[1]),
        ]
        # [For each shape] how many cuts have been effectively performed to its
        # segments:
        self.number_cuts_performed = [0, 0]
        self.kept_out_shapes = []
        self.strict_intersection = strict_intersection
        self.exclude_tangents = self.strict_intersection
        # Segment ends of simple shapes like arcs and lines can be omitted already early
        # on in the calculation process (and thus accelerate the calculation). For
        # segments composing rectangles and polygons it is not that simple, hence the
        # distinction here:
        self.exclude_segment_ends = []
        for i in (0, 1):
            self.exclude_segment_ends.append(
                self.strict_intersection and isinstance(self.shape[i], GeomShapeOpen)
            )

    def add_intersections(
        self, intersections: list[Vector2D], idx_shape1: int, idx_shape2: int
    ) -> None:
        """Add intersection points to the internal lists of intersections.

        Args:
            intersections: The list of intersection points.
            idx_shape1: The index of the segment of shape 1 that has the intersections
                given in `intersections`.
            idx_shape2: The index of the segment of shape 2 that has the intersections
                given in `intersections`.
        """
        for new_intersection in intersections:
            self._add_intersection(
                new_intersection, self.atoms_intersections[0][idx_shape1]
            )
            self._add_intersection(
                new_intersection, self.atoms_intersections[1][idx_shape2]
            )
            self._add_intersection(new_intersection, self.intersections)

    def _add_intersection(
        self, new_intersection: Vector2D, intersection_list: list[Vector2D]
    ) -> None:
        """Add a single intersection point to the given list of intersections. If the
        point already exists in the list, the existing point is updated with the average
        value between the existing point and the new point instead of adding the new
        point.
        """
        new_intersection_added = False
        for old_intersection in intersection_list:
            if new_intersection.is_equal(point=old_intersection, tol=self.tol):
                pt_mid = (new_intersection + old_intersection) / 2
                old_intersection = pt_mid
                new_intersection_added = True
                break
        if not new_intersection_added:
            intersection_list.append(new_intersection)

    def remove_intersection(self, point: Vector2D) -> None:
        """Remove an intersection point from the internal list of intersections.

        Args:
            point: The point that shall be removed.
        """
        i = 0
        while i < len(self.intersections):
            if self.intersections[i].is_equal(point=point, tol=self.tol):
                del self.intersections[i]
                break
            else:
                i += 1

    def is_point_an_intersection(self, point: Vector2D) -> bool:
        """Return if the point is an intersection point or not."""
        for ip in self.intersections:
            if point.is_equal(ip, tol=self.tol):
                return True
        return False
