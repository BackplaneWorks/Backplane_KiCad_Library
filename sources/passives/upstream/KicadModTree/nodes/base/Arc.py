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

"""Class definition for an arc."""

from __future__ import annotations

from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.line_style import LineStyle
from kilibs.geom import GeomArc, Vec2DCompatible


class Arc(Shape, GeomArc):
    """An arc."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        shape: Arc | GeomArc | None = None,
        center: Vec2DCompatible | None = None,
        start: Vec2DCompatible | None = None,
        mid: Vec2DCompatible | None = None,
        end: Vec2DCompatible | None = None,
        angle: float | None = None,
        long_way: bool = False,
    ) -> None:
        """Create an arc.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: Unused parameter - needed to provide a homogeneous initializer
                interface.
            shape: Arc from which to derive the parameters.
            center: Coordinates (in mm) of the center of the arc.
            start: Coordinates (in mm) of the start point of the arc.
            mid: Coordinates (in mm) of the mid point of the arc.
            end: Coordinates (in mm) of the end point of the arc.
            angle: Angle of the arc in degrees.
            long_way: Used when constructing the arc with the center, start and end
                point to specify if the longer of the 2 possible resulting arcs or the
                shorter one shall be constructed.
        """
        Shape.__init__(self, layer=layer, width=width, style=style, fill=fill)
        GeomArc.__init__(
            self,
            shape=shape,
            center=center,
            start=start,
            mid=mid,
            end=end,
            angle=angle,
            long_way=long_way,
        )

    def as_geom_shape(self) -> GeomArc:
        """Convert this shape node into its base geometric shape (GeomArc)."""
        return GeomArc(shape=self)
