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

import enum
import math
from collections.abc import Iterable, Sequence
from typing import List, Tuple, Union

from generators.tools.footprint.footprint_global_properties import *
from generators.tools.footprint.nodes import pin1_arrow
from KicadModTree import (
    Arc,
    Circle,
    Footprint,
    Line,
    Node,
    Pad,
    PolygonLine,
    Rectangle,
    Shape,
)
from kilibs.geom import (
    BoundingBox,
    Direction,
    GeomArc,
    GeomCircle,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomShape,
    GeomShapeClosed,
    GeomShapes,
    GeomShapesClosed,
    Vector2D,
)
from kilibs.geom.operations import (
    round_to_grid,
    round_to_grid_down,
    round_to_grid_e,
    round_to_grid_nearest,
    round_to_grid_up,
    subtract_many,
)


# round for grid g
def sqr(x):
    return x * x


# round for courtyard grid
def roundCrt(x: float):
    return round_to_grid(x, grid_crt)


def courtyardFromBoundingBox(bbox: BoundingBox, off: float, grid: float) -> dict:
    """
    Get a courtyard of the given box, with some offset, rounded to the grid

    :param bbox: bounding box of the body
    :param off: clearance
    :param grid: grid size to round to
    """
    return {
        "left": round_to_grid_down(bbox.left - off, grid),
        "right": round_to_grid_up(bbox.right + off, grid),
        "top": round_to_grid_down(bbox.top - off, grid),
        "bottom": round_to_grid_up(bbox.bottom + off, grid),
    }


# float-variant of range()
def frange(x, y, jump):
    while x < y:
        yield x
        x += jump


# inclusice float-variant of range()
def frangei(x, y, jump):
    while x <= y:
        yield x
        x += jump


# returns a list with a single rectangle around x,y with width and height w and h
def addKeepoutRect(x, y, w, h):
    return [GeomRectangle(center=(x, y), size=(w, h))]


# returns a series of rectangle that lie around the circular pad around (x,y) with radius w=h
# if w!=h, addKeepoutRect() is called
def addKeepoutRound(x, y, w, h):
    if w != h:
        # Could do two circles and a rect if we cared enough
        return [GeomRectangle(center=(x, y), size=(w, h))]

    return [GeomCircle(center=(x, y), radius=w / 2)]


def getKeepoutsForPads(
    pads: Pad | Iterable[Pad], clearance: float
) -> list[GeomShapesClosed]:
    """
    Return suitable keepouts for the given pads.

    For the clearance, a common value may be 0.26 for the
    standard silk-pad clearance, for example.

    :param pads: Pad or list of pads
    :param clearance: clearance around pads
    :param keepout: keepout around pads
    :return: list of Keepout objects
    """

    kos: list[GeomShapesClosed] = []
    pads = pads if isinstance(pads, Iterable) else [pads]

    def get_shape_center(pad: Pad) -> Vector2D:

        center = Vector2D(pad.at)

        if pad.rotation == 0 or pad.rotation == 180:
            center += pad.offset
        elif pad.rotation == 90:
            center += Vector2D(pad.offset.y, pad.offset.x)
        elif pad.rotation == 270:
            center += Vector2D(-pad.offset.y, -pad.offset.x)
        else:
            raise ValueError(
                f"Pad rotation {pad.rotation} not supported for non-square pads"
            )

        return center

    for pad in pads:
        center = get_shape_center(pad)
        if pad.shape == Pad.SHAPE_CIRCLE:
            kos.append(GeomCircle(center=center, radius=pad.size.x / 2 + clearance))
        else:
            # Everything else.
            # ovals and roundrects can be more accurate if needed
            # by handling them as a circles + rects

            size = Vector2D(pad.size) + 2 * Vector2D(clearance, clearance)

            if pad.rotation == 0 or pad.rotation == 180:
                pass
            elif pad.rotation == 90 or pad.rotation == 270:
                size = Vector2D(pad.size.y, pad.size.x)
            else:
                # We'll need a polygonal keepout here
                raise ValueError(
                    f"Pad rotation {pad.rotation} not supported for non-square pads"
                )

            kos.append(GeomRectangle(center=pad.at, size=size))

    return kos


# internal method for keepout-processing
def applyKeepouts(
    items: Iterable[GeomShapes],
    keepouts: Iterable[GeomShapesClosed],
) -> list[GeomShapes]:
    new_parts: list[GeomShapes] = []
    for item in items:
        this_part_kept_out = subtract_many(item, keepouts)
        new_parts += this_part_kept_out
    return new_parts


# gives True if the given point (x,y) is contained in any keepout
def containedInAnyKeepout(p: Vector2D, keepouts: List[GeomShapeClosed]) -> bool:
    for ko in keepouts:
        if ko.is_point_inside_self(p):
            return True
    return False


def renderKeepouts(
    keeouts: list[GeomShapeClosed], layer: str = "Cmts.User", width: float = 0.1
) -> list[Node]:
    """
    Debugging function to render keepouts.

    Just add the returned nodes to the footprint to see the keepouts
    (e.g. with `mod.extend( renderKeepouts( keepouts ) ) )`)
    """

    nodes: list[Node] = []
    for ko in keeouts:
        if isinstance(ko, GeomRectangle):
            nodes.append(
                Rectangle(
                    start=ko.top_left,
                    end=ko.bottom_right,
                    layer=layer,
                    width=width,
                )
            )
        elif isinstance(ko, GeomCircle):
            nodes.append(
                Circle(
                    center=ko.center,
                    radius=ko.radius,
                    layer=layer,
                    width=width,
                )
            )
        else:
            raise ValueError(f"Unknown keepout type: {ko}")

    return nodes


