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

"""Class definition for the shape node."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Self

from KicadModTree.nodes.Node import Node
from KicadModTree.util import LineStyle
from kilibs.geom import (
    BoundingBox,
    GeomShape,
    GeomShapes,
    Vector2D,
)


class Shape(Node, GeomShape):
    """A node class for shapes."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        shape: Self | GeomShape | None = None,
    ) -> None:
        """Create a `Shape`.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the rectangle is filled, `False` if only the outline is
                visible. `False` for open shapes.
            shape: Optional shape to copy for the creation of this shape node.
        """

        # Instance attributes:
        self.layer: str
        """The layer on which the node is drawn."""
        self.width: float | None
        """The width of the outline of the shape."""
        self.style: LineStyle
        """The line style used to draw the outline of the shape."""
        self.fill: bool
        """Whether the shape is filled, `False` for open shapes."""

        Node.__init__(self)
        self.layer = layer
        self.width = width
        self.style = style
        self.fill = fill

    def copy(self) -> Self:
        """Creates a copy of itself."""
        return self.__class__(
            shape=self,
            layer=self.layer,
            width=self.width,
            style=self.style,
            fill=self.fill,
        )

    def copy_with(
        self,
        shape: Self | None = None,
        layer: str | None = None,
        width: float | None = None,
        style: LineStyle | None = None,
        fill: bool | None = None,
        offset: float | None = None,
    ) -> Self:
        """Creates a copy of itself using the given parameters instead of the original ones.

        Args:
            shape: Use the shape given as parameter instead of the original one.
            layer: Use the layer given as parameter instead of the original one.
            width: Use the width given as parameter instead of the original one.
            style: Use the style given as parameter instead of the original one.
            fill: Use the fill type given as parameter instead of the original one.
            ofsset: inflate/deflate the shape by this amount.
        """
        params: dict[str, Any] = {}
        shape = shape if shape else self
        layer = layer if layer else self.layer
        width = width if width else self.width
        style = style if style else self.style
        fill = fill if fill else self.fill
        if offset:
            params.update({"offset": offset})
        return self.__class__(
            shape=shape, layer=layer, width=width, style=style, fill=fill, **params
        )

    @abstractmethod
    def as_geom_shape(self) -> GeomShape:
        """Convert this shape node into its base geometric shape (GeomShape)."""
        pass

    def translate(self, vector: Vector2D) -> Self:
        """Move the node.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated node.
        """
        return super(Node, self).translate(vector=vector)

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Self:
        """Rotate the node around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated node.
        """
        return super(Node, self).rotate(angle=angle, origin=origin)

    def bbox(self) -> BoundingBox:
        """Get the bounding box of the node."""
        return super(Node, self).bbox()

    def __repr__(self) -> str:
        """The string representation of the Shape."""
        class_name = self.__class__.__name__
        # Start looking for a __repr__ method in the classes that appear after
        # Node in the MRO of the current instance (this will be the class that
        # inherits from GeomShape, e.g. GeomArc, GeomLine, ...):
        node_class = super(Node, self)
        shape = f"shape={node_class.__repr__()}, "
        layer = f"layer={self.layer}, " if hasattr(self, "layer") else ""
        width = f"width={self.width}, " if hasattr(self, "width") else ""
        style = f"style={self.style}, " if hasattr(self, "style") else ""
        fill = f"fill={self.fill}, " if hasattr(self, "fill") else ""
        repr = f"{class_name}({shape}{layer}{width}{style}{fill}".removesuffix(", ")
        repr += ")"
        return repr

    def __str__(self) -> str:
        """The string representation of the Shape."""
        return self.__repr__()
