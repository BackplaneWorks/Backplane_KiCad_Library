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

from collections.abc import Sequence
from math import sqrt

from KicadModTree import Footprint, FootprintType, shape_to_node
from KicadModTree.tests.test_utils.fp_file_test import SerialisationTest
from kilibs.geom import (
    GeomCircle,
    GeomPolygon,
    GeomRectangle,
    GeomShapeClosed,
    Vector2D,
)
from kilibs.geom.operations import unite


def center_shape(shape: GeomShapeClosed) -> GeomShapeClosed:
    bbox = shape.bbox()
    x_center = -(bbox.left + bbox.right) / 2
    y_center = -(bbox.top + bbox.bottom) / 2
    return shape.translated(Vector2D(x_center, y=y_center))


def merge_and_add_to_footprint(
    shape1: GeomShapeClosed, shape2: GeomShapeClosed, fp: Footprint, y: float
) -> float:
    bbox1 = shape1.bbox()
    bbox2 = shape2.bbox()
    width1 = bbox1.size.x
    width2 = bbox2.size.x
    x = [-12, 0, 12]
    dist_x1 = [0.0, width1 / 4, width1 / 2]  # Overlapping, intersecting
    dist_x2 = [0.0, width2 / 4, width2 / 2]  # Overlapping, intersecting
    bbox = bbox1.copy().include_bbox(bbox2)
    for i in range(3):
        shape1 = center_shape(shape1).translated(
            Vector2D(x[i] - dist_x1[i], y + bbox.size.y / 2)
        )
        shape2 = center_shape(shape2).translated(
            Vector2D(x[i] + dist_x2[i], y + bbox.size.y / 2)
        )
        results = unite(shape1, shape2)
        for result in results:
            fp.append(shape_to_node(result, layer="F.SilkS", width=0.12))  # type: ignore
    return bbox.size.y + 1


def gen_footprint() -> Footprint:
    kicad_mod = Footprint("test", FootprintType.SMD)
    # Triangle
    shape1 = [(-sqrt(3), 0.0), (0.0, -1.0), (0.0, 1.0)]
    # Octagon
    shape2 = [(-1.0, -1.0), (0.0, -1.5), (1.0, -1.0), (1.5, 0.0), (1.0, 1.0), (0.0, 1.5), (-1.0, 1.0), (-1.5, 0.0)]  # fmt: skip  # NOQA
    # Concave shape
    shape3 = [(0.0, -3.0), (4.0, -3.0), (2.0, -2.0), (1.0, -2.5), (1.0, 1.0), (2.0, 1.0), (5.0, 0.0), (6.0, 0.0), (0.0, 3.0)]  # fmt: skip  # NOQA

    shapes: Sequence[GeomShapeClosed] = [
        GeomCircle(center=(0, 0), radius=1),  # circle
        GeomPolygon(shape=shape1),  # triangle
        GeomRectangle(center=(0, 0), size=(2, 2)),  # square
        GeomPolygon(shape=shape2),  # octagon
        GeomPolygon(shape=shape3),  # weird shape
    ]
    y_dist = 0
    for i in range(0, len(shapes)):
        for j in range(0, len(shapes)):
            y_dist += merge_and_add_to_footprint(
                shapes[i], shapes[j], kicad_mod, y=y_dist
            )
    return kicad_mod


class TestUnite(SerialisationTest):

    def test_unite(self) -> None:

        kicad_mod = gen_footprint()
        self.assert_serialises_as(kicad_mod, "test_unite.kicad_mod")