def _add_kept_out(
    items: List[Union[GeomArc, GeomCircle, GeomLine]], layer, width, roun
) -> List[Shape]:
    """
    Internal method to add the kept out items to the kicad_mod
    """

    tiny_threshold = width / 2

    # Prune tiny lines and arcs left over from keepout trims
    # TODO: uncomment the 3 comments with items-to_remove
    # items_to_remove = []
    for i, item in enumerate(items):

        tiny = False
        if isinstance(item, GeomLine):
            tiny = item.length < tiny_threshold
        elif isinstance(item, GeomArc):
            tiny = (item.start - item.mid).norm() < tiny_threshold / 2

        if tiny:
            items.remove(item)  # TODO: delete this line
            # items_to_remove.append(i)

    # items = [items[i] for i in range(len(items)) if i not in items_to_remove]

    nodes: list[Node] = []
    for item in items:
        # In here, round off coordinates to the nearest grid point,
        # but be mindful of the fact that we are rounding off to the nearest
        # grid point, not necessarily rounding away from zero (so 1.000003 should be
        # rounded to 1, not 1.01, say).

        if isinstance(item, GeomLine):
            nodes.append(
                Line(
                    start=[
                        round_to_grid_nearest(item.start.x, roun),
                        round_to_grid_nearest(item.start.y, roun),
                    ],
                    end=[
                        round_to_grid_nearest(item.end.x, roun),
                        round_to_grid_nearest(item.end.y, roun),
                    ],
                    layer=layer,
                    width=width,
                )
            )
        elif isinstance(item, GeomCircle):
            nodes.append(
                Circle(
                    center=[
                        round_to_grid_nearest(item.center.x, roun),
                        round_to_grid_nearest(item.center.y, roun),
                    ],
                    radius=round_to_grid_nearest(item.radius, roun),
                    layer=layer,
                    width=width,
                )
            )
        elif isinstance(item, GeomArc):
            nodes.append(
                Arc(
                    start=[
                        round_to_grid_nearest(item.start.x, roun),
                        round_to_grid_nearest(item.start.y, roun),
                    ],
                    mid=[
                        round_to_grid_nearest(item.mid.x, roun),
                        round_to_grid_nearest(item.mid.y, roun),
                    ],
                    end=[
                        round_to_grid_nearest(item.end.x, roun),
                        round_to_grid_nearest(item.end.y, roun),
                    ],
                    layer=layer,
                    width=width,
                )
            )
        else:
            raise ValueError(f"Unknown geometric item: {item}")
    return nodes


# can be used together with applyKeepouts or other list of GeomLine
# does not do the tiny line pruning of _add_kept_out
def addLinesToLayer(kicad_mod: Footprint, layer, lines: list[GeomLine], width, roun):
    for line in lines:
        kicad_mod.append(
            Line(
                start=[
                    round_to_grid_nearest(line.start.x, roun),
                    round_to_grid_nearest(line.start.y, roun),
                ],
                end=[
                    round_to_grid_nearest(line.end.x, roun),
                    round_to_grid_nearest(line.end.y, roun),
                ],
                layer=layer,
                width=width,
            )
        )


def addLinesToSilk(kicak_mod: Footprint, lines: list[GeomLine], width, roun):
    addLinesToLayer(kicak_mod, "F.SilkS", lines, width, roun)


def makeLineWithKeepout(line: GeomLine, layer, width, keepouts=[], roun=0.001):
    """
    Split an arbitrary line so it does not interfere with keepout areas
    """
    kept_out = applyKeepouts([line], keepouts)
    return _add_kept_out(kept_out, layer, width, roun)


def addLineWithKeepout(
    kicad_mod, line: GeomLine, layer, width, keepouts=[], roun=0.001
):
    """Compatibility shim, prefer makeLineWithKeepout in new code"""
    nodes = makeLineWithKeepout(line, layer, width, keepouts, roun)
    for node in nodes:
        kicad_mod.append(node)


# split a horizontal line so it does not interfere with keepout areas defined as [[x0,x1,y0,y1], ...]
def addHLineWithKeepout(
    kicad_mod, x0, x1, y, layer, width, keepouts=[], roun=0.001, dashed=False
):
    if dashed:
        addHDLineWithKeepout(kicad_mod, x0, x1, y, layer, width, keepouts, roun)
    else:
        # print("addHLineWithKeepout",y)
        line = GeomLine(start=[x0, y], end=[x1, y])
        addLineWithKeepout(kicad_mod, line, layer, width, keepouts, roun)


# split a vertical line so it does not interfere with keepout areas
def addVLineWithKeepout(
    kicad_mod, x, y0, y1, layer, width, keepouts=[], roun=0.001, dashed=False
):
    if dashed:
        addVDLineWithKeepout(kicad_mod, x, y0, y1, layer, width, keepouts, roun)
    else:
        # print("addVLineWithKeepout",x)
        line = GeomLine(start=[x, y0], end=[x, y1])
        addLineWithKeepout(kicad_mod, line, layer, width, keepouts, roun)


