# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

from dataclasses import dataclass
from typing import Callable

from KicadModTree import Circle, Node, LineStyle, Rectangle, PolygonLine, Cross
from kilibs.geom import Vector2D
from kilibs.declarative_defs import additional_drawings as ADs
from kilibs.declarative_defs import repeat_defs, evaluable_defs as EDs

from . import shape_properties as SP
from kilibs.config.global_config import GlobalConfig


class FPDrawingProvider(ADs.DrawingProvider):
    """
    A footprint drawing provider knows how to map from a shapes properties object to
    a Node in the context of a footprint (as opposed to, say, a symbol or 3D model).

    You can make your own implementations of this class to handle different
    types of shapes, or you can use the provided implementations for simple
    shapes like rectangles, circles, and polygons.

    This allows you to hook a generator into the system and give access
    to the drawing framework (e.g. for repeats and layer/width defaults)
    even for generator-specific shapes.
    """

    layer: str
    width: float | None
    """Line width of the drawing. If None, the default width for the layer is used."""
    fill: bool
    """Whether the drawing should be filled or not. Default is False"""
    line_style: LineStyle

    @dataclass
    class Context:
        """
        When it's time to actually make the nodes, the caller needs to provide
        the evaluation context for the expressions in the shape properties.
        This includes things based on the global configuration, as well as the
        AST evaluator, and so on.
        """

        layer: str
        """The resolved board layer"""
        width: float
        """The resolved line width"""
        evaluator: Callable
        transforms: list[repeat_defs.Transformation]

    def __init__(self, spec: dict):
        # Common drawing properties
        self.layer = spec["layer"]
        self.width = spec.get("width", None)
        self.fill = spec.get("fill", False)

        self.line_style = spec.get("style", None)

        if self.line_style is None:
            self.line_style = LineStyle.SOLID
        else:
            self.line_style = LineStyle(self.line_style)

    def make_nodes(self, context: Context) -> list[Node]:
        """
        Create the drawing nodes from the shape properties.
        """
        raise NotImplementedError("DrawingProvider.make_nodes() must be implemented")


class RectDrawingProvider(FPDrawingProvider):

    rect_def: SP.RectProperties

    def __init__(self, spec: dict):
        super().__init__(spec)
        self.rect_def = SP.RectProperties(spec)

    def make_nodes(self, context: FPDrawingProvider.Context) -> list[Node]:
        rect = self.rect_def.evaluate(context.evaluator)
        return [
            Rectangle(
                # For now, this will handle 90 degree rotations, but not others
                start=self._modify_point(rect.top_left, context.transforms),
                end=self._modify_point(rect.bottom_right, context.transforms),
                layer=context.layer,
                width=context.width,
                fill=self.fill,
                style=self.line_style,
            )
        ]


class CircleDrawingProvider(FPDrawingProvider):

    circle_def: SP.CircleProperties

    def __init__(self, spec: dict):
        super().__init__(spec)
        self.circle_def = SP.CircleProperties(spec)

    def make_nodes(self, context: FPDrawingProvider.Context) -> list[Node]:
        circ = self.circle_def.evaluate(context.evaluator)
        return [
            Circle(
                center=self._modify_point(circ.center, context.transforms),
                radius=circ.radius,
                layer=context.layer,
                width=context.width,
                fill=self.fill,
                style=self.line_style,
            )
        ]


class PolyDrawingProvider(FPDrawingProvider):

    poly_def: SP.PolyProperties

    def __init__(self, spec: dict):
        super().__init__(spec)
        self.poly_def = SP.PolyProperties(spec)

    def make_nodes(self, context: FPDrawingProvider.Context) -> list[Node]:
        poly = self.poly_def.evaluate(context.evaluator)

        def _point_modifier(pt: Vector2D) -> Vector2D:
            return self._modify_point(pt, context.transforms)

        poly.transform_points(_point_modifier)

        return [
            PolygonLine(
                shape=poly,
                layer=context.layer,
                width=context.width,
                fill=self.fill,
                style=self.line_style,
            )
        ]


class CrossDrawingProvider(FPDrawingProvider):
    """
    Draws a cross: "+"
    """

    center: EDs.EvaluableVector2D
    size: EDs.EvaluableVector2D
    angle: float

    def __init__(self, spec: dict):
        super().__init__(spec)

        size_spec = spec["size"]
        if not isinstance(size_spec, list):
            size_spec = [size_spec, size_spec]

        self.center = EDs.EvaluableVector2D(spec["center"])
        self.size = EDs.EvaluableVector2D(size_spec)
        # Handle the negative PCB y-axis (match pad rotation direction)
        self.angle = -spec.get("angle", 0)

    def make_nodes(self, context: FPDrawingProvider.Context) -> list[Node]:
        center = self.center.evaluate(context.evaluator)
        size = self.size.evaluate(context.evaluator)

        return [
            Cross(
                center=center,
                size=size,
                angle=self.angle,
                layer=context.layer,
                width=context.width,
            )
        ]


class FPAdditionalDrawing(ADs.AdditionalDrawing):
    """
    A specific additional drawing object for footprints, which knows how to
    create the appropriate drawing nodes from the shape properties.
    """

    def __init__(self, spec_dict: dict, key_name: str, additional_providers={}):
        """
        Initialize the additional drawing object from a single specification.
        """

        self._default_fp_providers = {
            "rect": RectDrawingProvider,
            "circle": CircleDrawingProvider,
            "poly": PolyDrawingProvider,
            "cross": CrossDrawingProvider,
        }

        self._default_fp_providers.update(additional_providers)

        super().__init__(spec_dict, key_name)

    def _get_default_providers(self) -> dict[str, FPDrawingProvider]:
        """
        Return the default drawing providers for footprint drawings.
        """
        return self._default_fp_providers

    def make_nodes(self, context: FPDrawingProvider.Context) -> list[Node]:
        """
        Create the drawing nodes from the shape properties.
        """
        assert isinstance(self.shape_provider, FPDrawingProvider)
        return self.shape_provider.make_nodes(context)


def create_additional_drawings(
    additional_drawings: list[FPAdditionalDrawing],
    global_config: GlobalConfig,
    expr_evaluator: Callable,
) -> list[Node]:
    """
    Create the drawing objects from the given additional drawing properties,
    after evaluating any expressions in the drawing shapes.

    Relevant defaults are also be applied from the global configuration at this
    time.

    This is the "glue" that converts "generic" addtional drawing properties
    into footprint-specific drawing objects. In theory, a similar function
    could be used to create suitable objects for adding to symbols.
    """
    dwg_nodes = []

    for add_dwg in additional_drawings:

        # Map from things like 'mechanical' to 'Cmts.User'
        layer = global_config.get_layer_for_function(add_dwg.shape_provider.layer)

        # Apply global config defaults
        if add_dwg.shape_provider.width is not None:
            width = add_dwg.shape_provider.width
        else:
            width = global_config.get_default_width_for_layer(layer)

        for transforms in add_dwg.get_transforms(expr_evaluator):

            context = FPDrawingProvider.Context(
                layer=layer,
                width=width,
                evaluator=expr_evaluator,
                transforms=transforms,
            )

            dwg_nodes += add_dwg.make_nodes(context)

    return dwg_nodes
