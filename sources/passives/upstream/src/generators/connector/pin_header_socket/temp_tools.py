#! /usr/bin/env python3

# These tools should move to drawingtools.py or other places, but keep them here until stable.

from KicadModTree import (
    Footprint,
    Line,
    Pad,
    Rectangle,
)
from kilibs.geom import Vector2D, Vec2DCompatible, GeomLine, GeomShapeClosed
from kilibs.geom.operations import round_to_grid, round_to_grid_nearest
from kilibs.geom.tolerances import TOL_MM
import generators.tools.footprint.drawing_tools as DT


def Pad2DArrayFromPads(
    start: Vector2D,
    positions: int,
    rows: int,
    pitch: float, # Future: define this as vector or as spacing like PadArray?
    pad_n: Pad,
    pad_1: Pad | None = None,
    # pad_inner: Pad | None = None,
    row_pitch: float | None = None,
    pin1_left: bool = True,
    staggered: bool = False,
    pads_offset: float = 0.0,
    # skipped_pads: Sequence[int] = []
) -> list[Pad]:
    """Generate 1 or more rows (vertically) of Pads from a given pad. (and another for pad1)

    Args:
        start: Starting point for the array, [0,0] for THT.
        positions: Count of (vertical) positions.
        rows: Count of (horizontal) positions.
        pitch: spacing between the positions and rows if row_pitch is not given.
        pad_n: The pad to use for most rows.
        pad_1: The pad to use for pad 1.
        row_pitch: spacing between the rows.
        pin1_left: Used for staggered pads and for rows > 1.
        staggered: place the pads in a zig-zag pattern.
        pads_offset: offset for the pads from where the normally are, used for SMD pads.
    """
    # input conditioning:
    if pad_1 == None: pad_1 = pad_n
    if row_pitch == None: row_pitch = pitch
    # print(f'{rows}x{positions} {pitch:.2f}mm/{row_pitch:.2f}mm start:{start}' +
    # f' {"Left" if pin1_left else "Right"} {"Staggered" if staggered else ""}')

    padlist = []
    pad_x1 = start.x
    for row in range(1, rows + 1):
        # PadArray like behaviour but with flexibility for custom pads.
        initial = row
        increment = rows
        if not(staggered):
            if row == 1:
                p_offset = -pads_offset if pin1_left else pads_offset
            elif row == rows:
                p_offset = pads_offset if pin1_left else -pads_offset
            else: # for 3-4 rows?
                p_offset = 0

        pad_y1 = start.y
        for pad_nr in range(initial, positions * increment +1, increment):
            if staggered:
                if pad_nr % 2 == 1:
                    p_offset = -pads_offset if pin1_left else pads_offset
                else:
                    p_offset = pads_offset if pin1_left else -pads_offset
            if pad_nr == 1:
                # padlist += [pad_1.copy_with(at=Vector2D(p_offset, pad_y1),number=pad_nr)]
                # incorrect for row_count > 1 ToDo: pitch components should be removed from pads_offset in yaml's:
                padlist += [pad_1.copy_with(at=Vector2D(pad_x1 + p_offset, pad_y1),number=pad_nr)]
            # elif row == 1 or row == rows:
            #     padlist += [pad_n.copy_with(at=Vector2D(pad_x1 + p_offset, pad_y1),number=pad_nr)]
            else:
                # padlist += [pad_n.copy_with(at=Vector2D(p_offset, pad_y1),number=pad_nr)]
                # incorrect for row_count > 1 ToDo: pitch components should be removed from pads_offset in yaml's:
                padlist += [pad_n.copy_with(at=Vector2D(pad_x1 + p_offset, pad_y1),number=pad_nr)]
            pad_y1 += pitch

        if pin1_left and rows>1:
            pad_x1 += row_pitch
        else:
            pad_x1 -= row_pitch

    return padlist