def makeCircleWithKeepout(circle: GeomCircle, layer, width, keepouts=[], roun=0.001):
    """
    Draw a circle minding the keepouts
    """
    parts_out = applyKeepouts([circle], keepouts)
    return _add_kept_out(parts_out, layer, width, roun)


def addCircleWithKeepout(
    kicad_mod, x, y, radius, layer, width, keepouts=[], roun=0.001
):
    """Compatibility shim, prefer makeCircleWithKeepout in new code"""
    c = GeomCircle(center=[x, y], radius=radius)
    nodes = makeCircleWithKeepout(c, layer, width, keepouts, roun)
    for node in nodes:
        kicad_mod.append(node)


def makeArcWithKeepout(arc: GeomArc, layer, width, keepouts=[], roun=0.001):
    """
    Draw an arc minding the keepouts
    """
    parts_out = applyKeepouts([arc], keepouts)
    return _add_kept_out(parts_out, layer, width, roun)


def addArcWithKeepout(kicad_mod, arc: GeomArc, layer, width, keepouts, roun):
    """Compatibility shim, prefer makeArcWithKeepout in new code"""
    nodes = makeArcWithKeepout(arc, layer, width, keepouts, roun)
    for node in nodes:
        kicad_mod.append(node)


# draw an arc
def addArc(kicad_mod, arc: GeomArc, layer, width, roun=0.001):
    kicad_mod.append(
        Arc(
            start=[
                round_to_grid_nearest(arc.start.x, roun),
                round_to_grid_nearest(arc.start.y, roun),
            ],
            mid=[
                round_to_grid_nearest(arc.mid.x, roun),
                round_to_grid_nearest(arc.mid.y, roun),
            ],
            end=[
                round_to_grid_nearest(arc.end.x, roun),
                round_to_grid_nearest(arc.end.y, roun),
            ],
            layer=layer,
            width=width,
        )
    )


# draw an ellipse with one axis along x-axis and one axis along y-axis and given width/height
def addEllipse(kicad_mod, x, y, w, h, layer, width, roun=0.001):
    addArc(
        kicad_mod=kicad_mod,
        arc=GeomArc(start=[x - w / 2, y], mid=[x, y - h / 2], end=[x + w / 2, y]),
        layer=layer,
        width=width,
        roun=roun,
    )
    addArc(
        kicad_mod=kicad_mod,
        arc=GeomArc(start=[x - w / 2, y], mid=[x, y + h / 2], end=[x + w / 2, y]),
        layer=layer,
        width=width,
        roun=roun,
    )


# draw an ellipse with one axis along x-axis and one axis along y-axis and given width/height
def addEllipseWithKeepout(kicad_mod, x, y, w, h, layer, width, keepouts=[], roun=0.001):
    addArcWithKeepout(
        kicad_mod=kicad_mod,
        arc=GeomArc(start=[x - w / 2, y], mid=[x, y - h / 2], end=[x + w / 2, y]),
        keepouts=keepouts,
        layer=layer,
        width=width,
        roun=roun,
    )
    addArcWithKeepout(
        kicad_mod=kicad_mod,
        arc=GeomArc(start=[x - w / 2, y], mid=[x, y + h / 2], end=[x + w / 2, y]),
        keepouts=keepouts,
        layer=layer,
        width=width,
        roun=roun,
    )


def makeNodesWithKeepout(
    geom_items: Sequence[GeomShapes],
    layer: str,
    width: float,
    keepouts: list[GeomShapesClosed],
    roun=0.001,
    transform: Vector2D = Vector2D(0, 0),
) -> list[Shape]:
    """
    Turn a list of geometric items into a list of nodes, keeping the keepouts in mind.

    Eventually we should do this with a transparent Keepout Node, as that will handle Translations, say,
    but for now this centralises logic.

    Transform is a translation vector to apply to the primitives before applying the keepouts. Which is
    a mediocre substitute for a proper Translation, but it does work quite well for most practical cases
    and again centralises logic here for later refactoring.
    """

    def get_kept_out(p):
        xfrmed = None
        if isinstance(p, GeomLine):
            xfrmed = GeomLine(
                start=p.start + transform,
                end=p.end + transform,
            )
        elif isinstance(p, GeomCircle):
            xfrmed = GeomCircle(
                center=p.center + transform,
                radius=p.radius,
            )
        elif isinstance(p, GeomArc):
            xfrmed = GeomArc(
                center=p.center + transform,
                start=p.start + transform,
                angle=p.angle,
            )
        else:
            raise ValueError(f"Unknown primitive type for transform: {type(p)}")

        return applyKeepouts([xfrmed], keepouts)

    if not isinstance(geom_items, list):
        geom_items = [geom_items]

    decomposed = []
    for item in geom_items:
        decomposed.extend(item.get_atomic_shapes())

    kept_out_prims = []
    for item in decomposed:
        kept_out_prims += get_kept_out(item)
    return _add_kept_out(kept_out_prims, layer, width, roun)


