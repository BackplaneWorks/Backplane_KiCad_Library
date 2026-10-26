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

"""Functions for converting `GeomShape` instances to `Shape` instances."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from KicadModTree import (
        Line,
        Arc,
        Circle,
        Rectangle,
        Polygon,
        CompoundPolygon,
        Cross,
        Cruciform,
        RoundRectangle,
        Stadium,
        Trapezoid,
        ChamferedRectangle,
        Shape,
    )

from KicadModTree.util import LineStyle
from kilibs.geom import (
    GeomArc,
    GeomChamferedRectangle,
    GeomCircle,
    GeomCompoundPolygon,
    GeomCross,
    GeomCruciform,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomRoundRectangle,
    GeomShapes,
    GeomStadium,
    GeomTrapezoid,
)

map_geomshape_node: dict[type, type] = {}
"""Mapping between all the GeomShape types and their corresponding Shape types."""


def _init_map_geomshape_node() -> None:
    from KicadModTree import (
        Arc,
        ChamferedRectangle,
        Circle,
        CompoundPolygon,
        Cross,
        Cruciform,
        Line,
        Polygon,
        Rectangle,
        RoundRectangle,
        Stadium,
        Trapezoid,
    )

    global map_geomshape_node
    map_geomshape_node = {
        GeomLine: Line,
        GeomArc: Arc,
        GeomCircle: Circle,
        GeomRectangle: Rectangle,
        GeomPolygon: Polygon,
        GeomCompoundPolygon: CompoundPolygon,
        GeomCross: Cross,
        GeomCruciform: Cruciform,
        GeomRoundRectangle: RoundRectangle,
        GeomStadium: Stadium,
        GeomTrapezoid: Trapezoid,
        GeomChamferedRectangle: ChamferedRectangle,
    }


@overload
def shape_to_node(
    shape: GeomLine,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Line: ...


@overload
def shape_to_node(
    shape: GeomArc,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Arc: ...


@overload
def shape_to_node(
    shape: GeomCircle,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Circle: ...


@overload
def shape_to_node(
    shape: GeomRectangle,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Rectangle: ...


@overload
def shape_to_node(
    shape: GeomPolygon,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Polygon: ...


@overload
def shape_to_node(
    shape: GeomCompoundPolygon,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> CompoundPolygon: ...


@overload
def shape_to_node(
    shape: GeomCross,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Cross: ...


@overload
def shape_to_node(
    shape: GeomCruciform,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Cruciform: ...


@overload
def shape_to_node(
    shape: GeomRoundRectangle,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> RoundRectangle: ...


@overload
def shape_to_node(
    shape: GeomStadium,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Stadium: ...


@overload
def shape_to_node(
    shape: GeomTrapezoid,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Trapezoid: ...


@overload
def shape_to_node(
    shape: GeomChamferedRectangle,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> ChamferedRectangle: ...


def shape_to_node(
    shape: GeomShapes,
    layer: str,
    width: float | None,
    style: LineStyle = LineStyle.SOLID,
    fill: bool = False,
) -> Shape:
    if not map_geomshape_node:
        _init_map_geomshape_node()
    node_class = map_geomshape_node[type(shape)]
    return node_class(  # type: ignore
        shape=shape, layer=layer, width=width, style=style, fill=fill  # pyright: ignore
    )
