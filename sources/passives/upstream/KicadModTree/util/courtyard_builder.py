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


from __future__ import annotations

from collections.abc import Iterable
from operator import itemgetter

import pyclipper  # type: ignore

from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Pad import Pad, ReferencedPad
from KicadModTree.nodes.base.Polygon import Polygon
from KicadModTree.nodes.base.Rectangle import Rectangle
from KicadModTree.nodes.Container import Container
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.Shape import Shape
from KicadModTree.nodes.specialized.ChamferedPad import ChamferedPad
from KicadModTree.nodes.specialized.ChamferedRectangle import ChamferedRectangle
from KicadModTree.nodes.specialized.ExposedPad import ExposedPad
from KicadModTree.nodes.specialized.PadArray import PadArray
from KicadModTree.nodes.specialized.PolygonLine import PolygonLine
from kilibs.config.global_config import GlobalConfig
from kilibs.geom.bounding_box import BoundingBox
from kilibs.geom.operations import is_polygon_clockwise, round_to_grid_increasing_area
from kilibs.geom.shapes.geom_chamfered_rectangle import GeomChamferedRectangle
from kilibs.geom.shapes.geom_line import GeomLine
from kilibs.geom.shapes.geom_polygon import GeomPolygon
from kilibs.geom.shapes.geom_rectangle import GeomRectangle
from kilibs.geom.shapes.geom_shape import GeomShape, GeomShapeClosed
from kilibs.geom.vector import Vector2D