# draw a circle with a screw slit under 45 degrees
def addSlitScrew(kicad_mod, c, radius, layer, width, keepouts=[], roun=0.001):
    """
    Draw a circle with a screw slit under 45 degrees

    :param keepouts: list of keepouts (can be empty)
    """
    c = Vector2D(c)

    addCircleWithKeepout(kicad_mod, c.x, c.y, radius, layer, width, keepouts, roun)

    da = 5
    dx1 = 0.99 * radius * math.sin(math.radians(135 - da))
    dy1 = 0.99 * radius * math.cos(math.radians(135 - da))
    dx2 = 0.99 * radius * math.sin(math.radians(135 + da))
    dy2 = 0.99 * radius * math.cos(math.radians(135 + da))
    dx3 = 0.99 * radius * math.sin(math.radians(315 - da))
    dy3 = 0.99 * radius * math.cos(math.radians(315 - da))
    dx4 = 0.99 * radius * math.sin(math.radians(315 + da))
    dy4 = 0.99 * radius * math.cos(math.radians(315 + da))

    line1 = GeomLine(start=c + [dx1, dy1], end=c + [dx4, dy4])
    line2 = GeomLine(start=c + [dx2, dy2], end=c + [dx3, dy3])

    addLineWithKeepout(kicad_mod, line1, layer, width, keepouts)
    addLineWithKeepout(kicad_mod, line2, layer, width, keepouts)


def addCrossScrew(kicad_mod, c, radius, layer, width, keepouts=[], roun=0.001):
    """
    Draw a circle with a cross-screw under 45 degrees

    :param keepouts: list of keepouts (can be empty)
    """
    c = Vector2D(c)
    dw = 0.75 * radius

    addCircleWithKeepout(kicad_mod, c.x, c.y, radius, layer, width, keepouts, roun)
    addHLineWithKeepout(
        kicad_mod, c.x - dw, c.x + dw, c.y, layer, width, keepouts, roun
    )
    addVLineWithKeepout(
        kicad_mod, c.x, c.y - dw, c.y + dw, layer, width, keepouts, roun
    )


# split a dashed horizontal line so it does not interfere with keepout areas defined as [[x0,x1,y0,y1], ...]
def addHDLineWithKeepout(kicad_mod, x0, x1, y, layer, width, keepouts=[], roun=0.001):
    dx = 3 * width
    x = min(x0, x1)
    while x < max(x0, x1):
        addHLineWithKeepout(
            kicad_mod, x, min(x + dx, x1), y, layer, width, keepouts, roun
        )
        x = x + dx * 2


# split a dashed vertical line so it does not interfere with keepout areas defined as [[x0,x1,y0,y1], ...]
def addVDLineWithKeepout(kicad_mod, x, y0, y1, layer, width, keepouts=[], roun=0.001):
    dy = 3 * width
    y = min(y0, y1)
    while y < max(y0, y1):
        addVLineWithKeepout(
            kicad_mod, x, y, min(y1, y + dy), layer, width, keepouts, roun
        )
        y = y + dy * 2


# split a rectangle
def addRectWith(kicad_mod, x, y, w, h, layer, width, roun=0.001):
    kicad_mod.append(
        Rectangle(
            start=[round_to_grid(x, roun), round_to_grid(y, roun)],
            end=[round_to_grid(x + w, roun), round_to_grid(y + h, roun)],
            layer=layer,
            width=width,
        )
    )


# split a rectangle so it does not interfere with keepout areas defined as [[x0,x1,y0,y1], ...]
def addRectWithKeepout(kicad_mod, x, y, w, h, layer, width, keepouts=[], roun=0.001):
    rect = GeomRectangle(start=Vector2D(x, y), size=Vector2D(w, h))
    kept_out = makeNodesWithKeepout(rect, layer, width, keepouts, roun)
    kicad_mod += kept_out


def makeRectWithKeepout(rect: GeomRectangle, layer, width, keepouts=[], roun=0.001):
    """
    Draw a rectangle minding the keepouts
    """
    lines = rect.get_atomic_shapes()
    parts_out = applyKeepouts(lines, keepouts)
    return _add_kept_out(parts_out, layer, width, roun)


# split a rectangle so it does not interfere with keepout areas defined as [[x0,x1,y0,y1], ...]
def addRectAndTLMarkWithKeepout(
    kicad_mod, x, y, w, h, mark_len, layer, width, keepouts=[], roun=0.001
):
    addHLineWithKeepout(kicad_mod, x, x + w, y, layer, width, keepouts, roun)
    addHLineWithKeepout(kicad_mod, x, x + w, y + h, layer, width, keepouts, roun)
    addVLineWithKeepout(kicad_mod, x, y, y + h, layer, width, keepouts, roun)
    addVLineWithKeepout(kicad_mod, x + w, y, y + h, layer, width, keepouts, roun)
    addHLineWithKeepout(
        kicad_mod,
        x - 2 * width,
        x + mark_len,
        y - 2 * width,
        layer,
        width,
        keepouts,
        roun,
    )
    addVLineWithKeepout(
        kicad_mod,
        x - 2 * width,
        y - 2 * width,
        y + mark_len,
        layer,
        width,
        keepouts,
        roun,
    )


# split a dashed rectangle so it does not interfere with keepout areas defined as [[x0,x1,y0,y1], ...]
def addDRectWithKeepout(kicad_mod, x, y, w, h, layer, width, keepouts=[], roun=0.001):
    addHDLineWithKeepout(kicad_mod, x, x + w, y, layer, width, keepouts, roun)
    addHDLineWithKeepout(kicad_mod, x, x + w, y + h, layer, width, keepouts, roun)
    addVDLineWithKeepout(kicad_mod, x, y, y + h, layer, width, keepouts, roun)
    addVDLineWithKeepout(kicad_mod, x + w, y, y + h, layer, width, keepouts, roun)


