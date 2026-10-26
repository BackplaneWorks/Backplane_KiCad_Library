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

"""Class definition for a circle."""

from __future__ import annotations

from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import GeomArc, GeomCircle, Vec2DCompatible


class Circle(Shape, GeomCircle):
    """A circle."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0.0,
        shape: Circle | GeomCircle | Arc | GeomArc | None = None,
        center: Vec2DCompatible | None = None,
        radius: float | None = None,
    ) -> None:
        """Create a circle.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the circle is filled, `False` if only the outline is
                visible.
            offset: Amount by which the circle is inflated or deflated (if offset is
                negative).
            shape: Shape from which to derive the parameters.
            center: Coordinates (in mm) of the center of the circle.
            radius: Radius of the circle in mm.
        """
        Shape.__init__(self, layer=layer, width=width, style=style, fill=fill)
        GeomCircle.__init__(self, shape=shape, center=center, radius=radius)
        if offset:
            self.inflate(amount=offset)

    def as_geom_shape(self) -> GeomCircle:
        """Convert this shape node into its base geometric shape (GeomCircle)."""
        return GeomCircle(shape=self)