class CourtyardBuilder:
    SCALE_FACTOR = 1e6
    """Scale factor that allows to convert between the KiCad resolution (1 nm) and the
    resolution of an integer (1)."""

    def __init__(self, global_config: GlobalConfig) -> None:

        # Instance attributes:
        self.global_config: GlobalConfig
        """The global config."""
        self.src_pts: list[list[list[float]]]
        """List of the source polygons."""
        self.crt_pts: list[list[float]]
        """The courtyard polygon."""
        self._node: Shape | None
        """The courtyard node."""
        self._bbox: BoundingBox | None
        """The bounding box of the courtyard."""

        self.global_config = global_config
        self.src_pts = []  # source points
        self.crt_pts = []  # courtyard points
        self._node = None
        self._bbox = None

    @classmethod
    def from_node(
        cls,
        node: Iterable[Node],
        global_config: GlobalConfig,
        offset_fab: float,
        offset_pads: float | None = None,
        outline: Node | GeomShapeClosed | BoundingBox | None = None,
    ) -> CourtyardBuilder:
        """
        Derives a courtyard with minimal area from the pads and primitives on the
        fabrication layer of the footprint and adds it to the footprint. Alternatively,
        instead of using the primitives on the fabrication layer of the footprint, the
        outline given as a separate argument can be used.

        Args:
            node: a node (typically the footprint).
            global_config: the global config.
            offset_fab: minimum clearance between courtyard and primitives on the
                fabrication layer.
            offset_pads: minimum clearance between courtyard and the pads. If omitted,
                the value of offset_fab is used.
            outline: optional outline of the component body.

        Returns:
            The bounding box of the courtyard.
        """
        cb = cls(global_config)
        if outline is None:
            use_fab_layer = True
        else:
            cb.add_element(outline, offset_fab, offset_pads, True)
            use_fab_layer = False
        nodes = node.children if isinstance(node, Container) else node
        for n in nodes:
            cb.add_element(n, offset_fab, offset_pads, use_fab_layer)
        cb._build()
        return cb

    @property
    def bbox(self) -> BoundingBox:
        """Get the bounding box of the courtyard."""
        if self._bbox is None:
            top = min(self.crt_pts, key=itemgetter(1))[1]
            bottom = max(self.crt_pts, key=itemgetter(1))[1]
            left = min(self.crt_pts, key=itemgetter(0))[0]
            right = max(self.crt_pts, key=itemgetter(0))[0]
            p1 = Vector2D.from_floats(left, top)
            p2 = Vector2D.from_floats(right, bottom)
            self._bbox = BoundingBox.from_vector2d(p1, p2)
            return self._bbox
        else:
            return self._bbox

    @property
    def node(self) -> Shape:
        """The courtyard node."""
        if self._node is None:
            return self._build()
        else:
            return self._node

    def _build(self) -> Shape:
        """Calculate and return the courtyard node and return it."""
        if len(self.src_pts) == 0:
            raise RuntimeError("Insufficient shapes to build a courtyard from.")
        pc = pyclipper.Pyclipper()  # pyright: ignore
        pc.AddPaths(  # pyright: ignore
            pyclipper.scale_to_clipper(  # pyright: ignore
                self.src_pts, CourtyardBuilder.SCALE_FACTOR
            ),
            pyclipper.PT_SUBJECT,  # pyright: ignore
            True,  # pyright: ignore
        )
        result: list[list[list[float]]] = pc.Execute(  # pyright: ignore
            pyclipper.CT_UNION,  # pyright: ignore
            pyclipper.PFT_NONZERO,  # pyright: ignore
            pyclipper.PFT_NONZERO,  # pyright: ignore
        )
        if len(result) != 1:  # pyright: ignore
            result = CourtyardBuilder._remove_holes(result)  # pyright: ignore
        if len(result) != 1:  # pyright: ignore
            result = CourtyardBuilder._unite_disjunct_courtyards(
                result  # pyright: ignore
            )
        round_to_grid_increasing_area(
            result[0],  # pyright: ignore
            int(self.global_config.courtyard_grid * CourtyardBuilder.SCALE_FACTOR),
        )
        result = CourtyardBuilder._simplify(result)  # pyright: ignore
        crt_pts: list[list[float]] = pyclipper.scale_from_clipper(  # pyright: ignore
            result, CourtyardBuilder.SCALE_FACTOR
        )[0]
        self.crt_pts = crt_pts

        width = self.global_config.courtyard_line_width
        if len(crt_pts) == 4:  # pyright: ignore
            p1 = crt_pts[0]  # pyright: ignore
            p2 = crt_pts[2]  # pyright: ignore
            self._node = Rectangle(
                width=width, layer="F.CrtYd", start=p1, end=p2  # pyright: ignore
            )
        else:
            crt_pts.append(crt_pts[0])  # close the courtyard  # pyright: ignore
            self._node = PolygonLine(
                shape=crt_pts, width=width, layer="F.CrtYd"  # pyright: ignore
            )
        return self._node

    def add_element(
        self,
        node: Node | GeomShape | BoundingBox,
        offset_fab: float,
        offset_pads: float | None = None,
        use_fab_layer: bool = True,
    ) -> None:
        """
        Add an element (node or geometric primitive) to the list of courtyard points.
        """
        if offset_pads is None:
            offset_pads = offset_fab
        if isinstance(node, Shape):
            if node.layer == "F.Fab" and use_fab_layer:
                if isinstance(node, Rectangle):
                    self.add_rectangle(node, offset_fab)
                elif isinstance(node, Polygon | PolygonLine):
                    self.add_polygon(node, offset_fab)
                elif isinstance(node, Line):
                    self.add_line(node, offset_fab)
                elif isinstance(node, ChamferedRectangle):
                    self.add_element(node.get_shapes()[0], offset_fab)
        elif isinstance(node, GeomShape | BoundingBox):
            if isinstance(node, GeomRectangle | BoundingBox):
                self.add_rectangle(node, offset_fab)
            elif isinstance(node, GeomPolygon):
                self.add_polygon(node, offset_fab)
            elif isinstance(node, GeomLine):
                self.add_line(node, offset_fab)
            elif isinstance(node, GeomChamferedRectangle):
                self.add_element(node.get_shapes()[0], offset_fab)
        else:
            if isinstance(node, Pad | ExposedPad | ReferencedPad):
                self.add_pad(node, offset_pads)
            elif isinstance(node, PadArray):
                self.add_pad_array(node, offset_pads)

    def add_rectangle(
        self, rectangle: GeomRectangle | BoundingBox, offset: float
    ) -> None:
        """
        Add a GeomRectangle or BoundingBox to the list of courtyard points.
        """
        self.src_pts.append(
            [
                [rectangle.right + offset, rectangle.top - offset],
                [rectangle.right + offset, rectangle.bottom + offset],
                [rectangle.left - offset, rectangle.bottom + offset],
                [rectangle.left - offset, rectangle.top - offset],
            ]
        )
        self._node = None  # invalidate previous node calculations

    def add_polygon(self, pl: PolygonLine | GeomPolygon, offset: float) -> None:
        """
        Add a Polygon to the list of courtyard points.
        """
        polygon: list[list[float]] = []
        for point in pl.points:
            if isinstance(point, Vector2D):  # pyright: ignore
                polygon.append([point.x, point.y])

        if len(polygon) < 2:
            # ignore polygons with less than 2 vertices
            return
        elif len(polygon) == 2:
            # polygons with 2 vertices are just lines
            self.add_line(
                Line(start=polygon[0], end=polygon[1]), offset
            )  # pyright: ignore
            return
        else:
            # add offset around polygon
            pco = pyclipper.PyclipperOffset()  # pyright: ignore
            polygon = pyclipper.scale_to_clipper(  # pyright: ignore
                polygon, CourtyardBuilder.SCALE_FACTOR
            )
            pco.AddPath(  # pyright: ignore
                polygon,
                pyclipper.JT_MITER,  # pyright: ignore
                pyclipper.ET_CLOSEDPOLYGON,  # pyright: ignore
            )
            polygon = pyclipper.scale_from_clipper(  # pyright: ignore
                pco.Execute(  # pyright: ignore
                    int(offset * CourtyardBuilder.SCALE_FACTOR)
                ),
                CourtyardBuilder.SCALE_FACTOR,
            )[0]
            # make sure that the polygon is defined in clockwise direction
            if not is_polygon_clockwise(polygon):  # pyright: ignore
                polygon.reverse()  # pyright: ignore
            self.src_pts.append(polygon)  # pyright: ignore
            self._node = None  # invalidate previous node calculations

    def add_line(self, line: Line | GeomLine, offset: float) -> None:
        """Add a Line to the list of courtyard points."""
        delta_parallel = (line.end - line.start).normalize() * offset
        delta_orthogonal = delta_parallel.orthogonal().normalize() * offset
        pts: list[Vector2D] = []
        pts.append(line.start - delta_parallel - delta_orthogonal)
        pts.append(line.end + delta_parallel - delta_orthogonal)
        pts.append(line.end + delta_parallel + delta_orthogonal)
        pts.append(line.start - delta_parallel + delta_orthogonal)
        self.src_pts.append([[pt.x, pt.y] for pt in pts])
        self._node = None  # invalidate previous node calculations

    def add_pad(
        self, pad: Pad | ExposedPad | ReferencedPad | ChamferedPad, offset: float
    ) -> None:
        """
        Add a pad to the list of courtyard points.
        """
        self.add_rectangle(pad.bbox(), offset)
        self._node = None  # invalidate previous node calculations

    def add_pad_array(self, padarray: PadArray, offset: float) -> None:
        """
        Add a PadArray to the list of courtyard points.
        """
        children = padarray.children
        if not children:
            return
        if padarray.modified:
            for pad in children:
                self.add_pad(pad, offset)
        else:
            bbox_first = children[0].bbox()
            bbox_last = children[-1].bbox()
            left = min(bbox_first.left, bbox_last.left) - offset
            right = max(bbox_first.right, bbox_last.right) + offset
            top = min(bbox_first.top, bbox_last.top) - offset
            bottom = max(bbox_first.bottom, bbox_last.bottom) + offset
            self.src_pts.append(
                [[right, top], [right, bottom], [left, bottom], [left, top]]
            )
        self._node = None  # invalidate previous node calculations

    @staticmethod
    def _unite_disjunct_courtyards(
        crts: list[list[list[float]]],
    ) -> list[list[list[float]]]:
        # increase offset around polygons, unite them, decrease offset around resulting polygon
        offset = 2e5  # 0.2 mm

        # increase offset around polygons and unite them
        # (PyclipperOffset automatically unites overlapping polygons)
        pco = pyclipper.PyclipperOffset()  # pyright: ignore
        pco.AddPaths(  # pyright: ignore
            crts, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON  # pyright: ignore
        )
        crts = pco.Execute(offset)  # pyright: ignore

        # decrease offset around polygons
        pco.Clear()  # pyright: ignore
        pco.AddPaths(  # pyright: ignore
            crts, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON  # pyright: ignore
        )
        crts = pco.Execute(-offset)  # pyright: ignore

        if len(crts) != 1:  # pyright: ignore
            raise ValueError(f"Failed to unite courtyards.")
            # If this error is thrown, try increasing the value of 'offset'.

        return crts  # pyright: ignore

    @staticmethod
    def _remove_holes(crts: list[list[list[float]]]) -> list[list[list[float]]]:
        crts_without_holes: list[list[list[float]]] = []
        for crt in crts:
            if is_polygon_clockwise(crt):
                crts_without_holes.append(crt)
        return crts_without_holes

    @staticmethod
    def _simplify(crts: list[list[list[float]]]) -> list[list[list[float]]]:
        pc = pyclipper.Pyclipper()  # pyright: ignore
        return pyclipper.SimplifyPolygons(crts, pyclipper.PFT_NONZERO)  # type: ignore