# split a plus sign so it does not interfere with keepout areas defined as [[x0,x1,y0,y1], ...]
def addPlusWithKeepout(km, x, y, w, h, layer, width, keepouts=[], roun=0.001):
    addHLineWithKeepout(km, x, x + w, y + h / 2, layer, width, keepouts, roun)
    addVLineWithKeepout(km, x + w / 2, y, y + h, layer, width, keepouts, roun)


# draw a downward equal-sided triangle
def allEqualSidedDownTriangle(model, xcenter, side_length, layer, width):
    h = math.sqrt(3) / 6 * side_length
    model.append(
        PolygonLine(
            shape=[
                [xcenter[0] - side_length / 2, xcenter[1] - h],
                [xcenter[0] + side_length / 2, xcenter[1] - h],
                [xcenter[0], xcenter[1] + 2 * h],
                [xcenter[0] - side_length / 2, xcenter[1] - h],
            ],
            layer=layer,
            width=width,
        )
    )


#     +------+
#    /       |
#   /        |
#   |        |
#   |        |
#   |        |
#   |        |
#   +--------+
#
#
def bevelRectTL(model, x, size, layer, width, bevel_size=1):
    model.append(
        PolygonLine(
            shape=[
                # clockwise from top left (after bevel) to bevel diagonal.
                [x[0] + bevel_size, x[1]],
                [x[0] + size[0], x[1]],
                [x[0] + size[0], x[1] + size[1]],
                [x[0], x[1] + size[1]],
                [x[0], x[1] + bevel_size],
                [x[0] + bevel_size, x[1]],
            ],
            layer=layer,
            width=width,
        )
    )


#   +------+
#   |       \
#   |        \
#   |        |
#   |        |
#   |        |
#   |        |
#   +--------+
def bevelRectTR(model, x, size, layer, width, bevel_size=1):
    model.append(
        PolygonLine(
            shape=[
                # clockwise from top left to bottom left and top left again.
                [x[0], x[1]],
                [x[0] + size[0] - bevel_size, x[1]],
                [x[0] + size[0], x[1] + bevel_size],
                [x[0] + size[0], x[1] + size[1]],
                [x[0], x[1] + size[1]],
                [x[0], x[1]],
            ],
            layer=layer,
            width=width,
        )
    )


#   +--------+
#   |        |
#   |        |
#   |        |
#   |        |
#   \        |
#    \       |
#     +------+
#
#
def bevelRectBL(model, x, size, layer, width, bevel_size=1):
    model.append(
        PolygonLine(
            shape=[
                [x[0], x[1]],
                [x[0] + size[0], x[1]],
                [x[0] + size[0], x[1] + size[1]],
                [x[0] + bevel_size, x[1] + size[1]],
                [x[0], x[1] + size[1] - bevel_size],
                [x[0], x[1]],
            ],
            layer=layer,
            width=width,
        )
    )


#     +----+
#    /      \
#   /        \
#   |        |
#   |        |
#   |        |
#   |        |
#   +--------+
#
#
# add a rectangle that has two angled corners at the top
def addRectAngledTop(kicad_mod, x1, x2, angled_delta, layer, width, roun=0.001):
    xmi = min(x1[0], x2[0])
    xma = max(x1[0], x2[0])
    xa = xma - angled_delta[0]
    xl = xmi + angled_delta[0]
    ymi = max(x1[1], x2[1])
    yma = min(x1[1], x2[1])
    ya = yma + angled_delta[1]
    nodes = [
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ymi, roun)),
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ya, roun)),
        Vector2D(round_to_grid_e(xl, roun), round_to_grid_e(yma, roun)),
        Vector2D(round_to_grid_e(xa, roun), round_to_grid_e(yma, roun)),
        Vector2D(round_to_grid_e(xma, roun), round_to_grid_e(ya, roun)),
        Vector2D(round_to_grid_e(xma, roun), round_to_grid_e(ymi, roun)),
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ymi, roun)),
    ]
    kicad_mod.append(PolygonLine(shape=nodes, layer=layer, width=width))


#     +----+
#    /      \
#   /        \
#   |        |
#   |        |
#   |        |
#   |        |
#   |        |
#
#
# add a rectangle that has two angled corners at the top
def addRectAngledTopNoBottom(kicad_mod, x1, x2, angled_delta, layer, width, roun=0.001):
    xmi = min(x1[0], x2[0])
    xma = max(x1[0], x2[0])
    xa = xma - angled_delta[0]
    xl = xmi + angled_delta[0]
    ymi = max(x1[1], x2[1])
    yma = min(x1[1], x2[1])
    ya = yma + angled_delta[1]
    nodes = [
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ymi, roun)),
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ya, roun)),
        Vector2D(round_to_grid_e(xl, roun), round_to_grid_e(yma, roun)),
        Vector2D(round_to_grid_e(xa, roun), round_to_grid_e(yma, roun)),
        Vector2D(round_to_grid_e(xma, roun), round_to_grid_e(ya, roun)),
        Vector2D(round_to_grid_e(xma, roun), round_to_grid_e(ymi, roun)),
    ]
    kicad_mod.append(PolygonLine(shape=nodes, layer=layer, width=width))


