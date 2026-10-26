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
# (C) 2022 by Armin Schoisswohl, @armin.sch
# (C) The KiCad Librarian Team

import sys
from typing import cast

from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.base.Circle import Circle
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Pad import Pad
from KicadModTree.nodes.Container import Container
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.Shape import Shape
from KicadModTree.nodes.specialized.Translation import Translation
from KicadModTree.nodes.specialized.Rotation import Rotation
from KicadModTree.util import shape_to_node
from kilibs.geom import GeomCircle, GeomRectangle, GeomShapes
from kilibs.geom.operations import subtract_many


def _extract_shapes_on_layers(
    container: Container[Node],
    layers: list[str],
) -> list[Shape]:
    """Extract all the shape nodes on the given layer from the container node
    recursively.

    Args:
        container: The root node.
        layers: The selected layers.

    Returns:
        The list of collected nodes (those are removed from the container node(s)).
    """
    shapes: list[Shape] = []
    if isinstance(container, Translation | Rotation):
        children = container.transformed_children()
    else:
        children = container.children
    for child in children:
        # TODO: Use the line below and delete the one two lines below. This is currently
        # commented as it would lead to a non-zero diff.
        # if isinstance(child, NodeShape) and child.layer == layer:
        if isinstance(child, Arc | Line | Circle) and child.layer in layers:
            shapes.append(child)
        elif isinstance(child, Container):
            shapes += _extract_shapes_on_layers(cast(Container[Node], child), layers)
    for shape in shapes:
        container.remove(shape)
    return shapes


def _collect_nodes_as_geometric_shapes(
    container: Container[Node],
    layers: list[str],
    select_drill: bool = False,
    silk_pad_clearance: float = 0.0,
) -> list[GeomShapes]:
    """Collect all geometric nodes and pads from a specific layer as geometric nodes
    (Arc, Line, Circle, Rectangle, etc.).

    Args:
        container: The root node.
        layer: The selected layers.
        select_drill: Defines if also drill holes should be selected (to catch NPTHs).
        silk_pad_clearance: Additional clearance between silk and pad to be added to pad
            shapes.

    Returns:
        The list of collected nodes.

    Notes:
        - The shape nodes inside `Translation` or `Rotation` containers will be returned
            with the transformation applied.
        - Pads are converted into rectangles or circles (other shapes are not yet
            supported).
        - Drills are (optionally) included as circles (other shapes not yet supported).
        - `silk_pad_clearance` is an additional offset around pads and holes.
    """
    shapes: list[GeomShapes] = []
    if isinstance(container, Translation | Rotation):
        children = container.transformed_children()
    else:
        children = container.children
    for c in children:
        if isinstance(c, Pad):
            if any(_ in c.layers for _ in layers):
                if c.shape in (Pad.SHAPE_RECT, Pad.SHAPE_ROUNDRECT, Pad.SHAPE_OVAL):
                    shapes.append(
                        GeomRectangle(
                            start=c.at - 0.5 * c.size - silk_pad_clearance,
                            end=c.at + 0.5 * c.size + silk_pad_clearance,
                        ).rotate(angle=-c.rotation, origin=c.at)
                    )
                elif c.shape == Pad.SHAPE_CIRCLE:
                    shapes.append(
                        GeomCircle(
                            center=c.at, radius=c.size[0] / 2 + silk_pad_clearance
                        )
                    )
                else:
                    sys.stderr.write(
                        "cleaning silk over pad is not implemented for pad shape '%s'\n"
                        % c.shape
                    )
            elif select_drill and c.drill:
                if c.drill.x != c.drill.y:
                    sys.stderr.write(
                        "cleaning silk over non-circular drills is not implemented\n"
                    )
                shapes.append(
                    GeomCircle(
                        center=c.at, radius=c.drill[0] * 0.5 + silk_pad_clearance
                    )
                )
        # TODO: Use the line below and delete the one two lines below. This is currently
        # commented as it would lead to a non-zero diff.
        # elif isinstance(c, Shape) and c.layer in layers:
        elif isinstance(c, Arc | Line | Circle) and c.layer in layers:
            shapes.append(c.as_geom_shape())
        elif isinstance(c, Container):
            shapes += _collect_nodes_as_geometric_shapes(
                container=cast(Container[Node], c),
                layers=layers,
                select_drill=select_drill,
                silk_pad_clearance=silk_pad_clearance,
            )
    return shapes


def clean_silk_over_mask(
    container: Container[Node],
    *,
    side: str,
    silk_pad_clearance: float,
    silk_line_width: float,
    ignore_paste: bool = False,
) -> None:
    """Clean the silkscreen contours by removing overlap with pads and holes.

    This is not perfect, but mostly does a very good job.

    Args:
        container: The container node (typically the footprint) to clean up.
        side: `'F'` for front or `'B'` for back side of the footprint.
        silk_pad_clearance: The clearance between silk and pad.
        ignore_paste: If set to `True`, then paste is ignored in calculating the
            silk/mask overlap.
    """
    silk_shapes = _extract_shapes_on_layers(container, [f"{side}.SilkS", "*.SilkS"])
    mask_layers = [f"{side}.Mask", "*.Mask"]
    if not ignore_paste:
        mask_layers += [f"{side}.Paste", "*.Paste"]

    mask_shapes = _collect_nodes_as_geometric_shapes(
        container,
        layers=mask_layers,
        select_drill=True,
        silk_pad_clearance=silk_pad_clearance + 0.5 * silk_line_width,
    )

    for silk_shape in silk_shapes:
        shapes = subtract_many(silk_shape.as_geom_shape(), mask_shapes)  # type: ignore
        for shape in shapes:
            node = shape_to_node(
                shape=shape,
                layer=silk_shape.layer,
                width=silk_shape.width,
                style=silk_shape.style,
                fill=silk_shape.fill,
            )
            container.append(node)
