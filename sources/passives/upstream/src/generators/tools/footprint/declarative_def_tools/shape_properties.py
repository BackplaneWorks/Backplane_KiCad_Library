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

from kilibs.geom import GeomCircle, GeomRectangle, Vector2D, GeomPolygon
from kilibs.declarative_defs import evaluable_defs as EDs


class ShapeProperties(EDs.Evaluable):

    offset: EDs.EvaluableVector2D | None
    """An offset applied to all evaluated points of the shape.

    This can be used if all the points are relative to some other point
    rather than having to copy the same offset into each point's definition.
    """

    def __init__(self, shape_def: dict):

        self.offset = None
        if 'offset' in shape_def:
            self.offset = EDs.EvaluableVector2D(shape_def['offset'])

    def _evaluate_offset(self, expr_evaluator: Callable) -> Vector2D:
        if self.offset is None:
            return Vector2D(0, 0)

        return self.offset.evaluate(expr_evaluator)

class RectProperties(ShapeProperties):

    # Expressions that define the coordinates of the rectangle
    # (these will be evaluated in the context of each footprint)
    # which can only happen much later when the variables are known
    @dataclass
    class CornerExprs:
        corner1: EDs.EvaluableVector2D
        corner2: EDs.EvaluableVector2D

    @dataclass
    class CenterSizeExprs:
        center: EDs.EvaluableVector2D
        size: EDs.EvaluableVector2D

    exprs: CornerExprs | CenterSizeExprs

    def __init__(self, rect: dict):
        super().__init__(rect)

        if 'center' in rect:
            if not 'size' in rect:
                raise ValueError('Rectangular shape with "center" also needs "size" key')

            if len(rect['center']) != 2 or len(rect['size']) != 2:
                raise ValueError('Both "center" and "size" must have exactly two coordinates')

            self.exprs = self.CenterSizeExprs(
                center=EDs.EvaluableVector2D(rect['center']),
                size=EDs.EvaluableVector2D(rect['size'])
            )
        elif 'corners' in rect:
            corners = rect['corners']

            if len(corners) != 2 or len(corners[0]) != 2 or len(corners[1]) != 2:
                raise ValueError('Each point of the rectangular shape must have exactly two coordinates')

            self.exprs = self.CornerExprs(
                corner1=EDs.EvaluableVector2D(corners[0]),
                corner2=EDs.EvaluableVector2D(corners[1])
            )
        else:
            raise ValueError('Rectangular shape must have either "center/size" or "corners" definition')

    def evaluate(self, expr_evaluator: Callable) -> GeomRectangle:

        offset = self._evaluate_offset(expr_evaluator)

        if isinstance(self.exprs, RectProperties.CornerExprs):
            corner1 = self.exprs.corner1.evaluate(expr_evaluator)
            corner2 = self.exprs.corner2.evaluate(expr_evaluator)
            return GeomRectangle(start=corner1 + offset, end=corner2 + offset)

        elif isinstance(self.exprs, RectProperties.CenterSizeExprs):
            center = self.exprs.center.evaluate(expr_evaluator)
            size = self.exprs.size.evaluate(expr_evaluator)
            return GeomRectangle(center=center + offset, size=size)

        raise RuntimeError(f"Invalid rectangle expression type: {self.exprs}")


class CircleProperties(ShapeProperties):

    # Expressions that define the coordinates of the rectangle
    # (these will be evaluated in the context of each footprint)
    # which can only happen much later when the variables are known
    @dataclass
    class CenterSizeExprs:
        center: EDs.EvaluableVector2D
        rad_diam: EDs.EvaluableScalar
        is_diam: bool

    exprs: CenterSizeExprs

    def __init__(self, circle: dict):
        """
        Initialise a circle properties from the given dictionary.

        Normally, this looks something like this:

        SOME_KEY:
            type: circle
            center: [x, y]
            diameter: d / radius: r

        where x, y, and d/r are expressions that will be evaluated in the context of each footprint.
        """

        super().__init__(circle)

        if not 'center' in circle:
            raise ValueError('Circle shape must have a "center" key')

        if 'diameter' in circle and 'radius' in circle:
            raise ValueError('Circle shape must have either "diameter" or "radius" key, not both')

        rad_diam_expr = circle.get('diameter', circle.get('radius'))
        is_diam = 'diameter' in circle

        self.exprs = self.CenterSizeExprs(
            center=EDs.EvaluableVector2D(circle['center']),
            rad_diam=EDs.EvaluableScalar(rad_diam_expr),
            is_diam=is_diam
        )

    def evaluate(self, expr_evaluator: Callable) -> GeomCircle:
        offset = self._evaluate_offset(expr_evaluator)
        center = self.exprs.center.evaluate(expr_evaluator)
        radius = self.exprs.rad_diam.evaluate(expr_evaluator)

        if self.exprs.is_diam:
            radius /= 2.0

        return GeomCircle(center=center + offset, radius=radius)


class PolyProperties(ShapeProperties):

    pts: list[EDs.EvaluableVector2D]
    close: bool

    def __init__(self, poly: dict):
        """
        Initialise a polygon/polyline properties from the given dictionary.

        Polygon or polyline shapes are defined by a list of points, each of which
        can be an expression that will be evaluated in the context of each footprint.

        The 'close' key can be used to indicate whether the polygon should be closed
        (the first and last points are connected). If not specified, it defaults to False
        (the polygon is a polyline).

        Looks something like this:

            type: poly
            layer: 'F.Fab'
            points:
                - [0,    1]
                - [-1.5, 1]
            offset: [$(body_left_x), $(body_top_y)]
        """

        super().__init__(poly)
        self.pts = []

        if not 'points' in poly or not isinstance(poly['points'], list):
            raise ValueError('Polygon/polyline shape must have a "points" key that is a list')

        for pt in poly['points']:
            self.pts.append(EDs.EvaluableVector2D(pt))

        if len(self.pts) < 2:
            raise ValueError('Polygon/polyline shape must have at least two points')

        self.close = bool(poly.get('close', False))

    def evaluate(self, expr_evaluator: Callable) -> GeomPolygon:
        offset = self._evaluate_offset(expr_evaluator)
        nodes: list[Vector2D] = []

        for pt in self.pts:
            evaled_pt = pt.evaluate(expr_evaluator)
            nodes.append(evaled_pt + offset)

        return GeomPolygon(shape=nodes, close=self.close)


def construct_shape(shape_spec: dict) -> ShapeProperties | None:

    if not 'type' in shape_spec:
        raise ValueError('Shape must have a "type" key')

    type = shape_spec['type']

    if type == "rect":
        return RectProperties(shape_spec)
    elif type == "circle":
        return CircleProperties(shape_spec)
    elif type == "poly":
        return PolyProperties(shape_spec)

    return None