#   +--------+
#   |        |
#   |        |
#   |        |
#   |        |
#   \        /
#    \      /
#     +----+
#
#
# add a rectangle that has two angled corners at the bottom
def addRectAngledBottom(kicad_mod, x1, x2, angled_delta, layer, width, roun=0.001):
    xmi = min(x1[0], x2[0])
    xma = max(x1[0], x2[0])
    xa = xma - angled_delta[0]
    xl = xmi + angled_delta[0]
    ymi = min(x1[1], x2[1])
    yma = max(x1[1], x2[1])
    ya = yma - angled_delta[1]
    nodes = [
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ymi, roun)),
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ya, roun)),
        Vector2D(round_to_grid_e(xl, roun), round_to_grid_e(yma, roun)),
        Vector2D(round_to_grid_e(xa, roun), round_to_grid_e(yma, roun)),
        Vector2D(round_to_grid_e(xma, roun), round_to_grid_e(ya, roun)),
        Vector2D(round_to_grid_e(xma, roun), round_to_grid_e(ymi, roun)),
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ymi, roun)),
    ]
    kicad_mod.append(PolygonLine(shape=nodes, layer=layer, width=width))


#   |        |
#   |        |
#   |        |
#   |        |
#   |        |
#   \        /
#    \      /
#     +----+
#
#
# add a rectangle that has two angled corners at the bottom and no top
def addRectAngledBottomNoTop(kicad_mod, x1, x2, angled_delta, layer, width, roun=0.001):
    xmi = min(x1[0], x2[0])
    xma = max(x1[0], x2[0])
    xa = xma - angled_delta[0]
    xl = xmi + angled_delta[0]
    ymi = min(x1[1], x2[1])
    yma = max(x1[1], x2[1])
    ya = yma - angled_delta[1]
    nodes = [
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ymi, roun)),
        Vector2D(round_to_grid_e(xmi, roun), round_to_grid_e(ya, roun)),
        Vector2D(round_to_grid_e(xl, roun), round_to_grid_e(yma, roun)),
        Vector2D(round_to_grid_e(xa, roun), round_to_grid_e(yma, roun)),
        Vector2D(round_to_grid_e(xma, roun), round_to_grid_e(ya, roun)),
        Vector2D(round_to_grid_e(xma, roun), round_to_grid_e(ymi, roun)),
    ]
    kicad_mod.append(PolygonLine(shape=nodes, layer=layer, width=width))


#        ..---..
#      /    /    \
#    //    /    /  \
#   |/    /    /    |
#  |/    /    /    / |
#   |   /    /    / |
#    \ /    /    / /
#      \   /    //
#        ``---``
#
#
# add a circle which is filled with 45° lines
def addCircleLF(kicad_mod, center, radius, layer, width, linedist=0.3, roun=0.001):
    rend = round_to_grid_e(radius, linedist) + linedist
    M11 = math.cos(math.radians(45))
    M12 = -math.sin(math.radians(45))
    M21 = math.sin(math.radians(45))
    M22 = math.cos(math.radians(45))
    for y in frangei(-rend, rend, linedist):
        if y * y <= radius * radius:
            x1 = -math.sqrt(radius * radius - y * y)
            x2 = -x1
            if x1 != x2:
                kicad_mod.append(
                    Line(
                        start=[
                            round_to_grid_e(M11 * x1 + M12 * y + center[0], roun),
                            round_to_grid_e(M21 * x1 + M22 * y + center[1], roun),
                        ],
                        end=[
                            round_to_grid_e(M11 * x2 + M12 * y + center[0], roun),
                            round_to_grid_e(M21 * x2 + M22 * y + center[1], roun),
                        ],
                        layer=layer,
                        width=width,
                    )
                )

    kicad_mod.append(
        Circle(
            center=[round_to_grid_e(center[0], roun), round_to_grid_e(center[1], roun)],
            radius=round_to_grid_e(radius, roun),
            layer=layer,
            width=width,
        )
    )


# draws a DIP-package with half-circle at the top
#
# +----------+
# |   \  /   |
# |    ~~    |
# |          |
# |          |
# |          |
# |          |
# +----------+
def DIPRectT(model, x, size, layer, width, marker_size=2):
    model.append(
        PolygonLine(
            shape=[
                [x[0] + size[0] / 2 - marker_size / 2, x[1]],
                [x[0], x[1]],
                [x[0], x[1] + size[1]],
                [x[0] + size[0], x[1] + size[1]],
                [x[0] + size[0], x[1]],
                [x[0] + size[0] / 2 + marker_size / 2, x[1]],
            ],
            layer=layer,
            width=width,
        )
    )
    model.append(
        Arc(
            center=[x[0] + size[0] / 2, x[1]],
            start=[x[0] + size[0] / 2 - marker_size / 2, x[1]],
            angle=-180,
            layer=layer,
            width=width,
        )
    )


# draws a DIP-package with half-circle at the left
#
# +---------------+
# |-\             |
# |  |            |
# |-/             |
# +---------------+
def DIPRectL(model, x, size, layer, width, marker_size=2):
    model.append(
        PolygonLine(
            shape=[
                [x[0], x[1] + size[1] / 2 - marker_size / 2],
                [x[0], x[1]],
                [x[0] + size[0], x[1]],
                [x[0] + size[0], x[1] + size[1]],
                [x[0], x[1] + size[1]],
                [x[0], x[1] + size[1] / 2 + marker_size / 2],
            ],
            layer=layer,
            width=width,
        )
    )
    model.append(
        Arc(
            center=[x[0], x[1] + size[1] / 2],
            start=[x[0], x[1] + size[1] / 2 - marker_size / 2],
            angle=180,
            layer=layer,
            width=width,
        )
    )


