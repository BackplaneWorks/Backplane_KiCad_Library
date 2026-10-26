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
from kilibs.config import global_config as GC


def generate_all(global_config: GC.GlobalConfig, generator_name: str) -> int:
    lib_name = "LED_SMD"
    datasheet = "https://fscdn.rohm.com/en/products/databook/datasheet/opto/led/chip_multi/smlvn6rgb1u1-e.pdf"
    description = "RGB LED, 3.1x2.8mm"
    footprint_name = "LED_ROHM_SMLVN6"
    pkgWidth = 3.1
    pkgHeight = 2.8
    padXSpacing = 3.05
    padYSpacing = 1.05
    padWidth = 1.45
    padHeight = 0.6
    padCornerHeight = 0.8

    f = Footprint(footprint_name, FootprintType.SMD)
    f.setDescription(f"{description}, {datasheet}")
    f.setTags("LED ROHM SMLVN6")
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
    pCorner = [padWidth, padCornerHeight]
    s = [1.0, 1.0]
    sFabRef = [0.7, 0.7]

    t1 = 0.1
    t2 = 0.15

    wCrtYd = 0.05
    wFab = 0.1
    wSilkS = 0.12
    crtYd = 0.3
    silkClearance = 0.15

    pin1MarkerHeight = 0.33
    pin1MarkerWidth = 0.48

    xCenter = 0.0
    xPadRight = padXSpacing / 2
    xFabRight = pkgWidth / 2
    xSilkRight = xPadRight
    xRightCrtYd = max(xPadRight + padWidth / 2, xFabRight) + crtYd

    xLeftCrtYd = -xRightCrtYd
    xPadLeft = -xPadRight
    xFabLeft = -xFabRight
    xChamfer = xFabLeft + 1.0
    xSilkLeft = -xSilkRight

    yCenter = 0.0
    yPadBottom = padYSpacing
    yFabBottom = pkgHeight / 2
    yBottom = max(yFabBottom + 0.1, yPadBottom + padHeight / 2)
    ySilkBottom = yBottom + silkClearance
    yBottomCrtYd = yBottom + crtYd

    yTopCrtYd = -yBottomCrtYd
    ySilkTop = -ySilkBottom
    yFabTop = -yFabBottom
    yPadTop = -yPadBottom
    yChamfer = yFabTop + 1

    yValue = yFabBottom + 1.25
    yRef = yFabTop - 1.25

    yPin1Bot = ySilkTop
    yPin1Top = yPin1Bot - pin1MarkerHeight
    xPin1Mid = xFabLeft - 0.4
    xPin1Left = xPin1Mid - pin1MarkerWidth / 2
    xPin1Right = xPin1Mid + pin1MarkerWidth / 2

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
        PolygonLine(
            shape=[
                [xFabLeft, yChamfer],
                [xChamfer, yFabTop],
                [xFabRight, yFabTop],
                [xFabRight, yFabBottom],
                [xFabLeft, yFabBottom],
                [xFabLeft, yChamfer],
            ],
            layer="F.Fab",
            width=wFab,
        )
    )

    f.append(
        Line(
            start=[xSilkLeft, ySilkTop],
            end=[xSilkRight, ySilkTop],
            layer="F.SilkS",
            width=wSilkS,
        )
    )
    f.append(
        Line(
            start=[xSilkLeft, ySilkBottom],
            end=[xSilkRight, ySilkBottom],
            layer="F.SilkS",
            width=wSilkS,
        )
    )
    # pin 1 marker
    f.append(
        Polygon(
            shape=[[xPin1Mid, yPin1Bot], [xPin1Left, yPin1Top], [xPin1Right, yPin1Top]],
            fill=True,
            layer="F.SilkS",
            width=wSilkS,
        )
    )

    pads = ["1", "6", "2", "5", "3", "4"]
    padShape = Pad.SHAPE_ROUNDRECT

    radius_handler = RoundRadiusHandler(
        radius_ratio=0.2,
    )

    f.append(
        Pad(
            number=pads[0],
            type=Pad.TYPE_SMT,
            shape=padShape,
            at=[xPadLeft, yPadTop],
            size=pCorner,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=radius_handler,
        )
    )
    f.append(
        Pad(
            number=pads[1],
            type=Pad.TYPE_SMT,
            shape=padShape,
            at=[xPadRight, yPadTop],
            size=pCorner,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=radius_handler,
        )
    )
    f.append(
        Pad(
            number=pads[2],
            type=Pad.TYPE_SMT,
            shape=padShape,
            at=[xPadLeft, yCenter],
            size=p,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=radius_handler,
        )
    )
    f.append(
        Pad(
            number=pads[3],
            type=Pad.TYPE_SMT,
            shape=padShape,
            at=[xPadRight, yCenter],
            size=p,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=radius_handler,
        )
    )
    f.append(
        Pad(
            number=pads[4],
            type=Pad.TYPE_SMT,
            shape=padShape,
            at=[xPadLeft, yPadBottom],
            size=pCorner,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=radius_handler,
        )
    )
    f.append(
        Pad(
            number=pads[5],
            type=Pad.TYPE_SMT,
            shape=padShape,
            at=[xPadRight, yPadBottom],
            size=pCorner,
            layers=Pad.LAYERS_SMT,
            round_radius_handler=radius_handler,
        )
    )

    write_footprint(f, lib_name, generator_name)
    return 1
