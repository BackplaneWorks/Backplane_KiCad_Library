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

"""Class definition for the rotation node."""

from collections.abc import Sequence

from KicadModTree.nodes.Container import Container
from KicadModTree.nodes.Node import Node
from kilibs.geom import BoundingBox, Vector2D


class Rotation(Container[Node]):
    """A rotation that is applied to every child node."""

    def __init__(self, angle: float = 0.0, origin: Vector2D = Vector2D.zero()) -> None:
        """Create a rotation node.

        Args:
            angle: The angle in degrees.
            origin: The coordinates of the point (in mm) around which the child nodes
                are rotated.
        """

        # Instance attributes:
        self.angle: float
        """The rotation angle in degrees."""
        self.origin: Vector2D
        """The coordinates of the point (in mm) around which the child nodes are rotated."""

        super().__init__()
        self.angle = angle
        self.origin = origin

    @property
    def children(self) -> Sequence[Node]:
        """Return a list of the rotated copies of all child nodes from the node tree.

        Returns:
            The list of all child nodes if the rotation angle is zero, otherwise a
            rotated copy of all child nodes.
        """
        if abs(self.angle % 360) <= 1e-10:
            return self._children
        else:
            transformed_nodes: list[Node] = []
            for child in self._children:
                transformed_nodes.append(child.rotated(self.angle, self.origin))
        return transformed_nodes

    def transformed_children(self) -> Sequence[Node]:
        """Return the immediate children with this node's rotation applied.

        Returns:
            The list of all child nodes if the rotation is zero, otherwise a rotated
            copy of all child nodes.
        """
        if abs(self.angle % 360) <= 1e-10:
            return self._children
        else:
            nodes: list[Node] = []
            for child in self._children:
                nodes.append(child.rotated(self.angle, self.origin))
            return nodes

    def flatten(self) -> Sequence[Node]:
        """Recursively retrieve primitives and apply their transformations to them.

        Returns:
            The list of all child nodes if the rotation is zero, otherwise a rotated
            copy of all flattened child nodes.
        """
        nodes: list[Node] = []
        if self.angle == 0.0:
            for child in self._children:
                nodes += child.flatten()
        else:
            for child in self._children:
                for flat_child in child.flatten():
                    nodes.append(flat_child.rotated(self.angle, self.origin))
        return nodes

    def bbox(self) -> BoundingBox:
        """Return the rotated bounding box of every child node."""
        bbox = BoundingBox()
        for child in self._children:
            child_bbox = child.rotated(angle=self.angle, origin=self.origin).bbox()
            bbox.include_bbox(child_bbox)
        return bbox

    def __repr__(self) -> str:
        """The string representation of the rotation."""
        return f"Rotation(angle={self.angle}, origin={self.origin})"
