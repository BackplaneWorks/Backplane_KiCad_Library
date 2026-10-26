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

from math import sqrt

from KicadModTree import Footprint, FootprintType, shape_to_node
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest
from kilibs.geom import (
    GeomArc,
    GeomCompoundPolygon,
    GeomLine,
    GeomPolygon,
    GeomShapeClosed,
    Vector2D,
)
from tests.kilibs.geom.geom_test_shapes import TEST_SHAPES_CLOSED

# fmt: off
SHAPES_FOR_COMPOUND_POLYGON: list[list[GeomLine | GeomArc] | list[GeomPolygon]] = [
    [  # TO-92 style
        GeomArc(start=(-1, 1), end=(1, 1), mid=(0, -sqrt(2))),
        GeomLine(start=(1, 1), end=(-1, 1)),
    ],
    [  # Stadium:
        GeomArc(start=[-1, 1], mid=[-2, 0], end=[-1, -1]),
        GeomLine(start=[-1, -1], end=[1, -1]),
        GeomArc(start=[1, -1], mid=[2, 0], end=[1, 1]),
        GeomLine(start=[1, 1], end=[-1, 1]),
    ],
    [  # Inverted stadium:
        GeomArc(start=[-2, 1], mid=[-1, 0], end=[-2, -1]),
        GeomLine(start=[-2, -1], end=[2, -1]),
        GeomArc(start=[2, -1], mid=[1, 0], end=[2, 1]),
        GeomLine(start=[2, 1], end=[-2, 1]),
    ],
    [  # 8:
        GeomArc(start=(0, +sqrt(3) / 2), end=(0, -sqrt(3) / 2), mid=(-1.5, 0)),
        GeomArc(start=(0, -sqrt(3) / 2), end=(0, +sqrt(3) / 2), mid=(1.5, 0)),
    ],
    [  # Half-moon:
        GeomArc(start=(0.75, +sqrt(3) / 2), end=(0.75, -sqrt(3) / 2), mid=(-1.75, 0)),
        GeomArc(start=(0.75, -sqrt(3) / 2), end=(0.75, +sqrt(3) / 2), mid=(-0.75, 0)),
    ],
    [  # Down-looking C:
        GeomArc(start=(-2, 0.75), end=(+2, 0.75), mid=(0, -1.25)),
        GeomArc(start=(+2, 0.75), end=(+1, 0.75), mid=(+1.5, 1.25)),
        GeomArc(start=(+1, 0.75), end=(-1, 0.75), mid=(0, -0.25)),
        GeomArc(start=(-1, 0.75), end=(-2, 0.75), mid=(-1.5, 1.25)),
    ],
    [  # Triangle:
        GeomPolygon(shape=[(-1, 0.75), (0, -0.75), (1, 0.75)])  # NOQA
    ],
    [  # Octagon:
        GeomPolygon(shape=[(-1, -1), (0, -1.5), (1, -1), (1.5, 0), (1, 1), (0, 1.5), (-1, 1), (-1.5, 0)])  # NOQA
    ],
    [  # V-like shape:
        GeomPolygon(shape=[(0, -3), (3, -3), (2, -2), (1, -2), (1, 0), (2, 0), (5, -3), (6, -3), (0, 3), (0, -3)])  # NOQA
    ],
]
# fmt: on


def gen_footprint() -> Footprint:
    kicad_mod = Footprint("test", FootprintType.SMD)
    shapes: list[GeomShapeClosed] = []
    for shape in SHAPES_FOR_COMPOUND_POLYGON:
        shapes.append(GeomCompoundPolygon(shape=shape))
        # Also append the polygons:
        if isinstance(shape[0], GeomPolygon):
            shapes.append(shape[0])
    shapes.extend(TEST_SHAPES_CLOSED)

    inflate_amount: list[float] = [-1.5, -0.2, 0.0, 0.2, 1.5]
    y_translate = -5 * (len(inflate_amount) - 1)
    for j in range(len(inflate_amount)):
        x_translate = -5 * (len(shapes) - 1)
        for i in range(0, len(shapes)):
            translation = Vector2D(x_translate, y=y_translate)
            translated_shape = shapes[i].translated(translation)
            kicad_mod.append(shape_to_node(translated_shape, layer="F.Fab", width=0.1))  # type: ignore
            try:
                inflated_shape = translated_shape.inflated(
                    amount=inflate_amount[j],
                )
                if isinstance(inflated_shape, GeomCompoundPolygon | GeomPolygon):
                    inflated_shape.simplify()
                    if (
                        inflate_amount[j] >= -0.5
                    ):  # Polygons that are deflated too much are rubbish. Don't plot them.
                        kicad_mod.append(
                            shape_to_node(inflated_shape, layer="F.SilkS", width=0.12)
                        )
                else:
                    kicad_mod.append(
                        shape_to_node(inflated_shape, layer="F.SilkS", width=0.12)
                    )
            except ValueError:
                pass
            x_translate += 10
        y_translate += 10

    return kicad_mod


class TestInflate(SerialisationTest):

    def test_inflate(self) -> None:

        kicad_mod = gen_footprint()
        self.assert_serialises_as(kicad_mod, "test_inflate.kicad_mod")
