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

from typing import Any
from KicadModTree import *
from kilibs.config import global_config as GC
from generators.tools.footprint.save_footprint import write_footprint

def roundCrtYd(x):
    sign = x / abs(x)
    return int((x + 0.0001 * sign) * 100) / 100.0

def textool(generator_name: str, args: dict[str, Any]) -> int:
    name = args["name"]
    nPads = args["n_pads"]
    dimA = args["a"]
    dimB = args["b"]
    dimC = args["c"]
    mils = args["c_mils"]
    lever = args["lever"]
    minWidth = args["min"]
    maxWidth = args["max"]
    lib_name = "Socket"

    widths = "_W" + str(minWidth) + "mm"
    for i in range(0, 15):
        w = i * 2.54
        if w > minWidth and w < maxWidth:
            widths = widths + "_W" + str(w) + "mm"
    widths = widths + "_W" + str(maxWidth) + "mm"

    footprint_name = "DIP_Socket-" + str(nPads) + widths + "_3M_" + name

    f = Footprint(footprint_name, FootprintType.THT)
    f.setDescription("3M " + str(nPads) + "-pin zero insertion force socket, through-hole, row spacing " + str(dimC) + " mm (" + str(mils) + " mils), http://multimedia.3m.com/mws/media/494546O/3mtm-dip-sockets-100-2-54-mm-ts0365.pdf")
    f.setTags("THT DIP DIL ZIF " + str(dimC) + "mm " + str(mils) + "mil Socket")
    f.append(Model(filename=global_config.model_3d_prefix + lib_name + ".3dshapes/" + footprint_name + global_config.model_3d_suffix, at=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0], rotate=[0.0, 0.0, 0.0]))

    pitch = 2.54

    d = [1.0, 1.0]
    p = [2.0, 1.44]

    r1 = 0.9
    r2 = 2.55

    s1 = [0.6, 0.6]
    s2 = [1.0, 1.0]

    t1 = 0.09
    t2 = 0.15

    wCrtYd = 0.05
    wFab = 0.1
    wSilkS = 0.12

    silk = 0.1
    crtYd = 0.5

    xLeftPads = 0.0
    xLeftFab = xLeftPads - (dimB - dimC) / 2
    xLeftSilk = xLeftFab - silk
    xLeftCrtYd = roundCrtYd(xLeftFab - crtYd)

    xRightPads = dimC
    xRightFab = xLeftFab + dimB
    xRightSilk = xRightFab + silk
    xRightCrtYd = roundCrtYd(xRightFab + crtYd)

    xLeftLever = -5.0
    xP1Ind = -4.95
    x06 = -3.7
    x07 = -3.5
    x08 = -3.2
    x09 = -2.85
    x10 = -1.9
    x11 = -1.7
    x12 = -1.65
    xRightLever = -0.4
    xMiddle = dimC / 2

    xLeftLeverCrtYd = roundCrtYd(xLeftLever - crtYd)
    xRightLeverCrtYd = roundCrtYd(xRightLever + crtYd)

    yTopPads = 0.0
    yTopFab = -10.56
    yTopSilk = yTopFab - silk
    yTopCrtYd = roundCrtYd(yTopFab - crtYd)

    yBottomFab = yTopFab + dimA
    yBottomSilk = yBottomFab + silk
    yBottomCrtYd = roundCrtYd(yBottomFab + crtYd)

    # These four are the lever
    yTopLever = yTopFab - lever # -25.4
    y02 = yTopLever + 1.4       # -24.0
    y03 = yTopLever + 5.0       # -20.4
    y04 = yTopLever + 7.0       # -18.4

    yRef = yTopFab - 1
    yValue = yBottomFab + 1
    yFabRef = (yTopFab + yBottomFab) / 2

    y09 = -9.75
    y10 = -9.4
    y11 = -8.8
    y12 = -8.4
    y13 = -6.35
    yBottomLever = -3.9
    yFirstLine = -1.27
    ySecondLine = 1.27

    yTopLeverCrtYd = roundCrtYd(yTopLever - crtYd)
    yBottomLeverCrtYd = roundCrtYd(yBottomLever + crtYd)

    # Text
    f.append(Property(name=Property.REFERENCE, text="REF**", at=[xMiddle, yRef],
                  layer="F.SilkS", size=s2, thickness=t2))
    f.append(Property(name=Property.VALUE, text=footprint_name, at=[xMiddle, yValue],
                  layer="F.Fab", size=s1, thickness=t1))
    f.append(Text(text='${REFERENCE}', at=[xMiddle, yFabRef],
                  layer="F.Fab", size=s2, thickness=t2))

    # Courtyard
    f.append(PolygonLine(shape=[[xLeftLeverCrtYd, yTopLeverCrtYd],
                                   [xRightLeverCrtYd, yTopLeverCrtYd],
                                   [xRightLeverCrtYd, yTopCrtYd],
                                   [xRightCrtYd, yTopCrtYd],
                                   [xRightCrtYd, yBottomCrtYd],
                                   [xLeftCrtYd, yBottomCrtYd],
                                   [xLeftCrtYd, yBottomLeverCrtYd],
                                   [xLeftLeverCrtYd, yBottomLeverCrtYd],
                                   [xLeftLeverCrtYd, yTopLeverCrtYd]],
                         layer="F.CrtYd", width=wCrtYd))

    # Fab Lever
    f.append(PolygonLine(shape=[[xLeftLever, y02],
                                   [x06, yTopLever],
                                   [x11, yTopLever],
                                   [xRightLever, y02],
                                   [xLeftLever, y02],
                                   [xLeftLever, y03],
                                   [xRightLever, y03],
                                   [xRightLever, y02]],
                         layer="F.Fab", width=wFab))
    f.append(Line(start=[xLeftLever, y03], end=[x07, y04], layer="F.Fab", width=wFab))
    f.append(Line(start=[xRightLever, y03], end=[x10, y04], layer="F.Fab", width=wFab))
    f.append(PolygonLine(shape=[[x07, y09],
                                   [x07, y04],
                                   [x10, y04],
                                   [x10, yTopFab]],
                         layer="F.Fab", width=wFab))

    # Fab Outline
    f.append(PolygonLine(shape=[[xRightFab, yBottomFab],
                                   [xLeftFab, yBottomFab],
                                   [xLeftFab, y10],
                                   [x09, yTopFab],
                                   [xRightFab, yTopFab],
                                   [xRightFab, yBottomFab]],
                         layer="F.Fab", width=wFab))

    # Silk Outline
    f.append(PolygonLine(shape=[[xLeftSilk, yBottomLever],
                                   [xLeftSilk, yBottomSilk],
                                   [xRightSilk, yBottomSilk],
                                   [xRightSilk, yTopSilk],
                                   [xLeftSilk, yTopSilk],
                                   [xLeftSilk, y11]],
                         layer="F.SilkS", width=wSilkS))

    # Silk Lever
    f.append(Line(start=[x12, yTopSilk], end=[x12, y12], layer="F.SilkS", width=wSilkS))
    f.append(Circle(center=[x08, y13], radius=r2, layer="F.SilkS", width=wSilkS))
    f.append(Circle(center=[x08, y13], radius=r1, layer="F.SilkS", width=wSilkS))

    # Silk Pin 1 Indicator
    f.append(Line(start=[xP1Ind, ySecondLine], end=[xP1Ind, yFirstLine],
                  layer="F.SilkS", width=wSilkS))

    # Pads
    pShape = Pad.SHAPE_RECT
    for i in range(0, nPads >> 1):
        y = yTopPads + i * pitch
        f.append(Pad(number=str(i+1), type=Pad.TYPE_THT, shape=pShape,
                     at=[xLeftPads, y], size=p, layers=Pad.LAYERS_THT, drill=d))
        pShape = Pad.SHAPE_OVAL
        f.append(Pad(number=str(nPads-i), type=Pad.TYPE_THT, shape=pShape,
                     at=[xRightPads, y], size=p, layers=Pad.LAYERS_THT, drill=d))

    write_footprint(f, lib_name, generator_name)
    return 1


def generate_all(generator_name: str, global_conf: GC.GlobalConfig, file: str) -> int:
    global global_config
    global_config = global_conf
    parser = ModArgparser(textool)
    # the root node of .yml files is parsed as name
    parser.add_parameter("name", type=str, required=True)
    parser.add_parameter("n_pads", type=int, required=True)
    parser.add_parameter("a", type=float, required=True)
    parser.add_parameter("b", type=float, required=True)
    parser.add_parameter("c", type=float, required=True)
    parser.add_parameter("c_mils", type=int, required=True)
    parser.add_parameter("lever", type=float, required=False, default=12.3)
    parser.add_parameter("min", type=float, required=True)
    parser.add_parameter("max", type=float, required=True)

    # now run our script which handles the whole part of parsing the files
    return parser.run(generator_name, [file])
