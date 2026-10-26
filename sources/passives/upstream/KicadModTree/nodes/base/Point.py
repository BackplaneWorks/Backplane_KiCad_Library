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

"""Class definition for a point."""

from KicadModTree.nodes.Node import Node

from kilibs.geom import Vec2DCompatible, Vector2D


class Point(Node):
    """A PCB point."""

    def __init__(
        self,
        at: Vec2DCompatible,
        size: float,
        layer: str,
    ) -> None:
        """Create a point.

        Args:
            at: Coordinates of the point.
            size: Size of the point.
            layer: Layer on which the point is located.
        """

        super().__init__()

        self.at: Vector2D = Vector2D(at)
        """Coordinates of the point."""
        self.size: float = size
        """Size of the point."""
        self.layer: str = layer
        """Layer on which the point is located."""
