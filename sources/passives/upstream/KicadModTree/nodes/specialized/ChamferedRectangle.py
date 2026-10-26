from __future__ import annotations

from KicadModTree.nodes.base.Polygon import Polygon
from KicadModTree.nodes.base.Rectangle import Rectangle
from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.corner_handling import ChamferSizeHandler
from KicadModTree.util.line_style import LineStyle
from KicadModTree.util.shape_to_node import shape_to_node
from kilibs.geom import (
    CornerSelection,
    GeomChamferedRectangle,
    Vec2DCompatible,
    Vector2D,
)


class ChamferedRectangle(Shape, GeomChamferedRectangle):
    """A rectangle with some chamfered corners."""

    def __init__(
        self,
        layer: str = "F.SilkS",
        width: float | None = None,
        style: LineStyle = LineStyle.SOLID,
        fill: bool = False,
        offset: float = 0,
        shape: ChamferedRectangle | GeomChamferedRectangle | None = None,
        size: Vec2DCompatible | None = None,
        center: Vec2DCompatible | None = None,
        angle: float = 0.0,
        chamfer: ChamferSizeHandler | None = None,
        corners: CornerSelection | None = None,
    ) -> None:
        """Create a chamfered rectangle.

        Args:
            layer: Layer.
            width: Line width in mm. If `None`, then the standard width for the given
                layer will be used when the serializing the node.
            style: Line style.
            fill: `True` if the chamfered rectangle is filled, `False` if only the
                outline is visible.
            offset: Amount by which the chamfered rectangle is inflated or deflated (if
                offset is negative).
            shape: Shape from which to derive the parameters of the chamfered rectangle.
            size: Width and height of the chamfered rectangle in mm.
            center: Coordinates of the center point of the chamfered rectangle in mm.
            angle: Rotation angle of the chamfered rectangle in degrees.
            chamfer: The chamfer size handler.
            corners: The corners to chamfer.
        """
        Shape.__init__(self, layer=layer, width=width, style=style, fill=fill)
        if size is not None and chamfer is not None:
            size = Vector2D(size)
            chamfer_size = chamfer.get_chamfer_size(min(size.x, size.y))
        else:
            chamfer_size = 0.0
        GeomChamferedRectangle.__init__(
            self,
            shape=shape,
            size=size,
            center=center,
            angle=angle,
            chamfer_size=chamfer_size,
            corners=corners,
        )
        if offset:
            self.inflate(amount=offset)

    def flatten(self) -> list[Rectangle | Polygon]:
        """Return the leaf nodes to serialize."""
        shape = self.get_shapes()[0]
        node = shape_to_node(
            shape=shape,
            layer=self.layer,
            width=self.width,
            style=self.style,
            fill=self.fill,
        )
        return [node]

    def as_geom_shape(self) -> GeomChamferedRectangle:
        """Convert this shape node into its base geometric shape
        (GeomChamferedRectangle).
        """
        return GeomChamferedRectangle(shape=self)
