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

import os
from typing import Optional

import generators.tools.footprint.drawing_tools as DT
from KicadModTree import (
    Circle,
    Footprint,
    FootprintType,
    Line,
    Model,
    Node,
    Pad,
    Property,
    Rectangle,
    Text,
    Translation,
)
from kilibs.geom import BoundingBox, Direction, Vector2D, GeomRectangle, GeomShapeClosed
from generators.tools.footprint.footprint_global_properties import *
from generators.tools.footprint.save_footprint import write_footprint
from kilibs.config import global_config as GC
from generators.tools.footprint.nodes import pin1_arrow

crt_offset = 0.5  # different for connectors
slk_offset = lw_slk


def make_silk_outline_with_pin1_arrow(
    silk_rect: GeomRectangle,
    arrow_x: float,
    line_width: float,
    keepouts: list[GeomShapeClosed],
    pin1_keepouts: list[GeomShapeClosed],
    arrow_direction: Direction,
) -> list[Node]:
    """

    +-------------------------+
    |                         |
    +---  --------------------+
        /\
        --

    Args:
        pin1_keepouts: subset of the keepouts that relate to pin 1.
            This is used to bump the arrow out of the way of the pads
            if needed.
        arrow_direction: Direction of the pin1 arrow. Must be either NORTH or SOUTH.
    """

    if arrow_direction not in (Direction.NORTH, Direction.SOUTH):
        raise ValueError("Arrow direction must be either NORTH or SOUTH")

    # Terminal blocks are big items, so we use a bigger arrow
    # (it's still not that big really)
    arrow_size, arrow_length = DT.getStandardSilkArrowSize(
        DT.SilkArrowSize.HUGE, lw_slk
    )

    if arrow_direction == Direction.NORTH:
        max_arrow_y = silk_rect.bottom
    else:  # SOUTH
        max_arrow_y = silk_rect.top

    # Bump arrow out of the way of the pads if needed
    if pin1_keepouts:
        pin1_bbox = BoundingBox()
        for ko in pin1_keepouts:
            pin1_bbox.include_bbox(ko.bbox())

        if arrow_direction == Direction.NORTH:
            max_arrow_y = max(max_arrow_y, pin1_bbox.bottom)
        else:  # SOUTH
            max_arrow_y = min(max_arrow_y, pin1_bbox.top)

    pin1_arrow_apex = Vector2D.from_floats(arrow_x, max_arrow_y)
    pin1_arrow_keepout = GeomRectangle(
        center=pin1_arrow_apex,
        size=Vector2D.from_floats(line_width * 5, line_width * 5),
    )

    nodes = DT.makeNodesWithKeepout(
        geom_items=[silk_rect],
        layer="F.SilkS",
        width=lw_slk,
        keepouts=keepouts + [pin1_arrow_keepout],
    )

    # Silkscreen pin1 marker
    nodes.append(
        pin1_arrow.Pin1SilkscreenArrow(
            apex_position=pin1_arrow_apex,
            angle=arrow_direction,
            size=arrow_size,
            length=arrow_length,
            layer="F.SilkS",
            line_width_mm=line_width,
        )
    )

    return nodes