def DrawPinArray(
    kicad_mod: Footprint,
    size: Vec2DCompatible,
    count: int,
    pitch: float,
    rows: int = 1,
    start_r: Vec2DCompatible | None = None,
    start_l: Vec2DCompatible | None = None,
    staggered: bool = False,
    start_left: bool = False,
    keepouts: list[GeomShapeClosed] | None = None,
    layer: str = 'F.SilkS',
    linewidth: float = 0.12,
    # style: LineStyle = LineStyle.SOLID,
    grid: float | int = 1e-6, # ToDo: round coordinates to grid
    open_start = True,
    open_tip = False,
    oldBehaviorCanvas: bool = False,
):
    """
    Draw a pin array from top to bottom on specified layer.
    :param count: Number of positions.
    :param pitch: distance between pin-pin centers.
    :param rows: 1 or 2 rows symetrically.
    :param size: Size of the pins.
    :param start_r: Start coordinate right pins, y is middle centered, x is edge of body.
                    Leave None for only left, only x is used for staggered pin1 left.
    :param start_l: Start coordinate left pins, y is middle centered, x is edge of body.
                    Leave None for only right, only x is used for staggered pin1 right.
    :param staggered: draw the pins alternately, depending on start_left
    :param start_left: distance between pin-pin centers.
    :param keepouts: When Keepouts are defined, lines will always be drawn and respecting the keepouts.
    :param open_start: start of the pin is against the body and generally open.
                        If both start and tip are closed, a Rectangle is drawn.
    :param open_tip: An open tip/end can be used to draw the angled pin part of angled headers/sockets.
                        If both start and tip are closed, a Rectangle is drawn.
    """
    if ( (staggered and not(start_r and start_l)) or
        (start_left and not(start_l)) or
        (not(start_left) and not(start_r))
    ):
        raise KeyError("Combination of staggered, start_left, start_r and/or start_l incompatible.")

    # Input Conditioning:
    size = Vector2D(size)
    if start_r: start_r = Vector2D(start_r)
    if start_l: start_l = Vector2D(start_l)
    isRectangle = True if not(keepouts) and not(open_start) and not(open_tip) else False

    if rows > 1: # pins row on each side.
        posleft = range(0, count)
        posright = range(0, count)
    elif staggered:
        if start_left:
            posleft = range(0, count, 2)
            posright = range(1, count, 2)
        else:
            posleft = range(1, count, 2)
            posright = range(0, count, 2)
    else:
        if start_left:
            posleft = range(0, count)
            posright = []
        else:
            posleft = []
            posright = range(0, count)

    if start_l: # not defined if everything should be drawn on the right
        x1 = start_l.x
        x2 = start_l.x - size.x
    for pos in posleft:
        y1 = start_l.y + (pos * pitch) - (size.y / 2)
        y2 = y1 + size.y
        if isRectangle:
            filled = True if pos == 0 else False
            kicad_mod.append(
                Rectangle(start=Vector2D(x1, y1), end=Vector2D(x2, y2), layer=layer, width=linewidth, fill=filled)
            )
        elif oldBehaviorCanvas:
            lines = chamferRect(start=[start_l.x - size.x, y1], end=[start_l.x,y2], draw=(True, False, True, True), normalize=False)
            DT.addLinesToLayer(kicad_mod, layer, lines, linewidth, grid)
        else:
            lines = []
            lines += [GeomLine(start=[x1, y1], end=[x2, y1])]
            if not(open_tip):
                lines += [GeomLine(start=[x2, y1], end=[x2, y2])]
            lines += [GeomLine(start=[x2, y2], end=[x1, y2])]
            if not(open_start):
                lines += [GeomLine(start=[x1, y2], end=[x1, y1])]
            if keepouts is not None:
                lines = DT.applyKeepouts(lines, keepouts)
            DT.addLinesToLayer(kicad_mod, layer, lines, linewidth, grid)

    if start_r: # not defined if everything should be drawn on the left
        x1 = start_r.x
        x2 = start_r.x + size.x
    for pos in posright:
        y1 = start_r.y + (pos * pitch) - (size.y / 2)
        y2 = y1 + size.y
        if isRectangle:
            filled = True if pos == 0 else False
            kicad_mod.append(
                Rectangle(start=Vector2D(x1, y1), end=Vector2D(x2, y2), layer=layer, width=linewidth, fill=filled)
            )
        elif oldBehaviorCanvas:
            lines = chamferRect(start=[x1, y1], end=[x2, y2], draw=(True, True, True, False), normalize=False)
            DT.addLinesToLayer(kicad_mod, layer, lines, linewidth, grid)
        else:
            lines = []
            lines += [GeomLine(start=[x1, y1], end=[x2, y1])]
            if not(open_tip):
                lines += [GeomLine(start=[x2, y1], end=[x2, y2])]
            lines += [GeomLine(start=[x2, y2], end=[x1, y2])]
            if not(open_start):
                lines += [GeomLine(start=[x1, y2], end=[x1, y1])]
            if keepouts is not None:
                lines = DT.applyKeepouts(lines, keepouts)
            DT.addLinesToLayer(kicad_mod, layer, lines, linewidth, grid)


