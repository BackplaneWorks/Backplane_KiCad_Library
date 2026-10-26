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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

"""Class definition for the translation node."""

from collections.abc import Sequence

from KicadModTree.nodes.Container import Container
from KicadModTree.nodes.Node import Node
from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.vector import Vector2D


class Translation(Container[Node]):
    """A translation that is applied to every child node."""

    def __init__(self, x: float | Vector2D = 0.0, y: float = 0.0) -> None:
        """Create a translation node.

        Args:
            x: The distance in mm in the x-direction.
            y: The distance in mm in the y-direction.
        """

        # Instance attributes:
        self.offset: Vector2D
        """The direction and distance in mm of the translation."""

        super().__init__()
        if isinstance(x, Vector2D):
            self.offset = x
        else:
            self.offset = Vector2D.from_floats(x, y)

    def transformed_children(self) -> Sequence[Node]:
        """Return the immediate children with this node's translation applied.

        Returns:
            The list of all child nodes if the translation offset is zero, otherwise
            a translated copy of all child nodes.
        """
        if self.offset.is_nullvec():
            return self._children
        else:
            nodes: list[Node] = []
            for child in self._children:
                nodes.append(child.translated(vector=self.offset))
            return nodes

    def flatten(self) -> Sequence[Node]:
        """Recursively retrieve primitives and apply their transformations to them.

        Returns:
            The list of all child nodes if the translation offset is zero, otherwise
            a translated copy of all flattened child nodes.
        """
        nodes: list[Node] = []
        if self.offset.is_nullvec():
            for child in self._children:
                nodes += child.flatten()
        else:
            for child in self._children:
                for flat_child in child.flatten():
                    nodes.append(flat_child.translated(vector=self.offset))
        return nodes

    def bbox(self) -> BoundingBox:
        """Return the bounding box of all the child nodes translated by 'offset'.
        This is in its own context, so it is independent of the parent nodes'
        transformations, but does incldue any transformation it applies itself.

        Example:
            >>> translation = Translation(-10, 0)
            >>> line = Line(start=(0, 0), end=(1, 1))
            >>> translation.append(line)
            >>> print(line.bbox())
                Vector2D(0, 0), Vector2D(1, 1)
            >>> print(translation.bbox())
                Vector2D(-10, 0), Vector2D(-9, 1)
        """
        bbox = BoundingBox()
        for child in self._children:
            child_bbox = child.bbox()
            bbox.include_bbox(child_bbox)
        if bbox.min is not None and bbox.max is not None:
            # translate the bounding box
            bbox.min += self.offset
            bbox.max += self.offset
            return bbox
        else:
            return bbox

    def __repr__(self) -> str:
        """The string representation of the translation."""
        return f"Translation(offset={self.offset})"