#
#  +----------------------------------------+                      ^
#  |       H           H           H        | ^                    |
#  |                                        | |                    |
#  |      OOO         OOO         OOO       | |secondHoleOffset    | package_height
#  |     OOOOO       OOOOO       OOOOO      | v                    |                  ^
#  |      OOO         OOO         OOO       |                      |                  |
#  +----------------------------------------+ ^                    |                  | leftbottom_offset
#  |                                        | | bevel_height       |                  |
#  +----------------------------------------+ v                    v                  v
#          <--- rm ---->
#  <------>leftbottom_offset[0]     <------->leftbottom_offset[2] (or leftbottom_offset[0]  if len(leftbottom_offset)==2)
#
#
#
def makeTerminalBlockStd(
    generator_name,
    footprint_name,
    pins,
    rm,
    package_height,
    leftbottom_offset,
    ddrill,
    pad,
    screw_diameter,
    bevel_height,
    slit_screw=True,
    screw_pin_offset=[0, 0],
    secondHoleDiameter=0,
    secondHoleOffset=[0, 0],
    thirdHoleDiameter=0,
    thirdHoleOffset=[0, 0],
    fourthHoleDiameter=0,
    fourthHoleOffset=[0, 0],
    secondDrillDiameter=0,
    secondDrillOffset=[0, 0],
    secondDrillPad=[0, 0],
    nibbleSize: Optional[Vector2D] = None,
    nibblePos: Optional[Vector2D] = None,
    fabref_offset=[0, 0],
    stackable=False,
    tags_additional=[],
    lib_name: Optional[str]="Connectors_Terminal_Blocks",
    classname="Connectors_Terminal_Blocks",
    classname_description="terminal block",
    webpage="",
):
    global_config = GC.GLOBAL_CONFIG

    package_size = Vector2D.from_floats(2 * leftbottom_offset[0] + (pins - 1) * rm, package_height)
    if len(leftbottom_offset) == 3:
        package_size = Vector2D.from_floats(
            leftbottom_offset[0] + leftbottom_offset[2] + (pins - 1) * rm,
            package_height,
        )

    h_fab = package_size[1]
    w_fab = package_size[0]
    l_fab = -leftbottom_offset[0]
    t_fab = -(h_fab - leftbottom_offset[1])

    h_slk = h_fab + 2 * slk_offset
    w_slk = w_fab + 2 * slk_offset
    l_slk = l_fab - slk_offset
    t_slk = t_fab - slk_offset

    h_crt = h_fab + 2 * crt_offset
    w_crt = w_fab + (0 if stackable else 2 * crt_offset)
    l_crt = l_fab - (0 if stackable else crt_offset)
    t_crt = t_fab - crt_offset

    text_size = w_fab * 0.6
    fab_text_size_max = 1.0
    if text_size < fab_text_size_min:
        text_size = fab_text_size_min
    elif text_size > fab_text_size_max:
        text_size = fab_text_size_max
    text_size = round(text_size, 2)
    text_size = [text_size, text_size]
    text_t = text_size[0] * 0.15

    description = (
        f"{classname_description}, {pins} pins, pitch {rm:.3g}mm, "
        f"size {package_size[0]:.3g}x{package_size[1]:.3g}mm, "
        f"drill diameter {ddrill:.3g}mm, pad diameter {max(pad):.3g}mm, {webpage}"
    )

    tags = [
        "THT",
        classname_description,
        f"pitch {rm:.3g}mm",
        f"size {package_size[0]:.3g}x{package_size[1]:.3g}mm",
        f"drill {ddrill:.3g}mm",
        f"pad {max(pad):.3g}mm",
    ]

    if len(tags_additional) > 0:
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags.append(t)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(description)
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = [0, 0]
    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[l_fab + w_fab / 2, t_slk - txt_offset],
            layer="F.SilkS",
        )
    )
    if type(fabref_offset) in (tuple, list):
        kicad_modg.append(
            Text(
                text="${REFERENCE}",
                at=[
                    l_fab + w_fab / 2 + fabref_offset[0],
                    t_fab + h_fab / 2 + fabref_offset[1],
                ],
                layer="F.Fab",
                size=text_size,
                thickness=text_t,
            )
        )
    else:
        kicad_modg.append(
            Text(
                text="${REFERENCE}",
                at=[l_fab + w_fab / 2, t_slk - txt_offset],
                layer="F.Fab",
                size=text_size,
                thickness=text_t,
            )
        )
    kicad_modg.append(
        Property(
            name=Property.VALUE,
            text=footprint_name,
            at=[l_fab + w_fab / 2, t_slk + h_slk + txt_offset],
            layer="F.Fab",
        )
    )

    # create pads
    p1 = int(1)
    x1 = 0
    y1 = 0

    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_ROUNDRECT
    pad_shapeother = Pad.SHAPE_CIRCLE
    if pad[0] != pad[1]:
        pad_shapeother = Pad.SHAPE_OVAL

    extradrill1_type = Pad.TYPE_NPTH
    if (
        secondDrillPad[0] > secondDrillDiameter
        or secondDrillPad[1] > secondDrillDiameter
    ):
        extradrill1_type = Pad.TYPE_THT

    if secondDrillDiameter > 0:
        if secondDrillPad[0] < secondDrillDiameter:
            secondDrillPad[0] = secondDrillDiameter
        if secondDrillPad[1] < secondDrillDiameter:
            secondDrillPad[1] = secondDrillDiameter

    pad_shape_extra = Pad.SHAPE_CIRCLE
    if secondDrillPad[0] != secondDrillPad[1]:
        pad_shape_extra = Pad.SHAPE_OVAL

    pad_layers = Pad.LAYERS_THT
    keepouts: list[GeomShapeClosed] = []
    pin1_keepouts: list[GeomShapeClosed] = []

    for p in range(1, pins + 1):
        pextra = 0
        if secondDrillPad[0] > 0:
            pextra = p
        if p == 1:
            kicad_modg.append(
                Pad(
                    number=p,
                    type=pad_type,
                    shape=pad_shape1,
                    at=[x1, y1],
                    size=pad,
                    drill=ddrill,
                    layers=pad_layers,
                    round_radius_handler=global_config.roundrect_radius_handler,
                )
            )
            pin1_keepouts += DT.addKeepoutRect(
                x1, y1, pad[0] + 8 * slk_offset, pad[1] + 8 * slk_offset
            )
            if secondDrillDiameter > 0:
                if extradrill1_type == Pad.TYPE_NPTH:
                    num = ""
                    extra_shape = pad_shape_extra
                else:
                    num = str(p)
                    extra_shape = Pad.SHAPE_RECT
                kicad_modg.append(
                    Pad(
                        number=num,
                        type=extradrill1_type,
                        shape=extra_shape,
                        at=[x1 + secondDrillOffset[0], y1 + secondDrillOffset[1]],
                        size=secondDrillPad,
                        drill=secondDrillDiameter,
                        layers=pad_layers,
                    )
                )
                pin1_keepouts += DT.addKeepoutRect(
                    x1 + secondDrillOffset[0],
                    y1 + secondDrillOffset[1],
                    max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                    max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                )

            keepouts += pin1_keepouts
        else:
            kicad_modg.append(
                Pad(
                    number=p,
                    type=pad_type,
                    shape=pad_shapeother,
                    at=[x1, y1],
                    size=pad,
                    drill=ddrill,
                    layers=pad_layers,
                )
            )
            if secondDrillPad[0] != secondDrillPad[1]:
                keepouts = keepouts +  DT.addKeepoutRect(
                    x1, y1, pad[0] + 8 * slk_offset, pad[1] + 8 * slk_offset
                )
            else:
                keepouts = keepouts +  DT.addKeepoutRound(
                    x1, y1, pad[0] + 8 * slk_offset, pad[0] + 8 * slk_offset
                )
            if secondDrillDiameter > 0:
                if extradrill1_type == Pad.TYPE_NPTH:
                    num = ""
                else:
                    num = str(p)
                kicad_modg.append(
                    Pad(
                        number=num,
                        type=extradrill1_type,
                        shape=pad_shape_extra,
                        at=[x1 + secondDrillOffset[0], y1 + secondDrillOffset[1]],
                        size=secondDrillPad,
                        drill=secondDrillDiameter,
                        layers=pad_layers,
                    )
                )
                keepouts = keepouts +  DT.addKeepoutRect(
                    x1 + secondDrillOffset[0],
                    y1 + secondDrillOffset[1],
                    max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                    max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                )

        x1 = x1 + rm

    # create Body
    if len(bevel_height) > 0:
        chamfer = min(h_fab / 4, 2, bevel_height[0])
    else:
        chamfer = min(h_fab / 4, 2)
    DT.bevelRectBL(
        kicad_modg, [l_fab, t_fab], [w_fab, h_fab], "F.Fab", lw_fab, bevel_size=chamfer
    )
    for bh in bevel_height:
        kicad_modg.append(
            Line(
                start=[l_fab, t_fab + h_fab - bh],
                end=[l_fab + w_fab, t_fab + h_fab - bh],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        DT.addHLineWithKeepout(
            kicad_modg,
            l_slk,
            l_slk + w_slk,
            t_fab + h_fab - bh,
            layer="F.SilkS",
            width=lw_slk,
            keepouts=keepouts,
        )

    kicad_modg += make_silk_outline_with_pin1_arrow(
        GeomRectangle(start=Vector2D(l_slk, t_slk), size=Vector2D(w_slk, h_slk)),
        0,
        lw_slk,
        keepouts,
        pin1_keepouts,
        Direction.NORTH,
    )

    # screws + other repeated features
    if screw_diameter > 0:
        for p in range(1, pins + 1):
            if screw_diameter > 0:
                screw_pos = Vector2D(
                    (p - 1) * rm + screw_pin_offset[0], screw_pin_offset[1]
                )
                if slit_screw:
                    DT.addSlitScrew(
                        kicad_modg,
                        screw_pos,
                        screw_diameter / 2,
                        "F.Fab",
                        lw_fab,
                        roun=0.001,
                    )
                else:
                    DT.addCrossScrew(
                        kicad_modg,
                        screw_pos,
                        screw_diameter / 2,
                        "F.Fab",
                        lw_fab,
                        roun=0.001,
                    )

            if (
                not (type(secondHoleDiameter) in (tuple, list))
                and secondHoleDiameter > 0
                and (p - 1) * rm + secondHoleOffset[0] < l_fab + w_fab
            ):
                kicad_modg.append(
                    Circle(
                        center=[
                            (p - 1) * rm + secondHoleOffset[0],
                            0 + secondHoleOffset[1],
                        ],
                        radius=secondHoleDiameter / 2,
                        layer="F.Fab",
                        width=lw_fab,
                    )
                )
                DT.addCircleWithKeepout(
                    kicad_modg,
                    (p - 1) * rm + secondHoleOffset[0],
                    0 + secondHoleOffset[1],
                    secondHoleDiameter / 2,
                    "F.SilkS",
                    lw_slk,
                    keepouts,
                )
            if (
                not (type(thirdHoleDiameter) in (tuple, list))
                and thirdHoleDiameter > 0
                and (p - 1) * rm + thirdHoleOffset[0] < l_fab + w_fab
            ):
                kicad_modg.append(
                    Circle(
                        center=[
                            (p - 1) * rm + thirdHoleOffset[0],
                            0 + thirdHoleOffset[1],
                        ],
                        radius=thirdHoleDiameter / 2,
                        layer="F.Fab",
                        width=lw_fab,
                    )
                )
                DT.addCircleWithKeepout(
                    kicad_modg,
                    (p - 1) * rm + thirdHoleOffset[0],
                    0 + thirdHoleOffset[1],
                    thirdHoleDiameter / 2,
                    "F.SilkS",
                    lw_slk,
                    keepouts,
                )
            if (
                not (type(fourthHoleDiameter) in (tuple, list))
                and fourthHoleDiameter > 0
                and (p - 1) * rm + fourthHoleOffset[0] < l_fab + w_fab
            ):
                kicad_modg.append(
                    Circle(
                        center=[
                            (p - 1) * rm + fourthHoleOffset[0],
                            0 + fourthHoleOffset[1],
                        ],
                        radius=fourthHoleDiameter / 2,
                        layer="F.Fab",
                        width=lw_fab,
                    )
                )
                DT.addCircleWithKeepout(
                    kicad_modg,
                    (p - 1) * rm + fourthHoleOffset[0],
                    0 + fourthHoleOffset[1],
                    fourthHoleDiameter / 2,
                    "F.SilkS",
                    lw_slk,
                    keepouts,
                )
            if (type(secondHoleDiameter) in (tuple, list)) and (
                p - 1
            ) * rm + secondHoleOffset[0] < l_fab + w_fab:
                kicad_modg.append(
                    Rectangle(
                        start=[
                            (p - 1) * rm
                            + secondHoleOffset[0]
                            - secondHoleDiameter[0] / 2,
                            0 + secondHoleOffset[1] - secondHoleDiameter[1] / 2,
                        ],
                        end=[
                            (p - 1) * rm
                            + secondHoleOffset[0]
                            + secondHoleDiameter[0] / 2,
                            0 + secondHoleOffset[1] + secondHoleDiameter[1] / 2,
                        ],
                        layer="F.Fab",
                        width=lw_fab,
                    )
                )
                DT.addRectWithKeepout(
                    kicad_modg,
                    (p - 1) * rm + secondHoleOffset[0] - secondHoleDiameter[0] / 2,
                    0 + secondHoleOffset[1] - secondHoleDiameter[1] / 2,
                    secondHoleDiameter[0],
                    secondHoleDiameter[1],
                    "F.SilkS",
                    lw_slk,
                    keepouts,
                )
            if (type(thirdHoleDiameter) in (tuple, list)) and (
                p - 1
            ) * rm + thirdHoleOffset[0] < l_fab + w_fab:
                kicad_modg.append(
                    Rectangle(
                        start=[
                            (p - 1) * rm
                            + thirdHoleOffset[0]
                            - thirdHoleDiameter[0] / 2,
                            0 + thirdHoleOffset[1] - thirdHoleDiameter[1] / 2,
                        ],
                        end=[
                            (p - 1) * rm
                            + thirdHoleOffset[0]
                            + thirdHoleDiameter[0] / 2,
                            0 + thirdHoleOffset[1] + thirdHoleDiameter[1] / 2,
                        ],
                        layer="F.Fab",
                        width=lw_fab,
                    )
                )
                DT.addRectWithKeepout(
                    kicad_modg,
                    (p - 1) * rm + thirdHoleOffset[0] - thirdHoleDiameter[0] / 2,
                    0 + thirdHoleOffset[1] - thirdHoleDiameter[1] / 2,
                    thirdHoleDiameter[0],
                    thirdHoleDiameter[1],
                    "F.SilkS",
                    lw_slk,
                    keepouts,
                )
            if (type(fourthHoleDiameter) in (tuple, list)) and (
                p - 1
            ) * rm + fourthHoleOffset[0] < l_fab + w_fab:
                kicad_modg.append(
                    Rectangle(
                        start=[
                            (p - 1) * rm
                            + fourthHoleOffset[0]
                            - fourthHoleDiameter[0] / 2,
                            0 + fourthHoleOffset[1] - fourthHoleDiameter[1] / 2,
                        ],
                        end=[
                            (p - 1) * rm
                            + fourthHoleOffset[0]
                            + fourthHoleDiameter[0] / 2,
                            0 + fourthHoleOffset[1] + fourthHoleDiameter[1] / 2,
                        ],
                        layer="F.Fab",
                        width=lw_fab,
                    )
                )
                DT.addRectWithKeepout(
                    kicad_modg,
                    (p - 1) * rm + fourthHoleOffset[0] - fourthHoleDiameter[0] / 2,
                    0 + fourthHoleOffset[1] - fourthHoleDiameter[1] / 2,
                    fourthHoleDiameter[0],
                    fourthHoleDiameter[1],
                    "F.SilkS",
                    lw_slk,
                    keepouts,
                )

    # nibble
    if nibbleSize is not None:
        assert nibblePos is not None
        kicad_modg.append(
            Rectangle(
                start=[l_fab + nibblePos[0], t_fab + nibblePos[1]],
                end=[
                    l_fab + nibblePos[0] + nibbleSize[0],
                    t_fab + nibblePos[1] + nibbleSize[1],
                ],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        DT.addRectWithKeepout(
            kicad_modg,
            l_fab + nibblePos[0] - slk_offset,
            t_fab + nibblePos[1] - slk_offset,
            nibbleSize[0],
            nibbleSize[1] + 2 * slk_offset,
            "F.SilkS",
            lw_slk,
            keepouts,
        )

    # create courtyard
    kicad_mod.append(
        Rectangle(
            start=[DT.roundCrt(l_crt + offset[0]), DT.roundCrt(t_crt + offset[1])],
            end=[
                DT.roundCrt(l_crt + offset[0] + w_crt),
                DT.roundCrt(t_crt + offset[1] + h_crt),
            ],
            layer="F.CrtYd",
            width=lw_crt,
        )
    )

    # If no lib_name is given, the caller handles this
    if lib_name is not None:
        model_filename = global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix
        kicad_modg.append(
            Model(
                filename=model_filename,
                at=[0, 0, 0],
                scale=[1, 1, 1],
                rotate=[0, 0, 0],
            )
        )
        write_footprint(kicad_mod, lib_name, generator_name)

    return kicad_mod

#
#  +----------------------------------------+                      ^
#  |       H           H           H        | ^                    |
#  |  -----------                           | |                    |                                       ^
#  |  |   OOO   |     OOO         OOO       | |secondHoleOffset    | package_height                        |
#  |  |  OOOOO  |    OOOOO       OOOOO      | v                    |                  ^                    | opening[1]
#  |  |   OOO   |     OOO         OOO       |                      |                  |                    |
#  +----------------------------------------+ ^                    |                  | leftbottom_offset  x
#  |                                        | | bevel_height       |                  |                    | opening_yoffset
#  +----------------------------------------+ v                    v                  v                    v
#          <--- rm ---->
#  <------>leftbottom_offset[0]     <------->leftbottom_offset[2] (or leftbottom_offset[0]  if len(leftbottom_offset)==2)
#     <---------> opening[0]
#
#
def makeTerminalBlockVertical(
    generator_name,
    footprint_name,
    pins,
    rm,
    package_height,
    leftbottom_offset,
    ddrill,
    pad,
    opening,
    opening_yoffset,
    bevel_height,
    opening_xoffset=0,
    secondHoleDiameter=0,
    secondHoleOffset=[0, 0],
    thirdHoleDiameter=0,
    thirdHoleOffset=[0, 0],
    fourthHoleDiameter=0,
    fourthHoleOffset=[0, 0],
    secondDrillDiameter=0,
    secondDrillOffset=[0, 0],
    secondDrillPad=[0, 0],
    nibbleSize: Optional[Vector2D] = None,
    nibblePos: Optional[Vector2D] = None,
    fabref_offset=[0, 0],
    stackable=False,
    tags_additional=[],
    lib_name: Optional[str]="Connectors_Terminal_Blocks",
    classname="Connectors_Terminal_Blocks",
    classname_description="terminal block",
    webpage="",
):
    global_config = GC.GLOBAL_CONFIG

    package_size = Vector2D.from_floats(2 * leftbottom_offset[0] + (pins - 1) * rm, package_height)
    if len(leftbottom_offset) == 3:
        package_size = Vector2D.from_floats(
            leftbottom_offset[0] + leftbottom_offset[2] + (pins - 1) * rm,
            package_height,
        )

    h_fab = package_size[1]
    w_fab = package_size[0]
    l_fab = -leftbottom_offset[0]
    t_fab = -(h_fab - leftbottom_offset[1])

    h_slk = h_fab + 2 * slk_offset
    w_slk = w_fab + 2 * slk_offset
    l_slk = l_fab - slk_offset
    t_slk = t_fab - slk_offset

    h_crt = h_fab + 2 * crt_offset
    w_crt = w_fab + (0 if stackable else 2 * crt_offset)
    l_crt = l_fab - (0 if stackable else crt_offset)
    t_crt = t_fab - crt_offset

    text_size = w_fab * 0.6
    fab_text_size_max = 1.0
    if text_size < fab_text_size_min:
        text_size = fab_text_size_min
    elif text_size > fab_text_size_max:
        text_size = fab_text_size_max
    text_size = round(text_size, 2)
    text_size = [text_size, text_size]
    text_t = text_size[0] * 0.15

    description = (
        f"{classname_description}, vertical (cable from top), "
        f"{pins} pins, pitch {rm:.3g}mm, size {package_size[0]:.3g}x{package_size[1]:.3g}mm, "
        f"drill diameter {ddrill:.3g}mm, pad diameter {max(pad):.3g}mm, {webpage}"
    )

    tags = [
        "THT",
        classname_description,
        "vertical",
        f"pitch {rm:.3g}mm",
        f"size {package_size[0]:.3g}x{package_size[1]:.3g}mm",
        f"drill {ddrill:.3g}mm",
        f"pad {max(pad):.3g}mm",
    ]

    if len(tags_additional) > 0:
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags.append(t)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(description)
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = [0, 0]
    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[l_fab + w_fab / 2, t_slk - txt_offset],
            layer="F.SilkS",
        )
    )
    if type(fabref_offset) in (tuple, list):
        kicad_modg.append(
            Text(
                text="${REFERENCE}",
                at=[
                    l_fab + w_fab / 2 + fabref_offset[0],
                    t_fab + h_fab / 2 + fabref_offset[1],
                ],
                layer="F.Fab",
                size=text_size,
                thickness=text_t,
            )
        )
    else:
        kicad_modg.append(
            Text(
                text="${REFERENCE}",
                at=[l_fab + w_fab / 2, t_slk - txt_offset],
                layer="F.Fab",
                size=text_size,
                thickness=text_t,
            )
        )
    kicad_modg.append(
        Property(
            name=Property.VALUE,
            text=footprint_name,
            at=[l_fab + w_fab / 2, t_slk + h_slk + txt_offset],
            layer="F.Fab",
        )
    )

    # create pads
    p1 = int(1)
    x1 = 0
    y1 = 0

    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_ROUNDRECT
    pad_shapeother = Pad.SHAPE_CIRCLE
    if pad[0] != pad[1]:
        pad_shapeother = Pad.SHAPE_OVAL

    extradrill1_type = Pad.TYPE_NPTH
    if (
        secondDrillPad[0] > secondDrillDiameter
        or secondDrillPad[1] > secondDrillDiameter
    ):
        extradrill1_type = Pad.TYPE_THT

    if secondDrillDiameter > 0:
        if secondDrillPad[0] < secondDrillDiameter:
            secondDrillPad[0] = secondDrillDiameter
        if secondDrillPad[1] < secondDrillDiameter:
            secondDrillPad[1] = secondDrillDiameter

    pad_shape_extra = Pad.SHAPE_CIRCLE
    if secondDrillPad[0] != secondDrillPad[1]:
        pad_shape_extra = Pad.SHAPE_OVAL

    pad_layers = Pad.LAYERS_THT
    keepouts: list[GeomShapeClosed]=[]

    # Used to track the keepouts for pin 1 to move the arrow if needed
    pin1_keepouts: list[GeomShapeClosed] = []

    for p in range(1, pins + 1):

        if p == 1:
            kicad_modg.append(
                Pad(
                    number=p,
                    type=pad_type,
                    shape=pad_shape1,
                    at=[x1, y1],
                    size=pad,
                    drill=ddrill,
                    layers=pad_layers,
                    round_radius_handler=global_config.roundrect_radius_handler,
                )
            )
            pin1_keepouts += DT.addKeepoutRect(
                x1, y1, pad[0] + 8 * slk_offset, pad[1] + 8 * slk_offset
            )

            if secondDrillDiameter > 0:
                if extradrill1_type == Pad.TYPE_NPTH:
                    num = ""
                    extra_shape = pad_shape_extra
                else:
                    num = str(p)
                    extra_shape = Pad.SHAPE_RECT
                kicad_modg.append(
                    Pad(
                        number=num,
                        type=extradrill1_type,
                        shape=extra_shape,
                        at=[x1 + secondDrillOffset[0], y1 + secondDrillOffset[1]],
                        size=secondDrillPad,
                        drill=secondDrillDiameter,
                        layers=pad_layers,
                    )
                )
                pin1_keepouts += DT.addKeepoutRect(
                    x1 + secondDrillOffset[0],
                    y1 + secondDrillOffset[1],
                    max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                    max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                )

            keepouts += pin1_keepouts
        else:
            kicad_modg.append(
                Pad(
                    number=p,
                    type=pad_type,
                    shape=pad_shapeother,
                    at=[x1, y1],
                    size=pad,
                    drill=ddrill,
                    layers=pad_layers,
                )
            )
            if pad[0] != pad[1]:
                keepouts = keepouts +  DT.addKeepoutRect(
                    x1, y1, pad[0] + 8 * slk_offset, pad[1] + 8 * slk_offset
                )
            else:
                keepouts = keepouts +  DT.addKeepoutRound(
                    x1, y1, pad[0] + 8 * slk_offset, pad[0] + 8 * slk_offset
                )
            if secondDrillDiameter > 0:
                if extradrill1_type == Pad.TYPE_NPTH:
                    num = ""
                else:
                    num = str(p)
                kicad_modg.append(
                    Pad(
                        number=num,
                        type=extradrill1_type,
                        shape=pad_shape_extra,
                        at=[x1 + secondDrillOffset[0], y1 + secondDrillOffset[1]],
                        size=secondDrillPad,
                        drill=secondDrillDiameter,
                        layers=pad_layers,
                    )
                )
                if secondDrillPad[0] != secondDrillPad[1]:
                    keepouts = keepouts +  DT.addKeepoutRect(
                        x1 + secondDrillOffset[0],
                        y1 + secondDrillOffset[1],
                        max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                        max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                    )
                else:
                    keepouts = keepouts +  DT.addKeepoutRound(
                        x1 + secondDrillOffset[0],
                        y1 + secondDrillOffset[1],
                        max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                        max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                    )

        x1 = x1 + rm

    # create Body
    if len(bevel_height) > 0:
        chamfer = min(h_fab / 4, 2, bevel_height[0])
    else:
        chamfer = min(h_fab / 4, 2)
    DT.bevelRectBL(
        kicad_modg, [l_fab, t_fab], [w_fab, h_fab], "F.Fab", lw_fab, bevel_size=chamfer
    )
    for bh in bevel_height:
        kicad_modg.append(
            Line(
                start=[l_fab, t_fab + h_fab - bh],
                end=[l_fab + w_fab, t_fab + h_fab - bh],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        DT.addHLineWithKeepout(
            kicad_modg,
            l_slk,
            l_slk + w_slk,
            t_fab + h_fab - bh,
            layer="F.SilkS",
            width=lw_slk,
            keepouts=keepouts,
        )

    kicad_modg += make_silk_outline_with_pin1_arrow(
        GeomRectangle(start=Vector2D(l_slk, t_slk), size=Vector2D(w_slk, h_slk)),
        0,
        lw_slk,
        keepouts,
        pin1_keepouts,
        Direction.NORTH,
    )

    # opening + other repeated features
    for p in range(1, pins + 1):
        DT.addRectWithKeepout(
            kicad_modg,
            (p - 1) * rm - opening[0] / 2 - opening_xoffset,
            t_fab + h_fab - opening_yoffset - opening[1],
            opening[0],
            opening[1],
            "F.SilkS",
            lw_slk,
            keepouts,
        )
        DT.addRectWith(
            kicad_modg,
            (p - 1) * rm - opening[0] / 2 - opening_xoffset,
            t_fab + h_fab - opening_yoffset - opening[1],
            opening[0],
            opening[1],
            "F.Fab",
            lw_fab,
        )

        if (
            not (type(secondHoleDiameter) in (tuple, list))
            and secondHoleDiameter > 0
            and (p - 1) * rm + secondHoleOffset[0] < l_fab + w_fab
        ):
            kicad_modg.append(
                Circle(
                    center=[
                        (p - 1) * rm + secondHoleOffset[0],
                        0 + secondHoleOffset[1],
                    ],
                    radius=secondHoleDiameter / 2,
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addCircleWithKeepout(
                kicad_modg,
                (p - 1) * rm + secondHoleOffset[0],
                0 + secondHoleOffset[1],
                secondHoleDiameter / 2,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (
            not (type(thirdHoleDiameter) in (tuple, list))
            and thirdHoleDiameter > 0
            and (p - 1) * rm + thirdHoleOffset[0] < l_fab + w_fab
        ):
            kicad_modg.append(
                Circle(
                    center=[(p - 1) * rm + thirdHoleOffset[0], 0 + thirdHoleOffset[1]],
                    radius=thirdHoleDiameter / 2,
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addCircleWithKeepout(
                kicad_modg,
                (p - 1) * rm + thirdHoleOffset[0],
                0 + thirdHoleOffset[1],
                thirdHoleDiameter / 2,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (
            not (type(fourthHoleDiameter) in (tuple, list))
            and fourthHoleDiameter > 0
            and (p - 1) * rm + fourthHoleOffset[0] < l_fab + w_fab
        ):
            kicad_modg.append(
                Circle(
                    center=[
                        (p - 1) * rm + fourthHoleOffset[0],
                        0 + fourthHoleOffset[1],
                    ],
                    radius=fourthHoleDiameter / 2,
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addCircleWithKeepout(
                kicad_modg,
                (p - 1) * rm + fourthHoleOffset[0],
                0 + fourthHoleOffset[1],
                fourthHoleDiameter / 2,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (type(secondHoleDiameter) in (tuple, list)) and (
            p - 1
        ) * rm + secondHoleOffset[0] < l_fab + w_fab:
            kicad_modg.append(
                Rectangle(
                    start=[
                        (p - 1) * rm + secondHoleOffset[0] - secondHoleDiameter[0] / 2,
                        0 + secondHoleOffset[1] - secondHoleDiameter[1] / 2,
                    ],
                    end=[
                        (p - 1) * rm + secondHoleOffset[0] + secondHoleDiameter[0] / 2,
                        0 + secondHoleOffset[1] + secondHoleDiameter[1] / 2,
                    ],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addRectWithKeepout(
                kicad_modg,
                (p - 1) * rm + secondHoleOffset[0] - secondHoleDiameter[0] / 2,
                0 + secondHoleOffset[1] - secondHoleDiameter[1] / 2,
                secondHoleDiameter[0],
                secondHoleDiameter[1],
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (type(thirdHoleDiameter) in (tuple, list)) and (
            p - 1
        ) * rm + thirdHoleOffset[0] < l_fab + w_fab:
            kicad_modg.append(
                Rectangle(
                    start=[
                        (p - 1) * rm + thirdHoleOffset[0] - thirdHoleDiameter[0] / 2,
                        0 + thirdHoleOffset[1] - thirdHoleDiameter[1] / 2,
                    ],
                    end=[
                        (p - 1) * rm + thirdHoleOffset[0] + thirdHoleDiameter[0] / 2,
                        0 + thirdHoleOffset[1] + thirdHoleDiameter[1] / 2,
                    ],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addRectWithKeepout(
                kicad_modg,
                (p - 1) * rm + thirdHoleOffset[0] - thirdHoleDiameter[0] / 2,
                0 + thirdHoleOffset[1] - thirdHoleDiameter[1] / 2,
                thirdHoleDiameter[0],
                thirdHoleDiameter[1],
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (type(fourthHoleDiameter) in (tuple, list)) and (
            p - 1
        ) * rm + fourthHoleOffset[0] < l_fab + w_fab:
            kicad_modg.append(
                Rectangle(
                    start=[
                        (p - 1) * rm + fourthHoleOffset[0] - fourthHoleDiameter[0] / 2,
                        0 + fourthHoleOffset[1] - fourthHoleDiameter[1] / 2,
                    ],
                    end=[
                        (p - 1) * rm + fourthHoleOffset[0] + fourthHoleDiameter[0] / 2,
                        0 + fourthHoleOffset[1] + fourthHoleDiameter[1] / 2,
                    ],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addRectWithKeepout(
                kicad_modg,
                (p - 1) * rm + fourthHoleOffset[0] - fourthHoleDiameter[0] / 2,
                0 + fourthHoleOffset[1] - fourthHoleDiameter[1] / 2,
                fourthHoleDiameter[0],
                fourthHoleDiameter[1],
                "F.SilkS",
                lw_slk,
                keepouts,
            )

    # nibble
    if nibbleSize is not None:
        assert nibblePos is not None
        kicad_modg.append(
            Rectangle(
                start=[l_fab + nibblePos[0], t_fab + nibblePos[1]],
                end=[
                    l_fab + nibblePos[0] + nibbleSize[0],
                    t_fab + nibblePos[1] + nibbleSize[1],
                ],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        DT.addRectWithKeepout(
            kicad_modg,
            l_fab + nibblePos[0] - slk_offset,
            t_fab + nibblePos[1] - slk_offset,
            nibbleSize[0],
            nibbleSize[1] + 2 * slk_offset,
            "F.SilkS",
            lw_slk,
            keepouts,
        )

    # create courtyard
    kicad_mod.append(
        Rectangle(
            start=[DT.roundCrt(l_crt + offset[0]), DT.roundCrt(t_crt + offset[1])],
            end=[
                DT.roundCrt(l_crt + offset[0] + w_crt),
                DT.roundCrt(t_crt + offset[1] + h_crt),
            ],
            layer="F.CrtYd",
            width=lw_crt,
        )
    )

    # None means the caller will deal with this
    if lib_name is not None:
        model_filename = global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix
        kicad_modg.append(
            Model(
                filename=model_filename,
                at=[0, 0, 0],
                scale=[1, 1, 1],
                rotate=[0, 0, 0],
            )
        )

        write_footprint(kicad_mod, lib_name, generator_name)

    return kicad_mod


#    <-----> vsegment_lines_offset
#  +-+------------+-----------+-------------+                      ^
#  | |     H      |    H      |    H        | ^                    |
#  | |----------- |           |             | |                    |                                       ^
#  | ||   OOO   | |   OOO     |   OOO       | |secondHoleOffset    | package_height                        |
#  | ||  OOOOO  | |  OOOOO    |  OOOOO      | v                    |                  ^                    | opening[1]
#  | ||   OOO   | |   OOO     |   OOO       |                      |                  |                    |
#  +-+------------+-----------+-------------+ ^                    |                  | leftbottom_offset  x
#  | |            |           |             | | bevel_height       |                  |                    | opening_yoffset
#  +-+------------+-----------+-------------+ v                    v                  v                    v
#          <--- rm ---->
#  <------>leftbottom_offset[0]     <------->leftbottom_offset[2] (or leftbottom_offset[0]  if len(leftbottom_offset)==2)
#     <---------> opening[0]
#
#
def makeTerminalBlock45Degree(
    generator_name,
    footprint_name,
    pins,
    rm,
    package_height,
    leftbottom_offset,
    ddrill,
    pad,
    opening,
    opening_xoffset,
    opening_yoffset,
    opening_elliptic=False,
    even_pin_offset=0, # Y-axis offset for even pins, relative to pin 1
    bevel_height=[],
    vsegment_lines_offset=[],
    secondHoleDiameter=0,
    secondHoleOffset=[0, 0],
    thirdHoleDiameter=0,
    thirdHoleOffset=[0, 0],
    fourthHoleDiameter=0,
    fourthHoleOffset=[0, 0],
    fifthHoleDiameter=0,
    fifthHoleOffset=[0, 0],
    secondDrillDiameter=0,
    secondDrillOffset=[0, 0],
    secondDrillPad=[0, 0],
    nibbleSize: Optional[Vector2D] = None,
    nibblePos: Optional[Vector2D] = None,
    fabref_offset=[0, 0],
    secondEllipseSize=[0, 0],
    secondEllipseOffset=[0, 0],
    stackable=False,
    tags_additional=[],
    lib_name: Optional[str] = "Connectors_Terminal_Blocks",
    classname="Connectors_Terminal_Blocks",
    classname_description="terminal block",
    webpage="",
):
    global_config = GC.GLOBAL_CONFIG

    package_size = Vector2D.from_floats(2 * leftbottom_offset[0] + (pins - 1) * rm, package_height)
    if len(leftbottom_offset) == 3:
        package_size = Vector2D.from_floats(
            leftbottom_offset[0] + leftbottom_offset[2] + (pins - 1) * rm,
            package_height,
        )

    h_fab = package_size[1]
    w_fab = package_size[0]
    l_fab = -leftbottom_offset[0]
    t_fab = -(h_fab - leftbottom_offset[1])

    h_slk = h_fab + 2 * slk_offset
    w_slk = w_fab + 2 * slk_offset
    l_slk = l_fab - slk_offset
    t_slk = t_fab - slk_offset

    h_crt = h_fab + 2 * crt_offset
    w_crt = w_fab + (0 if stackable else 2 * crt_offset)
    l_crt = l_fab - (0 if stackable else crt_offset)
    t_crt = t_fab - crt_offset

    text_size = w_fab * 0.6
    fab_text_size_max = 1.0
    if text_size < fab_text_size_min:
        text_size = fab_text_size_min
    elif text_size > fab_text_size_max:
        text_size = fab_text_size_max
    text_size = round(text_size, 2)
    text_size = [text_size, text_size]
    text_t = text_size[0] * 0.15

    description = (
        f"{classname_description}, 45Degree (cable under 45degree), {pins:d} pins, pitch {rm:.3g}mm, "
        f"size {package_size[0]:.3g}x{package_size[1]:.3g}mm, drill diameter {ddrill:.3g}mm, "
        f"pad diameter {max(pad):.3g}mm, {webpage}"
    )

    tags = [
        "THT",
        classname_description,
        "45Degree",
        f"pitch {rm:.3g}mm",
        f"size {package_size[0]:.3g}x{package_size[1]:.3g}mm",
        f"drill {ddrill:.3g}mm",
        f"pad {max(pad):.3g}mm",
    ]

    if len(tags_additional) > 0:
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags.append(t)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(description)
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = [0, 0]
    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[l_fab + w_fab / 2, t_slk - txt_offset],
            layer="F.SilkS",
        )
    )
    if type(fabref_offset) in (tuple, list):
        kicad_modg.append(
            Text(
                text="${REFERENCE}",
                at=[
                    l_fab + w_fab / 2 + fabref_offset[0],
                    t_fab + h_fab / 2 + fabref_offset[1],
                ],
                layer="F.Fab",
                size=text_size,
                thickness=text_t,
            )
        )
    else:
        kicad_modg.append(
            Text(
                text="${REFERENCE}",
                at=[l_fab + w_fab / 2, t_slk - txt_offset],
                layer="F.Fab",
                size=text_size,
                thickness=text_t,
            )
        )
    kicad_modg.append(
        Property(
            name=Property.VALUE,
            text=footprint_name,
            at=[l_fab + w_fab / 2, t_slk + h_slk + txt_offset],
            layer="F.Fab",
        )
    )

    # create pads
    p1 = int(1)
    x1 = 0
    y1 = 0

    pad_type = Pad.TYPE_THT
    pad_shape1 = Pad.SHAPE_ROUNDRECT
    pad_shapeother = Pad.SHAPE_CIRCLE
    if pad[0] != pad[1]:
        pad_shapeother = Pad.SHAPE_OVAL

    extradrill1_type = Pad.TYPE_NPTH
    if (
        secondDrillPad[0] > secondDrillDiameter
        or secondDrillPad[1] > secondDrillDiameter
    ):
        extradrill1_type = Pad.TYPE_THT

    if secondDrillDiameter > 0:
        if secondDrillPad[0] < secondDrillDiameter:
            secondDrillPad[0] = secondDrillDiameter
        if secondDrillPad[1] < secondDrillDiameter:
            secondDrillPad[1] = secondDrillDiameter

    pad_shape_extra = Pad.SHAPE_CIRCLE
    if secondDrillPad[0] != secondDrillPad[1]:
        pad_shape_extra = Pad.SHAPE_OVAL

    pad_layers = Pad.LAYERS_THT
    keepouts: list[GeomShapeClosed] = []
    pin1_keepouts: list[GeomShapeClosed] = []

    for p in range(1, pins + 1):
        pextra = 0
        if secondDrillPad[0] > 0:
            pextra = p
        if p % 2 == 0:
            y1 = even_pin_offset
        else:
            y1 = 0
        if p == 1:
            kicad_modg.append(
                Pad(
                    number=p,
                    type=pad_type,
                    shape=pad_shape1,
                    at=[x1, y1],
                    size=pad,
                    drill=ddrill,
                    layers=pad_layers,
                    round_radius_handler=global_config.roundrect_radius_handler,
                )
            )
            pin1_keepouts += DT.addKeepoutRect(
                x1, y1, pad[0] + 8 * slk_offset, pad[1] + 8 * slk_offset
            )
            if secondDrillDiameter > 0:
                if extradrill1_type == Pad.TYPE_NPTH:
                    num = ""
                    extra_shape = pad_shape_extra
                else:
                    num = str(p)
                    extra_shape = Pad.SHAPE_RECT
                kicad_modg.append(
                    Pad(
                        number=num,
                        type=extradrill1_type,
                        shape=extra_shape,
                        at=[x1 + secondDrillOffset[0], y1 + secondDrillOffset[1]],
                        size=secondDrillPad,
                        drill=secondDrillDiameter,
                        layers=pad_layers,
                    )
                )
                pin1_keepouts += DT.addKeepoutRect(
                    x1 + secondDrillOffset[0],
                    y1 + secondDrillOffset[1],
                    max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                    max(secondDrillPad[1], secondDrillDiameter) + 8 * slk_offset,
                )

            keepouts += pin1_keepouts
        else:
            kicad_modg.append(
                Pad(
                    number=p,
                    type=pad_type,
                    shape=pad_shapeother,
                    at=[x1, y1],
                    size=pad,
                    drill=ddrill,
                    layers=pad_layers,
                )
            )
            if pad[0] != pad[1]:
                keepouts = keepouts +  DT.addKeepoutRect(
                    x1, y1, pad[0] + 8 * slk_offset, pad[1] + 8 * slk_offset
                )
            else:
                keepouts = keepouts +  DT.addKeepoutRound(
                    x1, y1, pad[0] + 8 * slk_offset, pad[0] + 8 * slk_offset
                )
            if secondDrillDiameter > 0:
                if extradrill1_type == Pad.TYPE_NPTH:
                    num = ""
                else:
                    num = str(p)
                kicad_modg.append(
                    Pad(
                        number=num,
                        type=extradrill1_type,
                        shape=pad_shape_extra,
                        at=[x1 + secondDrillOffset[0], y1 + secondDrillOffset[1]],
                        size=secondDrillPad,
                        drill=secondDrillDiameter,
                        layers=pad_layers,
                    )
                )
                keepouts = keepouts +  DT.addKeepoutRect(
                    x1 + secondDrillOffset[0],
                    y1 + secondDrillOffset[1],
                    max(secondDrillPad[0], secondDrillDiameter) + 8 * slk_offset,
                    max(secondDrillPad[1], secondDrillDiameter) + 8 * slk_offset,
                )

        x1 = x1 + rm

    # create Body
    if len(bevel_height) > 0:
        chamfer = min(h_fab / 4, 2, bevel_height[0])
    else:
        chamfer = min(h_fab / 4, 2)
    DT.bevelRectBL(
        kicad_modg, [l_fab, t_fab], [w_fab, h_fab], "F.Fab", lw_fab, bevel_size=chamfer
    )
    for bh in bevel_height:
        kicad_modg.append(
            Line(
                start=[l_fab, t_fab + h_fab - bh],
                end=[l_fab + w_fab, t_fab + h_fab - bh],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        DT.addHLineWithKeepout(
            kicad_modg,
            l_slk,
            l_slk + w_slk,
            t_fab + h_fab - bh,
            layer="F.SilkS",
            width=lw_slk,
            keepouts=keepouts,
        )

    kicad_modg += make_silk_outline_with_pin1_arrow(
        GeomRectangle(start=Vector2D(l_slk, t_slk), size=Vector2D(w_slk, h_slk)),
        0,
        lw_slk,
        keepouts,
        pin1_keepouts,
        Direction.NORTH,
    )

    # opening + other repeated features
    for p in range(1, pins + 1):
        if opening[0] > 0 and opening[1] > 0:
            if opening_elliptic:
                DT.addEllipse(
                    kicad_modg,
                    (p - 1) * rm + opening_xoffset,
                    t_fab + h_fab - opening_yoffset,
                    opening[0],
                    opening[1],
                    layer="F.Fab",
                    width=lw_fab,
                )
                DT.addEllipseWithKeepout(
                    kicad_modg,
                    (p - 1) * rm + opening_xoffset,
                    t_fab + h_fab - opening_yoffset,
                    opening[0],
                    opening[1],
                    layer="F.SilkS",
                    width=lw_slk,
                    keepouts=keepouts,
                )
            else:
                DT.addRectWithKeepout(
                    kicad_modg,
                    (p - 1) * rm - opening[0] / 2 + opening_xoffset,
                    t_fab + h_fab - opening_yoffset - opening[1],
                    opening[0],
                    opening[1],
                    "F.SilkS",
                    lw_slk,
                    keepouts,
                )
                DT.addRectWith(
                    kicad_modg,
                    (p - 1) * rm - opening[0] / 2 + opening_xoffset,
                    t_fab + h_fab - opening_yoffset - opening[1],
                    opening[0],
                    opening[1],
                    "F.Fab",
                    lw_fab,
                )

        # vertical segment separation lines
        for seg_offset in vsegment_lines_offset:
            if seg_offset >= l_fab and seg_offset <= l_fab + w_fab:
                DT.addVLineWithKeepout(
                    kicad_modg,
                    x=(p - 1) * rm + seg_offset,
                    y0=t_fab,
                    y1=t_fab + h_fab,
                    layer="F.Fab",
                    width=lw_fab,
                    keepouts=[],
                )
                DT.addVLineWithKeepout(
                    kicad_modg,
                    x=(p - 1) * rm + seg_offset,
                    y0=t_slk,
                    y1=t_slk + h_slk,
                    layer="F.SilkS",
                    width=lw_slk,
                    keepouts=keepouts,
                )

        if (
            not (type(secondHoleDiameter) in (tuple, list))
            and secondHoleDiameter > 0
            and (p - 1) * rm + secondHoleOffset[0] < l_fab + w_fab
        ):
            kicad_modg.append(
                Circle(
                    center=[
                        (p - 1) * rm + secondHoleOffset[0],
                        0 + secondHoleOffset[1],
                    ],
                    radius=secondHoleDiameter / 2,
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addCircleWithKeepout(
                kicad_modg,
                (p - 1) * rm + secondHoleOffset[0],
                0 + secondHoleOffset[1],
                secondHoleDiameter / 2,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (
            not (type(thirdHoleDiameter) in (tuple, list))
            and thirdHoleDiameter > 0
            and (p - 1) * rm + thirdHoleOffset[0] < l_fab + w_fab
        ):
            kicad_modg.append(
                Circle(
                    center=[(p - 1) * rm + thirdHoleOffset[0], 0 + thirdHoleOffset[1]],
                    radius=thirdHoleDiameter / 2,
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addCircleWithKeepout(
                kicad_modg,
                (p - 1) * rm + thirdHoleOffset[0],
                0 + thirdHoleOffset[1],
                thirdHoleDiameter / 2,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (
            not (type(fourthHoleDiameter) in (tuple, list))
            and fourthHoleDiameter > 0
            and (p - 1) * rm + fourthHoleOffset[0] < l_fab + w_fab
        ):
            kicad_modg.append(
                Circle(
                    center=[
                        (p - 1) * rm + fourthHoleOffset[0],
                        0 + fourthHoleOffset[1],
                    ],
                    radius=fourthHoleDiameter / 2,
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addCircleWithKeepout(
                kicad_modg,
                (p - 1) * rm + fourthHoleOffset[0],
                0 + fourthHoleOffset[1],
                fourthHoleDiameter / 2,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (
            not (type(fifthHoleDiameter) in (tuple, list))
            and fifthHoleDiameter > 0
            and (p - 1) * rm + fifthHoleOffset[0] < l_fab + w_fab
        ):
            kicad_modg.append(
                Circle(
                    center=[(p - 1) * rm + fifthHoleOffset[0], 0 + fifthHoleOffset[1]],
                    radius=fifthHoleDiameter / 2,
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addCircleWithKeepout(
                kicad_modg,
                (p - 1) * rm + fifthHoleOffset[0],
                0 + fifthHoleOffset[1],
                fifthHoleDiameter / 2,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (type(secondHoleDiameter) in (tuple, list)) and (
            p - 1
        ) * rm + secondHoleOffset[0] < l_fab + w_fab:
            kicad_modg.append(
                Rectangle(
                    start=[
                        (p - 1) * rm + secondHoleOffset[0] - secondHoleDiameter[0] / 2,
                        0 + secondHoleOffset[1] - secondHoleDiameter[1] / 2,
                    ],
                    end=[
                        (p - 1) * rm + secondHoleOffset[0] + secondHoleDiameter[0] / 2,
                        0 + secondHoleOffset[1] + secondHoleDiameter[1] / 2,
                    ],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addRectWithKeepout(
                kicad_modg,
                (p - 1) * rm + secondHoleOffset[0] - secondHoleDiameter[0] / 2,
                0 + secondHoleOffset[1] - secondHoleDiameter[1] / 2,
                secondHoleDiameter[0],
                secondHoleDiameter[1],
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (type(thirdHoleDiameter) in (tuple, list)) and (
            p - 1
        ) * rm + thirdHoleOffset[0] < l_fab + w_fab:
            kicad_modg.append(
                Rectangle(
                    start=[
                        (p - 1) * rm + thirdHoleOffset[0] - thirdHoleDiameter[0] / 2,
                        0 + thirdHoleOffset[1] - thirdHoleDiameter[1] / 2,
                    ],
                    end=[
                        (p - 1) * rm + thirdHoleOffset[0] + thirdHoleDiameter[0] / 2,
                        0 + thirdHoleOffset[1] + thirdHoleDiameter[1] / 2,
                    ],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addRectWithKeepout(
                kicad_modg,
                (p - 1) * rm + thirdHoleOffset[0] - thirdHoleDiameter[0] / 2,
                0 + thirdHoleOffset[1] - thirdHoleDiameter[1] / 2,
                thirdHoleDiameter[0],
                thirdHoleDiameter[1],
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (type(fourthHoleDiameter) in (tuple, list)) and (
            p - 1
        ) * rm + fourthHoleOffset[0] < l_fab + w_fab:
            kicad_modg.append(
                Rectangle(
                    start=[
                        (p - 1) * rm + fourthHoleOffset[0] - fourthHoleDiameter[0] / 2,
                        0 + fourthHoleOffset[1] - fourthHoleDiameter[1] / 2,
                    ],
                    end=[
                        (p - 1) * rm + fourthHoleOffset[0] + fourthHoleDiameter[0] / 2,
                        0 + fourthHoleOffset[1] + fourthHoleDiameter[1] / 2,
                    ],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addRectWithKeepout(
                kicad_modg,
                (p - 1) * rm + fourthHoleOffset[0] - fourthHoleDiameter[0] / 2,
                0 + fourthHoleOffset[1] - fourthHoleDiameter[1] / 2,
                fourthHoleDiameter[0],
                fourthHoleDiameter[1],
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if (type(fifthHoleDiameter) in (tuple, list)) and (
            p - 1
        ) * rm + fifthHoleOffset[0] < l_fab + w_fab:
            kicad_modg.append(
                Rectangle(
                    start=[
                        (p - 1) * rm + fifthHoleOffset[0] - fifthHoleDiameter[0] / 2,
                        0 + fifthHoleOffset[1] - fifthHoleDiameter[1] / 2,
                    ],
                    end=[
                        (p - 1) * rm + fifthHoleOffset[0] + fifthHoleDiameter[0] / 2,
                        0 + fifthHoleOffset[1] + fifthHoleDiameter[1] / 2,
                    ],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            DT.addRectWithKeepout(
                kicad_modg,
                (p - 1) * rm + fifthHoleOffset[0] - fifthHoleDiameter[0] / 2,
                0 + fifthHoleOffset[1] - fifthHoleDiameter[1] / 2,
                fifthHoleDiameter[0],
                fifthHoleDiameter[1],
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        if secondEllipseSize[0] > 0 and secondEllipseSize[1] > 0:
            DT.addEllipse(
                kicad_modg,
                (p - 1) * rm + secondEllipseOffset[0],
                0 + secondEllipseOffset[1],
                secondEllipseSize[0],
                secondEllipseSize[1],
                layer="F.Fab",
                width=lw_fab,
            )
            DT.addEllipseWithKeepout(
                kicad_modg,
                (p - 1) * rm + secondEllipseOffset[0],
                0 + secondEllipseOffset[1],
                secondEllipseSize[0],
                secondEllipseSize[1],
                layer="F.SilkS",
                width=lw_slk,
                keepouts=keepouts,
            )

    # nibble
    if nibbleSize is not None:
        assert nibblePos is not None
        kicad_modg.append(
            Rectangle(
                start=[l_fab + nibblePos[0], t_fab + nibblePos[1]],
                end=[
                    l_fab + nibblePos[0] + nibbleSize[0],
                    t_fab + nibblePos[1] + nibbleSize[1],
                ],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        DT.addRectWithKeepout(
            kicad_modg,
            l_fab + nibblePos[0] - slk_offset,
            t_fab + nibblePos[1] - slk_offset,
            nibbleSize[0],
            nibbleSize[1] + 2 * slk_offset,
            "F.SilkS",
            lw_slk,
            keepouts,
        )

    # create courtyard
    kicad_mod.append(
        Rectangle(
            start=[DT.roundCrt(l_crt + offset[0]), DT.roundCrt(t_crt + offset[1])],
            end=[
                DT.roundCrt(l_crt + offset[0] + w_crt),
                DT.roundCrt(t_crt + offset[1] + h_crt),
            ],
            layer="F.CrtYd",
            width=lw_crt,
        )
    )

    if lib_name is not None:
        model_filename = global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix

        kicad_modg.append(
            Model(
                filename=model_filename,
                at=[0, 0, 0],
                scale=[1, 1, 1],
                rotate=[0, 0, 0],
            )
        )

        write_footprint(kicad_mod, lib_name, generator_name)

    return kicad_mod


# pins [[x,y], [x,y], ...] location of pins (relative to center of block)
# ddrill: drill diameter for pins
# pad [padx,pady]:  size of pin-pad
# screw_diameter: diameter of screw
# screw_offset: offset of screw from package center
# slit_screw=true|False: type of screw
# block_size [w,h]: size of block
def makeScrewTerminalSingleStd(
    generator_name,
    footprint_name,
    block_size,
    block_offset,
    pins,
    ddrill,
    pad,
    screw_diameter,
    screw_offset,
    slit_screw=True,
    tags_additional=[],
    lib_name: Optional[str] = "Connectors_Terminal_Blocks",
    classname="Connectors_Terminal_Blocks",
    classname_description="single screw terminal terminal block",
    webpage="",
):
    global_config = GC.GLOBAL_CONFIG

    h_fab = block_size[1]
    w_fab = block_size[0]
    l_fab = -block_size[0] / 2 + block_offset[0]
    t_fab = -block_size[1] / 2 + block_offset[1]

    h_slk = h_fab + 2 * slk_offset
    w_slk = w_fab + 2 * slk_offset
    l_slk = l_fab - slk_offset
    t_slk = t_fab - slk_offset

    h_crt = h_fab + 2 * crt_offset
    w_crt = w_fab + 2 * crt_offset
    l_crt = l_fab - crt_offset
    t_crt = t_fab - crt_offset

    text_size = w_fab * 0.6
    fab_text_size_max = 1.0
    if text_size < fab_text_size_min:
        text_size = fab_text_size_min
    elif text_size > fab_text_size_max:
        text_size = fab_text_size_max
    text_size = round(text_size, 2)
    text_size = [text_size, text_size]
    text_t = text_size[0] * 0.15
    txt_offset = text_size[1]

    description = (
        f"{classname_description}, block "
        f"size {block_size[0]:.3g}x{block_size[1]:.3g}mm, "
        f"drill diameter {ddrill:.3g}mm, pad diameter {max(pad):.3g}mm, "
        f"{webpage}"
    )

    tags = [
        "THT",
        classname_description,
        f"size {block_size[0]:.3g}x{block_size[1]:.3g}mm",
        f"drill {ddrill:.3g}mm",
        f"pad {max(pad):.3g}mm",
    ]

    if len(tags_additional) > 0:
        for t in tags_additional:
            footprint_name = footprint_name + "_" + t
            description = description + ", " + t
            tags.append(t)

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(description)
    kicad_mod.tags = tags

    # anchor for SMD-symbols is in the center, for THT-sybols at pin1
    offset = pins[0]
    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[l_fab + w_fab / 2, t_slk - txt_offset],
            layer="F.SilkS",
        )
    )
    kicad_modg.append(
        Text(
            text="${REFERENCE}",
            at=[l_fab + w_fab / 2, t_slk - txt_offset],
            layer="F.Fab",
        )
    )
    kicad_modg.append(
        Property(
            name=Property.VALUE,
            text=footprint_name,
            at=[l_fab + w_fab / 2, t_slk + h_slk + txt_offset],
            layer="F.Fab",
        )
    )

    # create pads
    p1 = int(1)
    x1 = 0
    y1 = 0

    # pins/pads
    pad_type = Pad.TYPE_THT
    pad_shapeother = Pad.SHAPE_CIRCLE
    pad_layers = Pad.LAYERS_THT
    keepouts: list[GeomShapeClosed] = []

    for p in pins:
        kicad_modg.append(
            Pad(
                number=1,
                type=pad_type,
                shape=pad_shapeother,
                at=p,
                size=pad,
                drill=ddrill,
                layers=pad_layers,
            )
        )
        keepouts = keepouts +  DT.addKeepoutRound(
            p[0], p[1], pad[0] + 8 * slk_offset, pad[0] + 8 * slk_offset
        )

    # screw
    keepouts_screw: list[GeomShapeClosed] = []
    if screw_diameter > 0:
        keepouts_screw = keepouts_screw +  DT.addKeepoutRound(
            screw_offset[0], screw_offset[1], screw_diameter, screw_diameter
        )
        if slit_screw:
            DT.addSlitScrew(
                kicad_modg,
                screw_offset,
                screw_diameter / 2,
                "F.Fab",
                lw_fab,
            )
        else:
            DT.addCrossScrew(
                kicad_modg,
                screw_offset,
                screw_diameter / 2,
                "F.Fab",
                lw_fab,
            )

    # create Body
    DT.addRectWithKeepout(
        kicad_modg,
        l_fab,
        t_fab,
        w_fab,
        h_fab,
        layer="F.Fab",
        width=lw_fab,
        keepouts=keepouts_screw,
    )
    DT.addRectWithKeepout(
        kicad_modg,
        l_slk,
        t_slk,
        w_slk,
        h_slk,
        layer="F.SilkS",
        width=lw_slk,
        keepouts=keepouts + keepouts_screw,
    )

    # create courtyard
    kicad_mod.append(
        Rectangle(
            start=[DT.roundCrt(l_crt + offset[0]), DT.roundCrt(t_crt + offset[1])],
            end=[
                DT.roundCrt(l_crt + offset[0] + w_crt),
                DT.roundCrt(t_crt + offset[1] + h_crt),
            ],
            layer="F.CrtYd",
            width=lw_crt,
        )
    )

    if lib_name is not None:
        model_filename = global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix

        kicad_modg.append(
            Model(
                filename=model_filename,
                at=[0, 0, 0],
                scale=[1, 1, 1],
                rotate=[0, 0, 0],
            )
        )

        write_footprint(kicad_mod, lib_name, generator_name)

    return kicad_mod