def NormLine(start:Vector2D, end:Vector2D, normalize=False):
    start = Vector2D(start)
    end = Vector2D(end)
    if normalize:
        if end.y < start.y:
            start, end = end, start # swap
        elif end.y == start.y and end.x < start.x:
            start, end = end, start # swap
    return GeomLine(start=start, end=end)


# Draws a chamfered rectangle in clockwise fashion starting with the top horizontal line, ending with chamf[0].
#           0
#       +-------+
#   0 /           \ 1
#    /             \
#   |               |
# 3 |               | 1
#   |               |
#    \             /
#   3 \           / 2
#       +-------+
#           2
def chamferRect(start:Vec2DCompatible, end:Vec2DCompatible = None, size:Vec2DCompatible = None,
    chamf=(0.0, 0.0, 0.0, 0.0), draw=(True, True, True, True), grid=1e-6,
    normalize=True, keepouts=None
) -> list[GeomLine]:
    def _align(a):
        return round_to_grid_nearest(a, grid)

    # input conditioning:
    if end == None and size == None:
        raise ValueError("Either end or size must be specified")
    start = Vector2D(start).round_to(grid)
    if end == None:
        size = Vector2D(size).round_to(grid)
        end = Vector2D.from_floats(start.x + size.x, start.y + size.y)
    else:
        end = Vector2D(end).round_to(grid)
    if type(chamf) in [int, float]:
        chamf = [_align(chamf)] * 4
    elif chamf == None:
        chamf = [0.0] * 4
    else:
        chamf = (_align(chamf[0]), _align(chamf[1]), _align(chamf[2]), _align(chamf[3]))

    lines = []
    if draw[0]: # top horizontal line
        lines += [NormLine(start=[start.x + chamf[0], start.y], end=[end.x - chamf[1], start.y],normalize=normalize )]
    if chamf[1] != 0.0: # top right chamfer
        lines += [NormLine(start=[end.x - chamf[1], start.y], end=[end.x, start.y + chamf[1]],normalize=normalize )]
    if draw[1]: # right vertical line
        lines += [NormLine(start=[end.x, start.y + chamf[1]], end=[end.x, end.y - chamf[2]],normalize=normalize )]
    if chamf[2] != 0.0: # bottom right chamfer
        lines += [NormLine(start=[end.x, end.y - chamf[2]], end=[end.x - chamf[2], end.y],normalize=normalize )]
    if draw[2]: # bottom horizontal line
        lines += [NormLine(start=[end.x - chamf[2], end.y], end=[start.x + chamf[3], end.y],normalize=normalize )]
    if chamf[3] != 0.0: # bottom left chamfer: top
        lines += [NormLine(start=[start.x + chamf[3], end.y], end=[start.x, end.y - chamf[3]],normalize=normalize )]
    if draw[3]: # left vertical line
        lines += [NormLine(start=[start.x, end.y - chamf[3]], end=[start.x, start.y + chamf[0]],normalize=normalize )]
    if chamf[0] != 0.0: # top left chamfer
        lines += [NormLine(start=[start.x, start.y + chamf[0]], end=[start.x + chamf[0], start.y],normalize=normalize )]

    if keepouts != None:
        lines = DT.applyKeepouts(lines, keepouts)
    return lines