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

import math

from KicadModTree import *  # NOQA
from KicadModTree.nodes import Point
from generators.tools.footprint.drawing_tools import *
from generators.tools.footprint.footprint_global_properties import *
from kilibs.config import global_config as GC
from generators.tools.footprint.save_footprint import write_footprint


global_config = GC.GLOBAL_CONFIG


# LED footprints
#   style options:
#     1. led_type="box"
#           +----------------+ ^
#           |                | |
#           |  OO        OO  | h
#           |                | |
#           +----------------+ v
#             <---pitch--->
#           <-------w-------->
#     2. led_type="round"
#              /----------\   ^
#             |            \  |
#             |  OO    OO   | h
#             |            /  |
#              \__________/   v
#               <-pitch->
#           <-------w-------->
#     3. led_type="roundedbox"
#           +--------------\   ^
#           |               \  |
#           |  OO        OO  | h
#           |               /  |
#           +--------------/   v
#              <--pitch-->
#           <-------w-------->
#     4. led_type="oval"
#           +----------------+ ^
#           |                | |
#           |  OO        OO  | h
#           |                | |
#           +----------------+ v
#               <--pitch->
#           <-------w-------->
#     2. led_type="round_simple"
#              /----------\   ^
#             /            \  |
#            |   OO    OO   | h
#             \            /  |
#              \__________/   v
#               <-pitch->
#           <-------w-------->
# in the center a second circle is drawn if rin>0
def makeLEDRadial(
    generator_name,
    pitch,
    w,
    h,
    ddrill,
    win=0,
    diameter=0,
    pins=2,
    led_type="round",
    has3d=1,
    fpname_override="",
    desc_extras_start=None,
    desc_extras_end=None,
    tag_extras=None,
    base_filename="LED",
    lib_name="LED_THT",
    name_additions=None,
    height3d=8,
    height3d_bottom=1,
):
    if desc_extras_start is None:
        desc_extras_start = []
    if name_additions is None:
        name_additions = []
    if desc_extras_end is None:
        desc_extras_end = []
    if tag_extras is None:
        tag_extras = []

    padx = 2 * ddrill
    pady = padx
    if padx + min_pad_distance > pitch:
        padx = pitch - min_pad_distance
    txtoffset = txt_offset

    pad1style = Pad.SHAPE_RECT

    padpos = []
    offset = [0, 0]
    overpad_width = (pins - 1) * pitch
    xpad = -overpad_width / 2
    offset = [-xpad, 0]
    for p in range(1, pins + 1):
        padpos.append([p, xpad, 0, ddrill, padx, pady])
        xpad = xpad + pitch

    l_fab = -w / 2
    t_fab = -h / 2
    w_fab = w
    h_fab = h
    d_fab = max(w, h)
    d2_fab = diameter
    h_slk = h_fab + 2 * slk_offset
    w_slk = w_fab + 2 * slk_offset
    l_slk = l_fab - slk_offset
    t_slk = t_fab - slk_offset
    d_slk = d_fab + lw_slk + slk_offset
    w_crt = max(w_slk, overpad_width + padx) + 2 * crt_offset
    h_crt = max(h_slk, pady) + 2 * crt_offset
    l_crt = -w_crt / 2
    t_crt = -h_crt / 2

    snfp = ""
    sn = ""
    snt = ""

    size_filename = ""
    size_info = []
    if led_type == "round" or led_type == "round_simple":
        size_filename = "_D{0:0.1f}mm".format(diameter)
        size_info.append("diameter {0:0.1f}mm".format(diameter))
    else:
        if led_type == "oval":
            size_info.append("Oval")
        if led_type == "box":
            size_info.append("Rectangular")
        wsize = w
        if led_type == "box" and win > 0:
            wsize = win
        size_filename = size_filename + "_W{0:0.1f}mm_H{1:0.1f}mm".format(wsize, h)
        size_info.append("size {0:0.1f}x{1:0.1f}mm".format(wsize, h))
        if diameter > 0:
            size_filename = "_D{0:0.1f}mm".format(diameter) + size_filename
            size_info.append("diameter {0:0.1f}mm".format(diameter))

    pincount_filename = ""
    pincount_tag = "{0:d} pins".format(pins)
    if pins > 2:
        pincount_filename = "-{0:d}".format(pins)
        if led_type == "box":
            pincount_filename = pincount_filename + "Pins"

    footprint_name = base_filename + size_filename + pincount_filename

    description = ["LED"]
    tags = ["LED"]

    added_info = list(desc_extras_start) + size_info
    if len(pincount_tag) > 0:
        added_info.append(pincount_tag)

    for t in added_info:
        if len(t):
            description.append(t)
    if fpname_override != "":
        footprint_name = fpname_override

    for t in desc_extras_end:
        if len(t):
            description.append(t)
    description.append("generated by kicad-footprint-generator")

    for t in tag_extras:
        if len(t):
            tags.append(t)

    for n in name_additions:
        if len(n) > 0:
            footprint_name = footprint_name + "_" + n

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(", ".join(description))
    kicad_mod.setTags(" ".join(tags))

    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[0, t_slk - txtoffset],
            layer="F.SilkS",
        )
    )
    kicad_modg.append(
        Property(
            name=Property.VALUE,
            text=footprint_name,
            at=[0, t_slk + h_slk + txtoffset],
            layer="F.Fab",
        )
    )
    kicad_modg.append(
        Text(
            text="${REFERENCE}",
            at=[0, 0],
            layer="F.Fab",
            size=[0.8, 0.8],
            thickness=0.12,
        )
    )

    # create FAB-layer
    if led_type == "round":
        kicad_modg.append(
            Circle(center=[0, 0], radius=d2_fab / 2, layer="F.Fab", width=lw_fab)
        )
        xmark = d2_fab / 2
        ymark = math.sqrt(d_fab * d_fab / 4 - xmark * xmark)
        alpha = 360 - 2 * math.degrees(math.atan(ymark / xmark))
        kicad_modg.append(
            Arc(
                center=[0, 0],
                start=[-xmark, -ymark],
                angle=alpha,
                layer="F.Fab",
                width=lw_fab,
            )
        )
        kicad_modg.append(
            Line(
                start=[-xmark, -ymark], end=[-xmark, ymark], layer="F.Fab", width=lw_fab
            )
        )
    if led_type == "round_simple":
        kicad_modg.append(
            Circle(center=[0, 0], radius=d2_fab / 2, layer="F.Fab", width=lw_fab)
        )
        kicad_modg.append(
            Circle(center=[0, 0], radius=d_fab / 2, layer="F.Fab", width=lw_fab)
        )
    elif led_type == "box":
        kicad_modg.append(
            Rectangle(
                start=[l_fab, t_fab],
                end=[l_fab + w_fab, t_fab + h_fab],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        if d2_fab > 0:
            kicad_modg.append(
                Circle(center=[0, 0], radius=d2_fab / 2, layer="F.Fab", width=lw_fab)
            )
        if win > 0:
            kicad_modg.append(
                Rectangle(
                    start=[-win / 2, t_fab],
                    end=[win / 2, t_fab + h_fab],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
    elif led_type == "oval":
        r = w / 2
        ystart = 0
        xstart = math.sqrt(r * r - ystart * ystart)
        ycenter = h / 2 - r
        alpha = 180 - 2 * math.degrees(math.atan(math.fabs(ycenter) / xstart))
        kicad_modg.append(
            Arc(
                center=[0, -ycenter],
                start=[-xstart, ystart],
                angle=alpha,
                layer="F.Fab",
                width=lw_fab,
            )
        )
        kicad_modg.append(
            Arc(
                center=[0, ycenter],
                start=[-xstart, -ystart],
                angle=-alpha,
                layer="F.Fab",
                width=lw_fab,
            )
        )

    # build keepeout for SilkScreen
    keepouts = []
    for p in padpos:
        if p[0] == 1:
            keepouts = keepouts + addKeepoutRect(
                p[1],
                p[2],
                p[4] + 2 * lw_slk + 2 * slk_offset,
                p[5] + 2 * lw_slk + 2 * slk_offset,
            )
        else:
            keepouts = keepouts + addKeepoutRound(
                p[1],
                p[2],
                p[4] + 2 * lw_slk + 2 * slk_offset,
                p[5] + 2 * lw_slk + 2 * slk_offset,
            )

    # create SILKSCREEN-layer
    if led_type == "box":
        addRectWithKeepout(
            kicad_modg, l_slk, t_slk, w_slk, h_slk, "F.SilkS", lw_slk, keepouts
        )
        if pins == 3:
            addVLineWithKeepout(
                kicad_modg,
                -offset[0] + pitch / 2,
                t_slk,
                t_slk + h_slk,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
        else:
            addVLineWithKeepout(
                kicad_modg,
                l_slk + lw_slk,
                t_slk,
                t_slk + h_slk,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
            addVLineWithKeepout(
                kicad_modg,
                l_slk + 2 * lw_slk,
                t_slk,
                t_slk + h_slk,
                "F.SilkS",
                lw_slk,
                keepouts,
            )
    elif led_type == "round":
        xmark = d2_fab / 2 + slk_offset
        ymark = math.sqrt(d_slk * d_slk / 4 - xmark * xmark)
        ypad = pady / 2 + slk_offset + lw_slk
        xpad = math.sqrt(d_slk * d_slk / 4 - ypad * ypad)
        alphamark = math.degrees(math.atan(ymark / xmark))
        alphapad = math.degrees(math.atan(ypad / xpad))
        alpha = 180 - alphamark
        if containedInAnyKeepout(
            Vector2D(xmark, 0.1), keepouts
        ) or containedInAnyKeepout(Vector2D(d_fab / 2, 0.1), keepouts):
            alpha = alpha - alphapad
        kicad_modg.append(
            Arc(
                center=[0, 0],
                start=[-xmark, -ymark],
                angle=alpha,
                layer="F.SilkS",
                width=lw_slk,
            )
        )
        kicad_modg.append(
            Arc(
                center=[0, 0],
                start=[-xmark, ymark],
                angle=-alpha,
                layer="F.SilkS",
                width=lw_slk,
            )
        )
        addVLineWithKeepout(
            kicad_modg, -xmark, -ymark, ymark, "F.SilkS", lw_slk, keepouts
        )

        ypad = pady / 2 + slk_offset + lw_slk
        xpad = math.sqrt(d2_fab * d2_fab / 4 - ypad * ypad)
        alphapad = math.degrees(math.atan(ypad / xpad))

        alpha = 180
        if containedInAnyKeepout(
            Vector2D(d2_fab / 2, 0.1), keepouts
        ) or containedInAnyKeepout(Vector2D(-d2_fab / 2, 0.1), keepouts):
            alpha = alpha - 2 * alphapad
        if alpha == 180:
            kicad_modg.append(
                Circle(center=[0, 0], radius=d2_fab / 2, layer="F.SilkS", width=lw_slk)
            )
        else:
            kicad_modg.append(
                Arc(
                    center=[0, 0],
                    start=[-xpad, -ypad],
                    angle=alpha,
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            kicad_modg.append(
                Arc(
                    center=[0, 0],
                    start=[-xpad, ypad],
                    angle=-alpha,
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
    elif led_type == "round_simple":
        rs = [d2_fab, d_slk]
        xpads = []
        ypads = []
        fullCircle = False
        for r in rs:
            ypad = pady / 2 + slk_offset + lw_slk
            xpad = math.sqrt(r * r / 4 - ypad * ypad)
            xpads.append(xpad)
            ypads.append(ypad)
            alphapad = math.degrees(math.atan(ypad / xpad))

            alpha = 180
            if containedInAnyKeepout(
                Vector2D(r / 2, 0.1), keepouts
            ) or containedInAnyKeepout(-r / 2, 0.1, keepouts):
                alpha = alpha - 2 * alphapad
            if alpha == 180:
                kicad_modg.append(
                    Circle(center=[0, 0], radius=r / 2, layer="F.SilkS", width=lw_slk)
                )
                fullCircle = True
            else:
                kicad_modg.append(
                    Arc(
                        center=[0, 0],
                        start=[-xpad, -ypad],
                        angle=alpha,
                        layer="F.SilkS",
                        width=lw_slk,
                    )
                )
                kicad_modg.append(
                    Arc(
                        center=[0, 0],
                        start=[-xpad, ypad],
                        angle=-alpha,
                        layer="F.SilkS",
                        width=lw_slk,
                    )
                )
        if fullCircle:
            x = -d_slk / 2 + lw_slk * 2
            y = math.sqrt(d_slk * d_slk / 4 - x * x)
            kicad_modg.append(
                Line(start=[x, -y], end=[x, y], layer="F.SilkS", width=lw_slk)
            )
        else:
            kicad_modg.append(
                Line(
                    start=[-xpads[0], ypads[0]],
                    end=[-xpads[1], ypads[0]],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            kicad_modg.append(
                Line(
                    start=[-xpads[0], -ypads[0]],
                    end=[-xpads[1], -ypads[0]],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
    elif led_type == "oval":
        r = w_slk / 2
        ystart = 0
        xstart = math.sqrt(r * r - ystart * ystart)
        ycenter = h_slk / 2 - r
        alpha = 180 - 2 * math.degrees(math.atan(math.fabs(ycenter) / xstart))
        kicad_modg.append(
            Arc(
                center=[0, -ycenter],
                start=[-xstart, ystart],
                angle=alpha,
                layer="F.SilkS",
                width=lw_slk,
            )
        )
        kicad_modg.append(
            Arc(
                center=[0, ycenter],
                start=[-xstart, -ystart],
                angle=-alpha,
                layer="F.SilkS",
                width=lw_slk,
            )
        )
        xmark = -xstart + 2 * lw_slk
        ymark = ycenter + math.sqrt(r * r - xmark * xmark)
        addVLineWithKeepout(
            kicad_modg, xmark, -ymark, ymark, "F.SilkS", lw_slk, keepouts
        )

    # create courtyard
    kicad_mod.append(
        Rectangle(
            start=[roundCrt(l_crt + offset[0]), roundCrt(t_crt + offset[1])],
            end=[
                roundCrt(l_crt + w_crt + offset[0]),
                roundCrt(t_crt + h_crt + offset[1]),
            ],
            layer="F.CrtYd",
            width=lw_crt,
        )
    )

    # debug_draw_keepouts(kicad_modg, keepouts)

    # create pads
    pn = 1
    for p in padpos:
        ps = Pad.SHAPE_CIRCLE
        if p[4] != p[5]:
            ps = Pad.SHAPE_OVAL
        if p[0] == 1:
            ps = pad1style
        kicad_modg.append(
            Pad(
                number=p[0],
                type=Pad.TYPE_THT,
                shape=ps,
                at=[p[1], p[2]],
                size=[p[4], p[5]],
                drill=p[3],
                layers=Pad.LAYERS_THT,
            )
        )
    # Add a snap-point, it should be in the center between the pads
    kicad_mod.append(
        Point(
            at=offset,
            size=2,
            layer=global_config.get_layer_for_function("centroid"),
        )
    )

    # add model
    if has3d != 0:
        kicad_modg.append(
            Model(
                filename=global_config.model_3d_prefix
                + lib_name
                + ".3dshapes/"
                + footprint_name
                + global_config.model_3d_suffix,
                at=[0, 0, 0],
                scale=[1, 1, 1],
                rotate=[0, 0, 0],
            )
        )

    write_footprint(kicad_mod, lib_name, generator_name)


# LED footprints for horizontally mounted LEDs
#   style options:
#     1. led_type="simple"
#                    +------\    ^
#     ^       OO     |       \   |
#     pitch          |        |  dled
#     v       OO     |       /   |
#                    +------/    v
#             <------>offsetled
#                    <--wled->
#
#  led_type="round"/"rect"
def makeLEDHorizontal(
    generator_name,
    pins=2,
    pitch=2.54,
    dled=5,
    dledout=5.8,
    offsetled=2.54,
    wled=8.6,
    ddrill=0.8,
    wledback=1,
    led_type="round",
    has3d=1,
    fpname_override="",
    desc_extras_start=None,
    desc_extras_end=None,
    tag_extras=None,
    base_filename="LED",
    lib_name="LED_THT",
    name_additions=None,
    height3d=5,
    ledypos=0,
):
    if desc_extras_start is None:
        desc_extras_start = []
    if name_additions is None:
        name_additions = []
    if desc_extras_end is None:
        desc_extras_end = []
    if tag_extras is None:
        tag_extras = []

    padx = 2 * ddrill
    pady = padx
    if padx + min_pad_distance > pitch:
        padx = pitch - min_pad_distance
    txtoffset = txt_offset

    pad1style = Pad.SHAPE_RECT

    padpos = []
    offset = [0, 0]
    overpad_width = (pins - 1) * pitch
    xpad = -overpad_width / 2
    offset = [-xpad, 0]
    for p in range(1, pins + 1):
        padpos.append([p, xpad, 0, ddrill, padx, pady])
        xpad = xpad + pitch

    l_fab = -max(dledout, overpad_width + padx) / 2
    t_fab = -pady / 2
    w_fab = max(dledout, overpad_width + padx)
    h_fab = pady / 2 + offsetled + wled
    h_slk = h_fab + 2 * slk_offset
    w_slk = w_fab + 2 * slk_offset
    l_slk = l_fab - slk_offset
    t_slk = t_fab - slk_offset
    w_crt = max(w_slk, overpad_width + padx) + 2 * crt_offset
    h_crt = h_slk + 2 * crt_offset
    l_crt = l_slk - crt_offset
    t_crt = t_slk - crt_offset

    snfp = ""
    sn = ""
    snt = ""

    size_filename = ""
    size_info = []
    if led_type == "round":
        size_filename = "_D{0:0.1f}mm".format(dled)
        size_info.append("diameter {0:0.1f}mm".format(dled))
    else:
        if dled != dledout:
            size_filename = size_filename + "_D{0:0.1f}mm".format(dled)
            size_info.append("diameter {0:0.1f}mm".format(dled))
        else:
            size_info.append("Rectangular")
        size_filename = size_filename + "_W{0:0.1f}mm_H{1:0.1f}mm".format(
            dled, height3d
        )
        size_info.append("size {0:0.1f}x{1:0.1f}mm".format(dled, height3d))

    size_info.append("horizontal offset {}mm".format(offsetled))

    fnypos = ""
    if ledypos > 0:
        fnypos = "_Z{0:0.1f}mm".format(ledypos)
        size_info.append("z-position of LED center {0:0.1f}mm".format(ledypos))
    else:
        ledypos = math.ceil(dled / 2 + 0.5)

    pincount_filename = ""
    pincount_tag = "{0:d} pins".format(pins)
    if pins > 2:
        pincount_filename = "-{0:d}".format(pins)

    footprint_name = base_filename + size_filename + pincount_filename

    description = ["LED"]
    tags = ["LED"]

    added_info = list(desc_extras_start) + size_info
    if len(pincount_tag) > 0:
        added_info.append(pincount_tag)

    for t in added_info:
        if len(t):
            description.append(t)
    if fpname_override != "":
        footprint_name = fpname_override

    for t in desc_extras_end:
        if len(t):
            description.append(t)
    description.append("generated by kicad-footprint-generator")

    for t in tag_extras:
        if len(t):
            tags.append(t)

    footprint_name = footprint_name + "_Horizontal_O{0:1.2f}mm{1}".format(
        offsetled, fnypos
    )

    for n in name_additions:
        if len(n) > 0:
            footprint_name = footprint_name + "_" + n

    # init kicad footprint
    kicad_mod = Footprint(footprint_name, FootprintType.THT)
    kicad_mod.setDescription(", ".join(description))
    kicad_mod.setTags(" ".join(tags))

    kicad_modg = Translation(offset[0], offset[1])
    kicad_mod.append(kicad_modg)

    # set general values
    kicad_modg.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[0, t_slk - txtoffset],
            layer="F.SilkS",
        )
    )
    kicad_modg.append(
        Property(
            name=Property.VALUE,
            text=footprint_name,
            at=[0, t_slk + h_slk + txtoffset],
            layer="F.Fab",
        )
    )
    ref_size = [0.8, 0.8]
    ref_pos = [0, offsetled + wled / 2 - ref_size[1]]
    kicad_modg.append(
        Text(
            text="${REFERENCE}",
            at=ref_pos,
            layer="F.Fab",
            size=ref_size,
            thickness=0.12,
        )
    )

    # create FAB-layer
    if led_type == "round":
        kicad_modg.append(
            Arc(
                center=[0, offsetled + wled - dled / 2],
                start=[-dled / 2, offsetled + wled - dled / 2],
                angle=-180,
                layer="F.Fab",
                width=lw_fab,
            )
        )
        kicad_modg.append(
            Line(
                start=[-dled / 2, offsetled],
                end=[-dled / 2, offsetled + wled - dled / 2],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        kicad_modg.append(
            Line(
                start=[dled / 2, offsetled],
                end=[dled / 2, offsetled + wled - dled / 2],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        kicad_modg.append(
            Line(
                start=[-dled / 2, offsetled],
                end=[dled / 2, offsetled],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        kicad_modg.append(
            Rectangle(
                start=[dledout / 2, offsetled],
                end=[dled / 2, offsetled + wledback],
                layer="F.Fab",
                width=lw_fab,
            )
        )
        snappoint_lens = [
            offset[0],
            offsetled + wled - dled / 2,
        ]  # same as the center of the lens-arc
    elif led_type == "box":
        snappoint_lens = [offset[0], offsetled + wled]
        if wledback <= 0:
            kicad_modg.append(
                Rectangle(
                    start=[-dledout / 2, offsetled],
                    end=[dledout / 2, offsetled + wled],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
        else:
            kicad_modg.append(
                Rectangle(
                    start=[-dledout / 2, offsetled],
                    end=[dledout / 2, offsetled + wledback],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )
            snappoint_lens = [offset[0], offsetled + wledback]
        if dled != dledout:
            kicad_modg.append(
                Rectangle(
                    start=[-dled / 2, offsetled + wledback],
                    end=[dled / 2, offsetled + wled],
                    layer="F.Fab",
                    width=lw_fab,
                )
            )

    # add snap point between the pins
    kicad_mod.append(
        Point(
            at=offset,
            size=2,
            layer=global_config.get_layer_for_function("centroid"),
        )
    )
    # and a snap-point where the lens is
    kicad_mod.append(
        Point(
            at=snappoint_lens,
            size=2,
            layer=global_config.get_layer_for_function("centroid"),
        )
    )

    for p in padpos:
        kicad_modg.append(
            Rectangle(
                start=[p[1], p[2]], end=[p[1], offsetled], layer="F.Fab", width=lw_fab
            )
        )

    # build keepeout for SilkScreen
    keepouts = []
    for p in padpos:
        if p[0] == 1:
            keepouts = keepouts + addKeepoutRect(
                p[1],
                p[2],
                p[4] + 2 * lw_slk + 2 * slk_offset,
                p[5] + 2 * lw_slk + 2 * slk_offset,
            )
        else:
            keepouts = keepouts + addKeepoutRound(
                p[1],
                p[2],
                p[4] + 2 * lw_slk + 2 * slk_offset,
                p[5] + 2 * lw_slk + 2 * slk_offset,
            )

    # create SILKSCREEN-layer
    if led_type == "round":
        kicad_modg.append(
            Arc(
                center=[0, offsetled + wled - dled / 2],
                start=[-dled / 2 - slk_offset, offsetled + wled - dled / 2],
                angle=-180,
                layer="F.SilkS",
                width=lw_slk,
            )
        )
        kicad_modg.append(
            Line(
                start=[-dled / 2 - slk_offset, offsetled - slk_offset],
                end=[-dled / 2 - slk_offset, offsetled + wled - dled / 2],
                layer="F.SilkS",
                width=lw_slk,
            )
        )
        kicad_modg.append(
            Line(
                start=[dled / 2 + slk_offset, offsetled - slk_offset],
                end=[dled / 2 + slk_offset, offsetled + wled - dled / 2],
                layer="F.SilkS",
                width=lw_slk,
            )
        )
        kicad_modg.append(
            Line(
                start=[-dled / 2 - slk_offset, offsetled - slk_offset],
                end=[dled / 2 + slk_offset, offsetled - slk_offset],
                layer="F.SilkS",
                width=lw_slk,
            )
        )
        kicad_modg.append(
            Rectangle(
                start=[dledout / 2 + slk_offset, offsetled - slk_offset],
                end=[dled / 2 + slk_offset, offsetled + wledback + slk_offset],
                layer="F.SilkS",
                width=lw_slk,
            )
        )
    elif led_type == "box":
        if wledback <= 0:
            kicad_modg.append(
                Rectangle(
                    start=[-dledout / 2 - slk_offset, offsetled - slk_offset],
                    end=[dledout / 2 + slk_offset, offsetled + wled + slk_offset],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            kicad_modg.append(
                Line(
                    start=[-dledout / 2 - slk_offset + lw_slk, offsetled - slk_offset],
                    end=[
                        -dledout / 2 + lw_slk - slk_offset,
                        offsetled + wled + slk_offset,
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            kicad_modg.append(
                Line(
                    start=[
                        -dledout / 2 - slk_offset + lw_slk * 2,
                        offsetled - slk_offset,
                    ],
                    end=[
                        -dledout / 2 + lw_slk * 2 - slk_offset,
                        offsetled + wled + slk_offset,
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
        else:
            kicad_modg.append(
                Rectangle(
                    start=[-dledout / 2 - slk_offset, offsetled - slk_offset],
                    end=[dledout / 2 + slk_offset, offsetled + wledback + slk_offset],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            kicad_modg.append(
                Line(
                    start=[-dledout / 2 - slk_offset + lw_slk, offsetled - slk_offset],
                    end=[
                        -dledout / 2 + lw_slk - slk_offset,
                        offsetled + wledback + slk_offset,
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
            kicad_modg.append(
                Line(
                    start=[
                        -dledout / 2 - slk_offset + lw_slk * 2,
                        offsetled - slk_offset,
                    ],
                    end=[
                        -dledout / 2 + lw_slk * 2 - slk_offset,
                        offsetled + wledback + slk_offset,
                    ],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )
        if dled != dledout:
            kicad_modg.append(
                Rectangle(
                    start=[-dled / 2 - slk_offset, offsetled + wledback + slk_offset],
                    end=[dled / 2 + slk_offset, offsetled + wled + slk_offset],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )

    for p in padpos:
        if pady / 2 + slk_offset + lw_slk < offsetled - slk_offset:
            kicad_modg.append(
                Rectangle(
                    start=[p[1], pady / 2 + slk_offset + lw_slk],
                    end=[p[1], offsetled - slk_offset],
                    layer="F.SilkS",
                    width=lw_slk,
                )
            )

    # create courtyard
    kicad_mod.append(
        Rectangle(
            start=[roundCrt(l_crt + offset[0]), roundCrt(t_crt + offset[1])],
            end=[
                roundCrt(l_crt + w_crt + offset[0]),
                roundCrt(t_crt + h_crt + offset[1]),
            ],
            layer="F.CrtYd",
            width=lw_crt,
        )
    )

    # debug_draw_keepouts(kicad_modg, keepouts)

    # create pads
    pn = 1
    for p in padpos:
        ps = Pad.SHAPE_CIRCLE
        if p[4] != p[5]:
            ps = Pad.SHAPE_OVAL
        if p[0] == 1:
            ps = pad1style
        kicad_modg.append(
            Pad(
                number=p[0],
                type=Pad.TYPE_THT,
                shape=ps,
                at=[p[1], p[2]],
                size=[p[4], p[5]],
                drill=p[3],
                layers=Pad.LAYERS_THT,
            )
        )

    # add model
    if has3d != 0:
        kicad_modg.append(
            Model(
                filename=global_config.model_3d_prefix
                + lib_name
                + ".3dshapes/"
                + footprint_name
                + global_config.model_3d_suffix,
                at=[0, 0, 0],
                scale=[1, 1, 1],
                rotate=[0, 0, 0],
            )
        )

    write_footprint(kicad_mod, lib_name, generator_name)
