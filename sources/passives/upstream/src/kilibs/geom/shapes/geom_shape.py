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

"""Abstract base classes of the geometric shapes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Self

from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vector2D

# Using TYPE_CHECKING to only import these for type checking, but not at runtime:
if TYPE_CHECKING:
    from .geom_shape_alias import GeomShapesAtomic, GeomShapesNative


class GeomShape(ABC):
    """The base class of all shapes."""

    def __init__(self, shape: GeomShape | None = None) -> None:
        """Create an instance of this class.

        Args:
            shape: An other instance of the same class from which the parameters are
                copied.
        """
        raise NotImplementedError(
            f"`__init__()` not implemented for {self.__class__.__name__}."
        )

    def copy(self) -> Self:
        """Create a copy of itself."""
        return self.__class__(shape=self)

    def get_atomic_shapes(self) -> Sequence[GeomShapesAtomic]:
        """Decompose this shape to its atomic shapes (of type `GeomArc`, `GeomCircle`
        and `GeomLine`) and return them in a list.
        """
        # Note: atomic shapes must redefine this function by returning a list containing
        # `self`.
        atomic_shapes: list[GeomShapesAtomic] = []
        for basic_shape in self.get_shapes():
            atomic_shapes += basic_shape.get_atomic_shapes()
        return atomic_shapes

    def get_native_shapes(self) -> Sequence[GeomShapesNative]:
        """Decompose this shape to its basic shapes (all atomic shapes plus
        `GeomRectangle`, `GeomPolygon` and `GeomCompoundPolygon`) and return them in a
        list.
        """
        # Note: basic shapes must redefine this function by returning a list containing
        # `self`.
        native_shapes: list[GeomShapesNative] = []
        for native_shape in self.get_shapes():
            native_shapes += native_shape.get_native_shapes()
        return native_shapes

    def get_shapes(self) -> Sequence[GeomShape]:
        """Return a list of more elementary shapes that this shape is composed of.

        Note:
            For closed shapes, the shapes must be sorted so that they describe the
            contour continuously in a clockwise order (in the left-hand coordinate
            system that is used in layouts), ideally starting in the top-left corner.
        """
        # Note: non-basic shapes must redefine this function.
        return [self]

    def translate(self, vector: Vector2D) -> Self:
        """Move the shape.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated shape.
        """
        raise NotImplementedError("Method translate() not implemented.")

    def translated(self, vector: Vector2D) -> Self:
        """Create a copy of itself and move it.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated copy.
        """
        return self.copy().translate(vector=vector)

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the shape around a given point.

        Args:
            angle: Rotation angle ind egrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated shape.
        """
        raise NotImplementedError("Method rotate() not implemented.")

    def rotated(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Create a copy of itself and rotate it.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated copy.
        """
        return self.copy().rotate(angle=angle, origin=origin)

    def bbox(self) -> BoundingBox:
        """Return the bounding box."""
        # Note: basic shapes must redefine this function.
        bb = BoundingBox()
        for shape in self.get_shapes():
            bb.include_bbox(bbox=shape.bbox())
        return bb

    def is_point_on_self(
        self,
        point: Vector2D,
        exclude_segment_ends: bool = False,
        tol: float = TOL_MM,
    ) -> bool:
        """Check if a point is on the outline.

        Args:
            point: The coordinates (in mm) of the point.
            exclude_segment_ends: If `True` then end points within `tol` distance are
                excluded, otherwise end points are included from the outline.
            tol : Distance in mm that the point is allowed to be away from the outline
                while still being considered to lay on the outline.

        Returns:
            `True` if the point is considered to be on the outline within the given
            tolerance, `False` otherwise.
        """
        for segment in self.get_atomic_shapes():
            if segment.is_point_on_self(
                point=point, exclude_segment_ends=exclude_segment_ends, tol=tol
            ):
                return True
        return False

    def __str__(self) -> str:
        """Return a string representation of the shape."""
        return self.__repr__()

    @abstractmethod
    def __repr__(self) -> str:
        """Return the string representation.

        Returns::
            The string representation of the shape. This is the text that is shown for
            example in the debugger when displaying the value of a shape class in a
            single line.
        """
        ...


class GeomShapeClosed(GeomShape):
    """The base class for all closed shapes."""

    def inflated(self, amount: float, tol: float = TOL_MM) -> Self:
        """Create a copy of itself and inflate or deflate it.

        Args:
            amount: The amount in mm by which the shape is inflated (when amount is
                positive) or deflated (when amount is negative).
            tol: Maximum negative dimension in mm that a segment of the shape is allowed
                to have after the deflation without causing a `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in segments with
                negative dimensions a `ValueError` is raised.

        Returns:
            The copy of the shape after the inflation/deflation.
        """
        return self.copy().inflate(amount=amount, tol=tol)

    @abstractmethod
    def inflate(self, amount: float, tol: float = TOL_MM) -> Self:
        """Inflate or deflate the shape by 'amount'.

        Args:
            amount: The amount in mm by which the shape is inflated (when amount is
                positive) or deflated (when amount is negative).
            tol: Maximum negative dimension in mm that a segment of the shape is allowed
                to have after the deflation without raising a `ValueError`.

        Raises:
            ValueError: If the deflation operation would result in segments with
                negative dimensions a `ValueError` is raised.

        Returns:
            The shape after the inflation/deflation.
        """
        ...

    @abstractmethod
    def is_point_inside_self(
        self, point: Vector2D, strictly_inside: bool = True, tol: float = TOL_MM
    ) -> bool:
        """Check if a point is on or inside the shape.

        Args:
            point: The coordinates (in mm) of the point.
            strictly_inside: If `True` points on the outline (within `tol` distance) are
                considered to be outside.
            tol: Distance in mm that a point is allowed to be away from the outline and
                still be considered as being on the outline.

        Returns:
            `True` if the point is considered to be inside the shape, `False`
            otherwise.
        """
        raise NotImplementedError(
            f"`is_point_inside_self()` not implemented for {self.__class__.__name__}."
        )


class GeomShapeOpen(GeomShape):
    """The base class for all open shapes."""

    pass