def CornerBracketWithArrowPointingSouthEast(
    model: Footprint,
    apex: Vector2D,
    arrow_size: float,
    arrow_length: float,
    bracket_max_x: float,
    bracket_max_y: float,
    layer: str,
    line_width_mm: float,
    silk_min_len: float,
):
    """Create an south-east triangular arrow and 90-degree bracket lines

      +
     /|
    +-+  ---
            | bracket_max_x
      |
      | __bracket_max_y

    """
    # minimum clearance between nodes of the lines
    silk_silk_node_clearance = 2 * line_width_mm

    model.append(
        pin1_arrow.Pin1SilkScreenArrow45Deg(
            apex, Direction.SOUTHEAST, arrow_size, layer, line_width_mm
        )
    )

    pin_1_silk_line_len_x = bracket_max_x - (apex.x + silk_silk_node_clearance)
    pin_1_silk_line_len_y = bracket_max_y - (apex.y + silk_silk_node_clearance)

    # There's a gap to avoid merging with the arrow
    # make sure there's enough line left to draw the lines

    if pin_1_silk_line_len_x > silk_min_len:
        tl_horz_line = Line(
            start=Vector2D(apex.x + 2 * line_width_mm, apex.y),
            end=Vector2D(bracket_max_x, apex.y),
            width=line_width_mm,
        )
        model.append(tl_horz_line)

    if pin_1_silk_line_len_y > silk_min_len:
        tl_vert_line = Line(
            start=Vector2D(apex.x, apex.y + 2 * line_width_mm),
            end=Vector2D(apex.x, bracket_max_y),
            width=line_width_mm,
        )
        model.append(tl_vert_line)


def CornerBracketWithArrowPointingSouth(
    model: Footprint,
    apex: Vector2D,
    arrow_size: float,
    arrow_length: float,
    bracket_max_x: float,
    bracket_max_y: float,
    layer: str,
    line_width_mm: float,
    silk_min_len: float,
):
    r"""Create an south-east triangular arrow and 90-degree bracket lines

    Move the whole triangle left if it will hit the pad on the right.

    +---+
     \ /
      +  ---
            | bracket_max_x
      |
      | __bracket_max_y

    """

    # minimum clearance between nodes of the lines
    silk_silk_node_clearance = 2 * line_width_mm

    # shove arrow left away from the pad on the right
    apex.x = min(apex.x, bracket_max_x - arrow_size / 2)

    # Round the apex away from the body corner
    apex.x = round_to_grid_down(apex.x, 0.01)
    apex.y = round_to_grid_down(apex.y, 0.01)

    model.append(
        pin1_arrow.Pin1SilkscreenArrow(
            apex, Direction.SOUTH, arrow_size, arrow_length, layer, line_width_mm
        )
    )

    # a little extra clearance on the side of the arrow
    pin_1_silk_line_len_x = bracket_max_x - (
        apex.x + silk_silk_node_clearance + line_width_mm / 2
    )
    pin_1_silk_line_len_y = bracket_max_y - (apex.y + silk_silk_node_clearance)

    # There's a gap to avoid merging with the arrow
    # make sure there's enough line left to draw the lines

    if pin_1_silk_line_len_x > silk_min_len:
        tl_horz_line = Line(
            start=Vector2D(bracket_max_x, apex.y),
            end=Vector2D(bracket_max_x - pin_1_silk_line_len_x, apex.y),
            width=line_width_mm,
        )
        model.append(tl_horz_line)

    if pin_1_silk_line_len_y > silk_min_len:
        tl_vert_line = Line(
            start=Vector2D(apex.x, bracket_max_y),
            end=Vector2D(apex.x, bracket_max_y - pin_1_silk_line_len_y),
            width=line_width_mm,
        )
        model.append(tl_vert_line)


class SilkArrowSize(enum.Enum):
    """
    Silkscreen arrow edge length in mm.
    """

    SMALL = 0.4
    MEDIUM = 0.6
    LARGE = 0.8
    HUGE = 1.0  # IPC maximum


def getStandardSilkArrowSize(
    size: SilkArrowSize, silk_line_width: float
) -> Tuple[float, float]:
    """
    Get the normal size of the arrow for a given enum value.

    This gives the "node-node" size.
    """
    # slight squashed relative to equilateral triangle
    # reduces intrusion of arrows into other footprints' spaces
    standard_arrow_aspect_ratio = 0.7

    # allows for 0.01mm grid-snap on each side of the apex
    width = round_to_grid_down(size.value - silk_line_width, 0.02)
    length = round_to_grid_down(width * standard_arrow_aspect_ratio, 0.01)

    return width, length


#
# This is an alternative to using silk keepout areas for simple cases.
# It calculates a new endpoint for a horizontal or vertical line such that
# the silk line has the correct minimal clearance. If the line is to short
# given the default clearance, the clearance is reduced and new points are
# calculated.
#
# Parameters:
#   - pad_size, pad_position, and pad_radius are the dimensions of the reference pad.
#     (pad that is expected to be intersected by the line)
#   - fixed_point: The fixed reference point
#   - moving_point: The point that will be moved (toward the fixed point)
#     if the line intersects the pads clearance area.
#   - silk_pad_offset: offset between edge of the pad and silk line center.
#   - min_length: minimum silk line length
#
# Returns a new point along the line or None if no valid point could be found
#
def nearestSilkPointOnOrthogonalLineSmallClerance(
    pad_size,
    pad_position,
    pad_radius,
    fixed_point,
    moving_point,
    silk_pad_offset_default,
    silk_pad_offset_reduced,
    min_length,
):
    if silk_pad_offset_reduced < silk_pad_offset_default:
        offset = (silk_pad_offset_default, silk_pad_offset_reduced)
    else:
        offset = silk_pad_offset_default

    for silk_pad_offset in (silk_pad_offset_default, silk_pad_offset_reduced):
        point = nearestSilkPointOnOrthogonalLine(
            pad_size,
            pad_position,
            pad_radius,
            fixed_point,
            moving_point,
            silk_pad_offset,
            min_length,
        )
        if point is not None:
            return point
    return None


