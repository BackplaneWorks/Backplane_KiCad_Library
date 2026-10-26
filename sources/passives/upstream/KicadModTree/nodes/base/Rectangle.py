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

"""Class definition for a rectangle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import BoundingBox, GeomRectangle, Vec2DCompatible

if TYPE_CHECKING:
    from .Polygon import Polygon


class Rectangle(Shape, GeomRectangle):
    """A rectangle."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0.0,
        shape: Rectangle | GeomRectangle | BoundingBox | None = None,
        start: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        size: Vec2DCompatible | None = None,
        angle: float = 0.0,
    ) -> None:
        """Create a rectangle.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the rectangle is filled, `False` if only the outline is
                visible.
            offset: Amount by which the rectangle is inflated or deflated (if offset is
                negative).
            shape: Shape from which to derive the parameters of the rectangle.
            center: Coordinates (in mm) of the center point of the rectangle.
            size: Size in mm of the rectangle.
            start: Coordinates (in mm) of the top left corner of the rectangle.
            stop: Coordinates (in mm) of the bottom right corner of the rectangle.
            angle: Rotation angle of the rectangle in degrees.
        """
        Shape.__init__(self, layer=layer, width=width, style=style, fill=fill)
        GeomRectangle.__init__(
            self,
            shape=shape,
            start=start,
            end=end,
            center=center,
            size=size,
            angle=angle,
        )
        if offset:
            self.inflate(amount=offset)

    def flatten(self) -> list[Rectangle | Polygon]:
        """Return the leaf nodes to serialize."""
        if self.angle:
            from .Polygon import Polygon

            return [
                Polygon(
                    shape=self,
                    layer=self.layer,
                    width=self.width,
                    style=self.style,
                    fill=self.fill,
                )
            ]
        else:
            return [self]

    def as_geom_shape(self) -> GeomRectangle:
        """Convert this shape node into its base geometric shape (GeomRectangle)."""
        return GeomRectangle(shape=self)
