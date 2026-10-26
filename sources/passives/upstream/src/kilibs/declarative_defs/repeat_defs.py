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
"""Classes for transformers and repeated definitions."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Any, cast

from kilibs.geom import Vector2D

from . import evaluable_defs as EDs


@dataclass
class Transformation:
    """This is a transformation that can be applied to an object.

    Exactly *how* the object is transformed is up to the calling code.
    """

    offset: Vector2D | None = None
    """Move the object by this amount."""

    rotation_angle: float | None = None
    """CCW rotation, in degrees."""
    mirror_x: float | None = None
    """The object should be mirrored in x about this point."""
    mirror_y: float | None = None
    """The object should be mirrored in y about this point.

    You can set both, which is equivalent to a 180 degree rotation about the point
    (mirror_x, mirror_y), but it may be more convenient for the calling code to do 1 or
    2 flips.
    """


class Transformer(ABC):
    """Some kind of transformation that can be applied to a point."""

    @abstractmethod
    def apply(self, pt: Vector2D) -> Transformation:
        """Apply the transformation to the point.

        Args:
            pt: The point.

        Returns:
            An instance of `Transformation` containing the details of the
            transformation.
        """
        raise NotImplementedError("Transformer.apply() must be implemented")


class Translation(Transformer):
    """Move the object by a given amount."""

    offset: Vector2D
    """The distance and direction by which to move an object."""

    def __init__(self, offset: Vector2D):
        """Create a `Translation` transformation.

        Args:
            offset: The distance and direction by which to move an object.
        """
        self.offset = offset

    def apply(self, pt: Vector2D) -> Transformation:
        """Apply the translation to the point.

        Args:
            pt: The point.

        Returns:
            The transformation details of the translation.
        """
        return Transformation(offset=self.offset)

    def __repr__(self):
        """A string representation of the `Transformation` class."""
        return f"Translation(offset={self.offset})"


class Rotation(Transformer):
    """Rotate the object by a given amount."""

    rotation_center: Vector2D
    """The center of rotation."""
    rotation_angle: float
    """The rotation angle."""
    rotate_elements: bool
    """When true, the returned `Transformation` includes the rotation angle, otherwise
    it is `None` and the transformation is just a translation.
    """

    def __init__(
        self, rotation_center: Vector2D, rotation_angle: float, rotate_elements: bool
    ):
        """Create a `Rotation` transformation.

        Args:
            rotation_center: The center of the rotation.
            rotation_angle: The angle of the rotation.
            rotation_elements: When true, the returned `Transformation` includes the
                rotation angle, otherwise it is `None` and the transformation is just a
                translation.
        """
        self.rotation_center = rotation_center
        self.rotation_angle = rotation_angle
        self.rotate_elements = rotate_elements

    def apply(self, pt: Vector2D) -> Transformation:
        """Apply the rotation to the point.

        Args:
            pt: The point.

        Returns:
            The transformation details of the rotation.
        """
        vec_to_pt = pt - self.rotation_center
        new_vec = vec_to_pt.rotated(self.rotation_angle)

        angle = self.rotation_angle if self.rotate_elements else None
        return Transformation(offset=new_vec - vec_to_pt, rotation_angle=angle)

    def __repr__(self):
        """A string representation of the `Transformation` class."""
        return (
            f"Rotation(center={self.rotation_center}, "
            f"angle={self.rotation_angle}, rotate_elements={self.rotate_elements})"
        )


class Mirror(Transformer):
    """Mirror the object on a given axis."""

    mirror_x: float | None
    """The location on the x-axis of the mirror parallel to the y-axis. If `None` then
    no mirroring is applied.
    """
    mirror_y: float | None
    """The location on the y-axis of the mirror parallel to the x-axis. If `None` then
    no mirroring is applied.
    """

    def __init__(self, mirror_x: float | None, mirror_y: float | None):
        """Create a `Mirror` transformation.

        Args:
            mirror_x: Mirror the points on the y-axis offset by `mirror_x`. `None` if no
                mirroring on the y-axis is desired.
            mirror_y: Mirror the points on the x-axis offset by `mirror_y`. `None` if no
                mirroring on the x-axis is desired.
        """
        self.mirror_x = mirror_x
        self.mirror_y = mirror_y

    def apply(self, pt: Vector2D) -> Transformation:
        """Apply the mirror operation to the point.

        Args:
            pt: The point.

        Returns:
            The details of the mirroring transformation.
        """
        new_pt = Vector2D(pt.x, pt.y)
        if self.mirror_x is not None:
            new_pt.x = self.mirror_x - (new_pt.x - self.mirror_x)

        if self.mirror_y is not None:
            new_pt.y = self.mirror_y - (new_pt.y - self.mirror_y)

        return Transformation(offset=new_pt - pt)


class RepeatDef(ABC):
    """Some definition that drives a repeat of some kind. Usually a grid, but could be
    circular or something else.

    These are usually constructed from some YAML specification.

    They generate a series of Transformations that should be applied to the object
    by the calling code (exactly what a Transformation does to an object may vary).
    """

    @abstractmethod
    def get_transformations(
        self,
        expr_evaluator: Callable[
            [EDs.EvaluableScalar.ExprType | EDs.EvaluableInt.ExprType], float | int
        ],
    ) -> Generator[Transformation | None, None, None]:
        """Yield the offsets for the repeat definition.

        If None is returned, it means "don't transform" for that instance (but there
        might be others coming), and the calling code should include the original object
        as-is.

        Args:
            expr_evaluator: A callable used to evaluate expressions within the repeat
                definition.

        Yields:
            A `Transformation` object to apply, or `None` for the original object.
        """
        raise NotImplementedError("RepeatDefinition.get_offsets() must be implemented")


class GridRepeatDef(RepeatDef):
    """The "usual" grid repeater. Repeats in a grid pattern with a given spacing and
    count.
    """

    spacing: EDs.EvaluableVector2D
    """The spacing between grid elements."""
    count: EDs.EvaluableVector2Int
    """The number of repetitions in the x and y directions."""
    reference_is: str
    """Specifies the reference point for the grid layout (e.g., "center", "left",
    "right", "top", "bottom").
    """
    omit_indexes: list[EDs.EvaluableVector2Int]
    """A list of grid indexes (x, y) to omit from the repetition."""

    def __init__(self, spec_dict: dict[str, Any]) -> None:
        """Create a `GridRepeatDef`.

        Args:
            spec_dict: The dictionary containing the specifications for the grid repeat.
                Expected keys include "spacing", "count", "reference_is", and optionally
                "omit".
        """
        self.spacing = EDs.EvaluableVector2D(spec_dict["spacing"])
        self.count = EDs.EvaluableVector2Int(spec_dict["count"])

        self.reference_is = spec_dict["reference_is"]

        self.omit_indexes = []
        if "omit" in spec_dict:
            if not isinstance(spec_dict["omit"], list):
                raise ValueError("Grid repeat omit must be a list")

            for omit in cast(list[list[EDs.EvaluableInt.ExprType]], spec_dict["omit"]):
                omit_xy = EDs.EvaluableVector2Int(omit)
                self.omit_indexes.append(omit_xy)

    def get_transformations(
        self, expr_evaluator: Callable[[str | int | float], float | int]
    ) -> Generator[Transformation, None, None]:
        """Yield the `Transformation` objects for each instance in the grid.

        Args:
            expr_evaluator: A callable used to evaluate expressions within the grid
                definition.

        Yields:
            The `Transformation` objects corresponding to the grid repeat definition.
        """

        # First, resolve the spacing and count expressions
        spacing = self.spacing.evaluate(expr_evaluator)
        count = self.count.evaluate(
            cast(Callable[[EDs.EvaluableInt.ExprType], int], expr_evaluator)
        )

        size = Vector2D(
            spacing.x * (count[0] - 1),
            spacing.y * (count[1] - 1),
        )

        omits: set[tuple[int, int]] = set()
        for omit in self.omit_indexes:
            omit = omit.evaluate(
                cast(Callable[[EDs.EvaluableInt.ExprType], int], expr_evaluator)
            )
            omits.add(omit)

        if self.reference_is == "center":
            offset = Vector2D(-size.x / 2, -size.y / 2)
        elif self.reference_is == "left":
            offset = Vector2D(0, -size.y / 2)
        elif self.reference_is == "right":
            offset = Vector2D(-size.x, -size.y / 2)
        elif self.reference_is == "top":
            offset = Vector2D(-size.x / 2, 0)
        else:  # self.reference_is == "bottom":
            offset = Vector2D(-size.x / 2, -size.y)

        for y in range(count[1]):
            for x in range(count[0]):

                if (x, y) in omits:
                    continue

                grid_pt = Vector2D(x * spacing.x, y * spacing.y)
                transform = Translation(offset=offset + grid_pt)
                yield transform


class CircularRepeatDef(RepeatDef):
    """Repeats an object in a circular pattern around a center point."""

    center: EDs.EvaluableVector2D
    """The center point of the circular repetition."""
    count: EDs.EvaluableInt
    """The number of repetitions, including the original."""

    def __init__(self, spec_dict: dict[str, Any]) -> None:
        """Create a `CircularRepeatDef`.

        Args:
            spec_dict (dict): The dictionary containing the specifications for the
            circular repeat. Expected keys include "center" and "count".
        """
        self.center = EDs.EvaluableVector2D(spec_dict["center"])
        self.count = EDs.EvaluableInt(spec_dict["count"])

    def get_transformations(
        self, expr_evaluator: Callable[[str | int | float], float | int]
    ) -> Generator[Transformation | None, None, None]:
        """Yield the `Transformation` objects for each object in the circle.

        Args:
            expr_evaluator: A callable used to evaluate expressions within the circular
            repeat definition.

        Yields:
            A `Rotation` transformation for each rotated instance, and `None` for the
            original (non-transformed) instance.
        """

        center = self.center.evaluate(expr_evaluator)
        count = self.count.evaluate(expr_evaluator)

        # The first one is the original, no transform
        yield None

        for i in range(1, count):
            angle = 360 / count * i
            yield Rotation(
                rotation_center=Vector2D(center.x, center.y),
                rotation_angle=angle,
                rotate_elements=True,
            )


class MirrorRepeatDef(RepeatDef):
    """Create a copy of the object mirrored along the x and/or y axis."""

    mirror_x: EDs.EvaluableScalar | None
    """The expression that defines the x-axis mirror. None for no x-axis mirror."""
    mirror_y: EDs.EvaluableScalar | None
    """The expression that defines the y-axis mirror. None for no y-axis mirror."""

    def __init__(self, spec_dict: dict[str, Any]):
        """Create a `MirrorRepeatDef`.

        Args:
            spec_dict: The dictionary containing the specifications for the mirror
                repeat. Expected keys are "x" and/or "y", whose values define the mirror
                planes.
        """
        self.mirror_x = None
        self.mirror_y = None

        if "x" in spec_dict:
            self.mirror_x = EDs.EvaluableScalar(spec_dict["x"])

        if "y" in spec_dict:
            self.mirror_y = EDs.EvaluableScalar(spec_dict["y"])

    def get_transformations(
        self, expr_evaluator: Callable[[str | int | float], float | int]
    ) -> Generator[Transformation | None, None, None]:
        """Yield the `Transformation` objects for the mirrored instances.

        Args:
            expr_evaluator: A callable used to evaluate expressions for the mirror
            planes.

        Yields:
            A `Mirror` object for each mirrored instance, and `None` for the original
            (non-mirrored) instance.
        """

        # First, resolve the spacing and count expressions
        mirror_x = (
            self.mirror_x.evaluate(expr_evaluator)
            if self.mirror_x is not None
            else None
        )
        mirror_y = (
            self.mirror_y.evaluate(expr_evaluator)
            if self.mirror_y is not None
            else None
        )

        # The original point doesn't need a transform at all
        # But we need to yield something so the original object is included
        yield None

        if self.mirror_x is not None:
            yield Mirror(mirror_x=mirror_x, mirror_y=None)

        if self.mirror_y is not None:
            yield Mirror(mirror_x=None, mirror_y=mirror_y)

        if self.mirror_x is not None and self.mirror_y is not None:
            yield Mirror(mirror_x=mirror_x, mirror_y=mirror_y)
