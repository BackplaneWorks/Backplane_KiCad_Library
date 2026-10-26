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

"""Class for a bounding box."""

from __future__ import annotations

from kilibs.geom.vector import Vec2DCompatible, Vector2D


class BoundingBox:
    """A bounding box."""

    def __init__(
        self,
        corner1: Vec2DCompatible | None = None,
        corner2: Vec2DCompatible | None = None,
    ) -> None:
        """Initialize a bounding box with the given corner points.
        Passing None for both min and max will create a "null" bounding box that
        can't be used for much until more points are included.

        Args:
            corner1: Corner of the bounding box.
            corner2: Other corner of the bounding box.
        """

        # Instance attributes:
        self.min: Vector2D | None
        """The top left corner of the bounding box or `None` if uninitialized."""
        self.max: Vector2D | None
        """The bottom right corner of the bounding box or `None` if uninitialized."""

        if (corner1 is None) != (corner2 is None):
            raise ValueError("Must provide both corner1 and corner2 or neither")

        if corner1 is not None and corner2 is not None:
            corner1 = Vector2D(corner1)
            corner2 = Vector2D(corner2)
            self.min = Vector2D.from_floats(
                min(corner1.x, corner2.x), min(corner1.y, corner2.y)
            )
            self.max = Vector2D.from_floats(
                max(corner1.x, corner2.x), max(corner1.y, corner2.y)
            )
        else:
            self.min = None
            self.max = None

    @classmethod
    def from_vector2d(
        cls,
        min: Vector2D,
        max: Vector2D,
    ) -> BoundingBox:
        """Initialize a bounding box from the given minimum and maximum points.

        Args:
            min: Top left corner of the bounding box.
            max: Bottom right corner of the bounding box.
        """
        bbox = BoundingBox.__new__(BoundingBox)
        bbox.min = min
        bbox.max = max
        return bbox

    def copy(self) -> BoundingBox:
        """Create a copy of the bounding box."""
        bbox = BoundingBox()
        if self.min and self.max:
            bbox.min = self.min.copy()
            bbox.max = self.max.copy()
        return bbox

    def include_point(self, point: Vector2D) -> BoundingBox:
        """Increase the bounding box to include the given point.

        Args:
            point: Point to include in the bounding box.

        Returns:
            The bounding box after including the point.
        """
        if self.min is None:
            self.min = point.copy()
            self.max = point.copy()
        else:
            assert self.max is not None
            if self.min.x <= point.x:
                if self.max.x < point.x:
                    self.max.x = point.x
            else:
                self.min.x = point.x
            if self.min.y <= point.y:
                if self.max.y < point.y:
                    self.max.y = point.y
            else:
                self.min.y = point.y
        return self

    def include_bbox(self, bbox: BoundingBox) -> BoundingBox:
        """Increase the bounding box to include the given bounding box.

        Args:
            bbox: Bounding box to include in the bounding box.

        Returns:
            The bounding box after including the other bounding box.
        """
        if bbox.min is not None:
            assert bbox.max is not None
            self.include_point(bbox.min)
            self.include_point(bbox.max)
        return self

    def translate(self, vector: Vector2D = Vector2D.zero()) -> BoundingBox:
        """Move the bounding box.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated bounding box.
        """
        if self.min is not None:
            assert self.max is not None
            self.min += vector
            self.max += vector
        return self

    def inflate(self, amount: float) -> BoundingBox:
        """Expand the bounding box by the given amount in all directions.

        Args:
            amount: Amount by which to inflate the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.

        Returns:
            The bounding box after inflation.
        """
        if self.min is not None and self.max is not None:
            self.min.x -= amount
            self.min.y -= amount
            self.max.x += amount
            self.max.y += amount
            return self
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    def inflate_anisotropic(self, amount: Vector2D | float) -> BoundingBox:
        """Expand the bounding box by possibly diferent amounts in x- and y-direction.

        Args:
            amount: Amount by which to inflate the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.

        Returns:
            The bounding box after inflation.
        """
        if self.min is not None and self.max is not None:
            if isinstance(amount, float | int):
                self.min.x -= amount
                self.min.y -= amount
                self.max.x += amount
                self.max.y += amount
            else:
                self.min.x -= amount.x
                self.min.y -= amount.y
                self.max.x += amount.x
                self.max.y += amount.y

        else:
            raise RuntimeError("Cannot access empty bounding box.")
        return self

    def contains_point(self, point: Vector2D) -> bool:
        """Test if a point is inside the bounding box."""
        # A null bbox won't contain any point
        if self.min is None or self.max is None:
            return False
        return (
            self.min.x <= point.x <= self.max.x and self.min.y <= point.y <= self.max.y
        )

    def contains_bbox(self, bbox: BoundingBox) -> bool:
        """Test if another bounding box is completely inside this one."""
        if self.min is not None and self.max is not None:
            if bbox.min is not None and bbox.max is not None:
                return (
                    self.min.x <= bbox.min.x
                    and self.min.y <= bbox.min.y
                    and self.max.x >= bbox.max.x
                    and self.max.y >= bbox.max.y
                )
            else:
                return True
        else:
            return False

    def is_defined(self) -> bool:
        """Return `True` if the bounding box is defined."""
        if self.min is not None and self.max is not None:
            return True
        return False

    @property
    def top(self) -> float:
        """Return the left-most coordinate of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return self.min.y
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def bottom(self) -> float:
        """Return the bottom-most coordinate of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return self.max.y
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def left(self) -> float:
        """Return the left-most coordinate of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return self.min.x
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def right(self) -> float:
        """Return the right-most coordinate of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return self.max.x
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def top_left(self) -> Vector2D:
        """Return the top-left coordinate of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return self.min
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def top_right(self) -> Vector2D:
        """Return the top-right coordinate of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return Vector2D.from_floats(self.max.x, self.min.y)
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def bottom_right(self) -> Vector2D:
        """Return the bottom-right coordinate of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return self.max
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def bottom_left(self) -> Vector2D:
        """Return the bottom-left coordinate of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return Vector2D.from_floats(self.min.x, self.max.y)
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def right_midpoint(self) -> Vector2D:
        """Return the right mid-point of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return Vector2D.from_floats(self.right, self.center.y)
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def left_midpoint(self) -> Vector2D:
        """Return the left mid-point of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return Vector2D.from_floats(self.left, self.center.y)
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def top_midpoint(self) -> Vector2D:
        """Return the top mid-point of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return Vector2D.from_floats(self.center.x, self.top)
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def bottom_midpoint(self) -> Vector2D:
        """Return the bottom mid-point of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return Vector2D.from_floats(self.center.x, self.bottom)
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def size(self) -> Vector2D:
        """Return the size of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return self.max - self.min
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    @property
    def center(self) -> Vector2D:
        """Return the center point of the bounding box.

        Raises:
            RuntimeError: If the bounding box is not initialized.
        """
        if self.min is not None and self.max is not None:
            return (self.min + self.max) / 2
        else:
            raise RuntimeError("Cannot access empty bounding box.")

    def __repr__(self) -> str:
        """Return the string representation of the arc."""
        return f"BoundingBox(min={self.min}, max={self.max})"
