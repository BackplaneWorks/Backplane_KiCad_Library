# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

from collections.abc import Iterable
from typing import Self

from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.Container import Container
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import BoundingBox, GeomPolygon, GeomRectangle, Vec2DCompatible


class PolygonLine(Shape, Container[Line], GeomPolygon):
    """Add a Polygon Line to the render tree.

    A "polygon line" is a "polyline" - a chain of line segments.

    As of v9, KiCad doesn't support a specific node type like this, but rather we
    will represent it as a chain of (n_pts - 1) line segments.

    :Example:

    >>> from KicadModTree import *
    >>> PolygonLine(shape=[[0, 0], [0, 1], [1, 1], [0, 0]], layer='F.SilkS')
    """

    layer: str
    width: float | None
    style: LineStyle

    def __init__(
        self,
        shape: (
            Self | GeomPolygon | GeomRectangle | BoundingBox | Iterable[Vec2DCompatible]
        ),
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0,
        x_mirror: float | None = None,
        y_mirror: float | None = None,
    ):
        """Create a polygon.

        Args:
            shape: Polygon, rectangle, bounding box or list of points from which to derive the polygon.
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: If the shape is filled or only the outline is visible.
            offset: amount by which the shape is inflated or deflated (if offset negative).
            x_mirror: Mirror x direction around offset axis.
            y_mirror: Mirror y direction around offset axis.
        """
        Shape.__init__(self)
        Container.__init__(self)  # pyright: ignore
        close = True
        if isinstance(shape, list | tuple):
            if shape[-1] != shape[0]:
                close = False
        GeomPolygon.__init__(
            self, shape=shape, x_mirror=x_mirror, y_mirror=y_mirror, close=close
        )
        self.layer = layer
        self.width = width
        self.fill = fill
        if self.width is not None:
            self.width = float(self.width)
        self.style = style
        if offset:
            self.inflate(amount=offset)
        self._update_children()

    def flatten(self) -> list[Line]:
        """Return the nodes to serialize."""
        return self._children

    def lineItems(self):
        if not self._children:
            self._update_children()
        return iter(self._children)

    def pointItems(self):
        return iter(self.points)

    def isPointOnSelf(self, point: Vec2DCompatible) -> bool:
        return self.is_point_on_self(point)

    def isPointInsideSelf(self, point: Vec2DCompatible, include_corners=True) -> bool:
        return self.is_point_inside_self(point, include_corners=include_corners)

    def rotate(self, *args, **kwargs):
        super().rotate(*args, **kwargs)
        self._update_children()
        return self

    def translate(self, *args, **kwargs):
        super().translate(*args, **kwargs)
        self._update_children()
        return self

    def inflate(self, *args, **kwargs):
        super().inflate(*args, **kwargs)
        self._update_children()
        return self

    def simplify(self, *args, **kwargs):
        super().simplify(*args, **kwargs)
        self._update_children()
        return self

    def as_geom_shape(self) -> GeomPolygon:
        """Convert this shape node into its base geometric shape (GeomStadium)."""
        return GeomPolygon(shape=self)

    def _update_children(self):
        nodes: list[Line] = []
        for line_start, line_end in zip(self.points, self.points[1:]):
            new_node = Line(
                start=line_start,
                end=line_end,
                layer=self.layer,
                width=self.width,
                style=self.style,
            )
            nodes.append(new_node)
        if self.close:
            new_node = Line(
                start=self.points[-1],
                end=self.points[0],
                layer=self.layer,
                width=self.width,
                style=self.style,
            )
            nodes.append(new_node)
        self._children = nodes

    def _getRenderTreeText(self):
        render_text = Node._getRenderTreeText(self)
        render_text += " ["
        node_strings = []
        for point in self.points:
            node_strings.append(f"[x: {point.x}, y: {point.y}]")
        if len(node_strings) <= 6:
            render_text += " ,".join(node_strings)
        else:
            # display only a few nodes of the beginning and the end of the polygon line
            render_text += " ,".join(node_strings[:3])
            render_text += " ,... ,"
            render_text += " ,".join(node_strings[-3:])
        render_text += "]"
        return render_text
