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

"""Class definition for a polygon."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.line_style import LineStyle
from KicadModTree.util.shape_to_node import shape_to_node
from kilibs.geom import BoundingBox, GeomPolygon, GeomRectangle, Vec2DCompatible

if TYPE_CHECKING:
    from KicadModTree.nodes.base.Line import Line


class Polygon(Shape, GeomPolygon):
    """A polygon."""

    def __init__(
        self,
        shape: (
            Polygon
            | GeomPolygon
            | Iterable[Vec2DCompatible]
            | GeomRectangle
            | BoundingBox
        ),
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0.0,
        x_mirror: float | None = None,
        y_mirror: float | None = None,
        close: bool = True,
    ) -> None:
        """Create a polygon.

        Args:
            shape: Polygon, rectangle, bounding box or list of points from which to
                derive the polygon.
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the polygon is filled, `False` if only the outline is
                visible.
            offset: Amount by which the polygon is inflated or deflated (if offset is
                negative).
            x_mirror: Mirror x direction around offset axis.
            y_mirror: Mirror y direction around offset axis.
            close: If `True` the polygon will form a closed shape. If `False` there
                won't be any connecting line between the last and the first point.
        """
        Shape.__init__(self, layer=layer, width=width, style=style, fill=fill)
        GeomPolygon.__init__(
            self, shape=shape, x_mirror=x_mirror, y_mirror=y_mirror, close=close
        )
        if offset:
            self.inflate(amount=offset)

    def flatten(self) -> list[Polygon | Line]:
        """Return the leaf nodes to serialize."""
        if self.close:
            return [self]
        else:
            nodes: list[Polygon | Line] = []
            for shape in self.get_atomic_shapes():
                node = shape_to_node(
                    shape=shape,
                    layer=self.layer,
                    width=self.width,
                    style=self.style,
                    fill=self.fill,
                )
                nodes.append(node)
            return nodes

    def as_geom_shape(self) -> GeomPolygon:
        """Convert this shape node into its base geometric shape (GeomPolygon)."""
        return GeomPolygon(shape=self)
