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

from generators.tools.footprint.save_footprint import write_footprint
from KicadModTree import *
from KicadModTree.nodes.specialized.ChamferedRectangle import (
    ChamferedRectangle,
    ChamferSizeHandler,
    CornerSelection,
)
from kilibs.config import global_config as GC


def plcc4(generator_name: str, args):
    footprint_name = args["name"]

    pkgWidth = args["pkg_width"]
    pkgHeight = args["pkg_height"]

    padXSpacing = args["pad_x_spacing"]
    padYSpacing = args["pad_y_spacing"]

    padWidth = args["pad_width"]
    padHeight = args["pad_height"]

    pads_clockwise = args["pads_clockwise"]

    desc = str(pkgWidth) + "mm x " + str(pkgHeight) + "mm PLCC4 RGB LED, "

    lib_name = "LED_SMD"

    f = Footprint(footprint_name, FootprintType.SMD)
    f.setDescription(desc + args["datasheet"])
    f.setTags("LED Cree PLCC-4 " + args["tags"])
    f.append(
        Model(
            filename=global_config.model_3d_prefix
            + lib_name
            + ".3dshapes/"
            + footprint_name
            + global_config.model_3d_suffix,
            at=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0],
            rotate=[0.0, 0.0, 0.0],
        )
    )

    p = [padWidth, padHeight]
    r = pkgHeight * 0.4
    s = [1.0, 1.0]
    sFabRef = [0.5, 0.5]

    t1 = 0.075
    t2 = 0.15

    wCrtYd = 0.05
    wFab = 0.1

    xCenter = 0.0
    xPadRight = padXSpacing / 2
    xFabRight = pkgWidth / 2
    xPadRightCorner = xPadRight + padWidth / 2
    xSilkRight = xPadRightCorner + global_config.silk_pad_offset
    xSilkWidth = 2 * xSilkRight
    xRightCrtYd = xPadRightCorner + global_config.get_courtyard_offset(
        global_config.CourtyardType.DEFAULT
    )

    xLeftCrtYd = -xRightCrtYd
    xPadLeft = -xPadRight
    xFabLeft = -xFabRight
    xChamfer = xFabLeft + 1.0

    yCenter = 0.0
    yPadBottom = padYSpacing / 2
    yPadBotomCorner = yPadBottom + padHeight / 2
    yFabBottom = pkgHeight / 2
    ySilkBottom = max(
        yFabBottom + global_config.silk_fab_offset,
        yPadBotomCorner + global_config.silk_pad_offset,
    )
    ySilkHeight = 2 * ySilkBottom
    yBottomCrtYd = yFabBottom + global_config.get_courtyard_offset(
        global_config.CourtyardType.DEFAULT
    )

    yTopCrtYd = -yBottomCrtYd
    yFabTop = -yFabBottom
    yPadTop = -yPadBottom
    yChamfer = yFabTop + 1

    yValue = yFabBottom + 1.25
    yRef = yFabTop - 1.25

    f.append(
        Property(
            name=Property.REFERENCE,
            text="REF**",
            at=[xCenter, yRef],
            layer="F.SilkS",
            size=s,
            thickness=t2,
        )
    )
    f.append(
        Property(
            name=Property.VALUE,
            text=footprint_name,
            at=[xCenter, yValue],
            layer="F.Fab",
            size=s,
            thickness=t2,
        )
    )
    f.append(
        Text(
            text="${REFERENCE}",
            at=[xCenter, yCenter],
            layer="F.Fab",
            size=sFabRef,
            thickness=t1,
        )
    )

    f.append(
        Rectangle(
            start=[xLeftCrtYd, yTopCrtYd],
            end=[xRightCrtYd, yBottomCrtYd],
            layer="F.CrtYd",
            width=wCrtYd,
        )
    )

    f.append(
        Line(
            start=[xChamfer, yFabTop],
            end=[xFabLeft, yChamfer],
            layer="F.Fab",
            width=wFab,
        )
    )
    f.append(
        Rectangle(
            start=[xFabLeft, yFabTop],
            end=[xFabRight, yFabBottom],
            layer="F.Fab",
            width=wFab,
        )
    )
    f.append(Circle(center=[xCenter, yCenter], radius=r, layer="F.Fab", width=wFab))

    f.append(
        ChamferedRectangle(
            center=Vector2D(xCenter, yCenter),
            size=Vector2D(xSilkWidth, ySilkHeight),
            chamfer=ChamferSizeHandler(chamfer_exact=0.3),
            corners=CornerSelection({CornerSelection.TOP_LEFT: True}),
            layer="F.SilkS",
            width=global_config.silk_line_width,
            fill=False,
        )
    )

    if pads_clockwise:
        pads = ["1", "2", "3", "4"]
    else:
        pads = ["1", "4", "3", "2"]

    f.append(
        Pad(
            number=pads[0],
            type=Pad.TYPE_SMT,
            shape=Pad.SHAPE_ROUNDRECT,
            at=[xPadLeft, yPadTop],
            size=p,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=global_config.roundrect_radius_handler,
        )
    )
    f.append(
        Pad(
            number=pads[1],
            type=Pad.TYPE_SMT,
            shape=Pad.SHAPE_ROUNDRECT,
            at=[xPadRight, yPadTop],
            size=p,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=global_config.roundrect_radius_handler,
        )
    )
    f.append(
        Pad(
            number=pads[2],
            type=Pad.TYPE_SMT,
            shape=Pad.SHAPE_ROUNDRECT,
            at=[xPadRight, yPadBottom],
            size=p,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=global_config.roundrect_radius_handler,
        )
    )
    f.append(
        Pad(
            number=pads[3],
            type=Pad.TYPE_SMT,
            shape=Pad.SHAPE_ROUNDRECT,
            at=[xPadLeft, yPadBottom],
            size=p,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=global_config.roundrect_radius_handler,
        )
    )

    write_footprint(f, lib_name, generator_name)
    return 1


def generate_all(global_conf: GC.GlobalConfig, file: str, generator_name: str) -> int:
    global global_config
    global_config = global_conf

    parser = ModArgparser(plcc4)
    # the root node of .yml files is parsed as name
    parser.add_parameter("name", type=str, required=True)
    parser.add_parameter("datasheet", type=str, required=True)
    parser.add_parameter("tags", type=str, required=True)
    parser.add_parameter("pkg_width", type=float, required=False, default=2.0)
    parser.add_parameter("pkg_height", type=float, required=False, default=2.0)
    parser.add_parameter("pad_x_spacing", type=float, required=False, default=1.5)
    parser.add_parameter("pad_y_spacing", type=float, required=False, default=1.1)
    parser.add_parameter("pad_width", type=float, required=False, default=1.0)
    parser.add_parameter("pad_height", type=float, required=False, default=0.8)
    parser.add_parameter("pads_clockwise", type=bool, required=False, default=True)

    # now run our script which handles the whole part of parsing the files
    return parser.run(generator_name, [file])