#
# This is an alternative to using silk keepout areas for simple cases.
# It calculates a new endpoint for a horizontal or vertical line such that
# the silk line has the correct minimal clearance.
#
# Parameters:
#   - pad_size, pad_position, and pad_radius are the dimensions of the reference pad.
#     (pad that is expected to be intersected by the line)
#   - fixed_point: The fixed reference point
#   - moving_point: The point that will be moved (toward the fixed point)
#     if the line intersects the pads clearance area.
#   - silk_pad_offset: offset between edge of the pad and silk line center.
#   - min_length: minimum silk line length
#
# Returns a new point along the line or None if no valid point could be found
#
def nearestSilkPointOnOrthogonalLine(
    pad_size,
    pad_position,
    pad_radius,
    fixed_point,
    moving_point,
    silk_pad_offset,
    min_length,
):
    if fixed_point[0] == moving_point[0]:
        normal_dir_idx = 0
    elif fixed_point[1] == moving_point[1]:
        normal_dir_idx = 1
    else:
        raise ValueError(
            "nearestSilkPointOnOrthogonalLine only works for horizontal or vertical lines. \n"
            "(Either x or y coordinate of the two reference points must be equal)"
        )

    inline_dir_idx = (normal_dir_idx + 1) % 2

    line_pad_offset = fixed_point[normal_dir_idx] - pad_position[normal_dir_idx]

    rc_normal_dir = pad_size[normal_dir_idx] / 2 - pad_radius

    sign = 1 if pad_position[inline_dir_idx] - fixed_point[inline_dir_idx] > 0 else -1
    ep_new = Vector2D(moving_point)

    if rc_normal_dir < line_pad_offset:
        # the silk outline is in the area where the radius of the pad is.

        dr_normal_dir = line_pad_offset - rc_normal_dir

        r = pad_radius + silk_pad_offset

        # rounding to avoid floating point errors
        if round(dr_normal_dir, 6) >= round(r, 6):
            return moving_point

        dr_inline = math.sqrt(r**2 - dr_normal_dir**2)

        ep_new[inline_dir_idx] = pad_position[inline_dir_idx] - sign * (
            pad_size[inline_dir_idx] / 2 - (pad_radius - dr_inline)
        )
    else:
        ep_new[inline_dir_idx] = pad_position[inline_dir_idx] - sign * (
            pad_size[inline_dir_idx] / 2 + silk_pad_offset
        )

    if sign * (ep_new[inline_dir_idx] - fixed_point[inline_dir_idx]) < min_length:
        return None

    if abs(ep_new[inline_dir_idx] - fixed_point[inline_dir_idx]) > math.fabs(
        moving_point[inline_dir_idx] - fixed_point[inline_dir_idx]
    ):
        return moving_point

    return ep_new


#
# Check if c point intersects the line segment from a to b points
#
# Parameters:
#    a: point coordinates as Vector2D
#    b: point coordinates as Vector2D
#    c: point coordinates as Vector2D
#
# Return iff point c intersects the line segment from a to b.
#
# Code adapted from post from Darius Bacon (code posted at 2008) at:
# https://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
#
# StackOverflow licensing is CC BY-SA 2.5. Check at: https://stackoverflow.com/help/licensing
#
def point_is_on_segment(a, b, c):
    "Return true iff point c intersects the line segment from a to b."
    # (or the degenerate case that all 3 points are coincident)
    return collinear_points(a, b, c) and (
        point_within(a.x, c.x, b.x) if a.x != b.x else point_within(a.y, c.y, b.y)
    )


#
# Check if a,b,c points all lie on the same line.
#
# Parameters:
#    a: point coordinates as Vector2D
#    b: point coordinates as Vector2D
#    c: point coordinates as Vector2D
#
# Return true iff a, b, and c all lie on the same line.
#
# Code adapted from post from Darius Bacon (code posted at 2008) at:
# https://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
#
# StackOverflow licensing is CC BY-SA 2.5. Check at: https://stackoverflow.com/help/licensing
#
def collinear_points(a, b, c):
    "Return true iff a, b, and c all lie on the same line."
    if (abs(((b.x - a.x) * (c.y - a.y)) - ((c.x - a.x) * (b.y - a.y)))) <= 0.000001:
        return True
    else:
        return False


#
# Check if q point is between p and r points
#
# Parameters:
#    p: scalar coordinate
#    q: scalar coordinate
#    r: scalar coordinate
#
# Return true iff q is between p and r (inclusive).
#
# Code adapted from post from Darius Bacon (code posted at 2008) at:
# https://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
#
# StackOverflow licensing is CC BY-SA 2.5. Check at: https://stackoverflow.com/help/licensing
#
def point_within(p, q, r):
    "Return true iff q is between p and r (inclusive)."
    return p <= q <= r or r <= q <= p
