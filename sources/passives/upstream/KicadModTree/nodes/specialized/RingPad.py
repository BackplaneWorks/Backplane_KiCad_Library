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
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) 2018 by Rene Poeschl, github @poeschlr
# (C) The KiCad Librarian Team

"""Class definitions for a ring pad."""

from __future__ import annotations, division

from math import ceil
from typing import cast

from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.base.Circle import Circle
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Pad import Pad
from KicadModTree.nodes.Container import Container
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.shape_to_node import shape_to_node
from kilibs.geom import GeomArc, GeomCircle, GeomLine, Vec2DCompatible, Vector2D
from kilibs.geom.operations import split


class _RingPadPrimitive(Node):
    """A ring pad primitive."""

    def __init__(
        self,
        radius: float,
        width: float,
        layers: list[str],
        at: Vector2D = Vector2D.zero(),
        number: str | int = "",
    ) -> None:
        """Create a ring pad primitive.

        Args:
            radius: Middle radius of the ring.
            width: Width of the ring (outer radius - inner radius).
            at: Position of the center.
            layers: Layers used for creating the pad.
            number: Number/name of the pad.
        """

        # Instance attributes:
        self.at: Vector2D
        """Position of the center of the ring pad."""
        self.radius: float
        """Middle radius of the ring."""
        self.width: float
        """Width of the ring (outer radius - inner radius)."""
        self.layers: list[str]
        """Layers used for creating the pad."""
        self.number: str | int
        """Number/name of the pad."""

        Node.__init__(self)
        self.at = Vector2D(at)
        self.radius = radius
        self.width = width
        self.layers = layers
        self.number = number

    def copy(self) -> _RingPadPrimitive:
        return _RingPadPrimitive(
            at=self.at,
            radius=self.radius,
            width=self.width,
            layers=self.layers,
            number=self.number,
        )

    def flatten(self) -> list[Pad]:
        """Return the leaf nodes to serialize."""
        return [
            Pad(
                number=self.number,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_CUSTOM,
                at=(self.at + Vector2D(self.radius, 0)),
                size=self.width,
                layers=self.layers,
                primitives=[
                    Circle(
                        center=(-self.radius, 0),
                        radius=self.radius,
                        width=self.width,
                    )
                ],
            )
        ]

    def translate(self, vector: Vector2D) -> _RingPadPrimitive:
        """Move the ring pad primitive.

        Args:
            vector: The distance in mm in the x- and y-direction.

        Returns:
            The translated ring pad primitive.
        """
        self.at += vector
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> _RingPadPrimitive:
        """Rotate the ring pad primitive around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated ring pad primitive.
        """
        self.at.rotate(angle, origin)
        return self


class _ArcPadPrimitive(Node):
    """An arc pad primitive."""

    reference_arc: GeomArc
    """The reference arc used for this pad."""
    width: float
    """Width of the pad."""
    number: str | int
    """Number/name of the pad."""
    layers: list[str]
    """Layers on which are used for the pad."""
    minimum_overlap: float
    """Minimum overlap."""
    round_radius: float
    """The calculated round radius for the pad corners."""
    start_line: GeomLine | None
    """Line confining the side near the reference arc's start point."""
    end_line: GeomLine | None
    """Line confining the side near the reference arc's end point."""

    def __init__(
        self,
        reference_arc: GeomArc,
        width: float,
        layers: list[str],
        start_line: GeomLine | None = None,
        end_line: GeomLine | None = None,
        number: str | int = "",
        minimum_overlap: float = 0.1,
        round_radius: float | None = None,
        round_radius_ratio: float = 0.25,
        max_round_radius: float | None = 0.25,
    ) -> None:
        """Create an arc pad primitive.

        Args:
            number: Number/name of the pad.
            width: Width of the pad.
            layers: Layers on which are used for the pad.
            round_radius_ratio: Round radius.
            max_round_radius: Maximum round radius. Use `None` to ignore.
            reference_arc: The reference arc used for this pad.
            start_line: Line confining the side near the reference points start point.
            end_line: Line confining the side near the reference points end point.
            minimum_overlap: Minimum overlap.
        """
        Node.__init__(self)
        self.reference_arc = GeomArc(shape=reference_arc)
        self.width = width
        self.number = number
        self.layers = layers
        self.minimum_overlap = minimum_overlap
        self._set_round_radius(round_radius, round_radius_ratio, max_round_radius)
        self.set_limiting_lines(start_line, end_line)

    def _set_round_radius(
        self,
        round_radius: float | None,
        round_radius_ratio: float,
        max_round_radius: float | None,
    ) -> None:
        if round_radius is not None:
            self.round_radius = round_radius
            return
        r = self.width * round_radius_ratio
        if max_round_radius is not None and max_round_radius > 0:
            self.round_radius = min(r, max_round_radius)

    def set_limiting_lines(
        self, start_line: GeomLine | None, end_line: GeomLine | None
    ) -> None:
        if start_line is not None:
            self.start_line = start_line.copy()
        else:
            self.start_line = None
        if end_line is not None:
            self.end_line = end_line.copy()
        else:
            self.end_line = None

    def copy(self) -> _ArcPadPrimitive:
        return _ArcPadPrimitive(
            reference_arc=self.reference_arc,
            width=self.width,
            round_radius=self.round_radius,
            number=self.number,
            layers=self.layers,
            start_line=self.start_line,
            end_line=self.end_line,
            minimum_overlap=self.minimum_overlap,
        )

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> _ArcPadPrimitive:
        """Rotate around given origin.

        Args:
            angle: Rotation angle in degrees.
            origin: Origin point for the rotation.
        """
        self.reference_arc.rotate(angle=angle, origin=origin)
        if self.start_line is not None:
            self.start_line.rotate(angle=angle, origin=origin)
        if self.end_line is not None:
            self.end_line.rotate(angle=angle, origin=origin)
        return self

    def translate(self, vector: Vector2D) -> _ArcPadPrimitive:
        """Move the arc pad primitive.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated arc pad primitive.
        """

        self.reference_arc.translate(vector)
        if self.start_line is not None:
            self.start_line.translate(vector)
        if self.end_line is not None:
            self.end_line.translate(vector)
        return self

    def _get_step(self) -> float:
        line_width = self.round_radius * 2
        if self.minimum_overlap >= line_width:
            raise ValueError(
                "arc line width (round radius) too small for requested overlap"
            )

        required_arcs = ceil(
            (self.width - self.minimum_overlap) / (line_width - self.minimum_overlap)
        )
        return (self.width - line_width) / (required_arcs - 1)

    def _get_arc_primitives(self) -> list[Arc | Line]:
        line_width = self.round_radius * 2
        step = self._get_step()

        r_inner = self.reference_arc.radius - self.width / 2 + line_width / 2
        r_outer = self.reference_arc.radius + self.width / 2 - line_width / 2

        ref_arc = Arc(shape=self.reference_arc, width=line_width)
        ref_arc.radius = r_outer

        nodes: list[Arc] = []
        r = r_inner
        while r < r_outer:
            new_arc = ref_arc.copy()
            new_arc.radius = r
            nodes.append(new_arc)
            r += step
        nodes.append(ref_arc)

        if self.start_line is not None:
            nodes = self._cut_arcs(nodes, self.start_line, 1)
        if self.end_line is not None:
            nodes = self._cut_arcs(nodes, self.end_line, 0)
        arcs_and_lines: list[Arc | Line] = cast(list[Arc | Line], nodes)
        arcs_and_lines.append(
            Line(start=nodes[0].end, end=nodes[-1].end, width=line_width)
        )
        arcs_and_lines.append(
            Line(start=nodes[0].start, end=nodes[-2].start, width=line_width)
        )

        return arcs_and_lines

    def _cut_arcs(
        self, arcs: list[Arc], line: GeomLine | None, index_to_keep: int
    ) -> list[Arc]:
        if line is None:
            return arcs
        result: list[Arc] = []
        for current_arc in arcs:
            try:
                cut_arcs = split(current_arc, line)
                result.append(
                    shape_to_node(
                        cut_arcs[index_to_keep],
                        layer=current_arc.layer,
                        width=current_arc.width,
                    )  # type: ignore
                )
            except IndexError:
                raise ValueError(
                    "Cutting the arc primitive with one of its endlines "
                    "did not result in the expected number of arcs."
                )
        return result

    def flatten(self) -> list[Node]:
        """Return the leaf nodes to serialize."""
        at = self.reference_arc.mid
        primitives = self._get_arc_primitives()
        for p in primitives:
            p.translate(-at)
        return cast(
            list[Node],
            [
                Pad(
                    number=self.number,
                    type=Pad.TYPE_SMT,
                    shape=Pad.SHAPE_CUSTOM,
                    at=at,
                    size=self.width / 2,
                    layers=self.layers,
                    primitives=cast(list[Shape], primitives),
                )
            ],
        )


class RingPad(Container[Pad | _ArcPadPrimitive | _RingPadPrimitive]):
    """A ring pad."""

    solder_mask_margin: float
    """Solder mask margin of the pad."""
    minimum_overlap: float
    """Minimum arc overlap for paste zones."""
    at: Vector2D
    """Center position of the pad."""
    radius: float
    """Middle radius of the ring."""
    width: float
    """Width of the ring (outer radius - inner radius)."""
    size: float
    """Outside diameter of the pad."""
    is_circle: bool
    """True if the inner diameter is zero, indicating a solid circle pad."""
    number: str | int
    """Number/name of the pad."""
    paste_width: float
    """Width of the solder paste area."""
    paste_center: float
    """Center radius of the solder paste area."""
    num_paste_zones: int
    """Number of paste zones."""
    paste_max_round_radius: float | None
    """Maximum round radius for paste zones. `None` to ignore."""
    paste_round_radius_radio: float
    """Round over radius ratio for paste zones."""
    paste_to_paste_clearance: float
    """Clearance between two paste zones."""
    num_anchor: int
    """Number of anchor pads around the circle."""
    anchor_to_edge_clearance: float
    """Clearance from anchor pad to edge of the ring pad, needed for NPTH center pads."""
    pads: list[Pad | _ArcPadPrimitive | _RingPadPrimitive]
    """List of generated pad primitives."""
    solder_paste_margin: float
    """Solder paste margin of the pad."""

    def __init__(
        self,
        at: Vec2DCompatible,
        size: float,
        inner_diameter: float,
        number: str | int = "",
        num_anchor: int = 1,
        anchor_to_edge_clearance: float = 0.0,
        num_paste_zones: int = 1,
        paste_to_paste_clearance: float | None = None,
        paste_round_radius_radio: float = 0.25,
        paste_max_round_radius: float | None = 0.25,
        solder_paste_margin: float = 0.0,
        paste_outer_diameter: float | None = None,
        paste_inner_diameter: float | None = None,
        solder_mask_margin: float = 0.0,
        minimum_overlap: float = 0.1,
    ) -> None:
        """Create a ring pad.

        Args:
            number: Number/name of the pad.
            at: Center position of the pad.
            inner_diameter: Diameter of the copper free inner zone.
            size: Outside diameter of the pad.
            num_anchor: Number of anchor pads around the circle.
            anchor_to_edge_clearance: Clearance from anchorpad to edge of the ringpad,
                needed for NPTH center pads.
            num_paste_zones: Number of paste zones.
            paste_to_paste_clearance: Clearance between two paste zones,
                needed only if number of paste zones > 1.
                default: 2*abs(solder_paste_margin).
            paste_round_radius_radio: Round over radius ratio.
                resulting radius must be larger than minimum overlap.
            paste_max_round_radius: Maximum round radius.
                Only used if number of paste zones > 1.
                default: 0.25. Set to None to ignore.
            solder_paste_margin: Solder paste margin of the pad.
            paste_outer_diameter: Together with paste inner diameter an alternative for defining the paste area.
            paste_inner_diameter: Together with paste outer diameter an alternative for defining the paste area.
            solder_mask_margin: Solder mask margin of the pad.
            minimum_overlap: Minimum arc overlap.
        """
        super().__init__()
        self.solder_mask_margin = solder_mask_margin
        self.minimum_overlap = minimum_overlap
        self.at = Vector2D(at)
        self._init_size(inner_diameter=inner_diameter, size=size)
        self.number = number
        self._init_paste_settings(
            solder_paste_margin=solder_paste_margin,
            paste_outer_diameter=paste_outer_diameter,
            paste_inner_diameter=paste_inner_diameter,
            num_paste_zones=num_paste_zones,
            paste_max_round_radius=paste_max_round_radius,
            paste_round_radius_radio=paste_round_radius_radio,
            paste_to_paste_clearance=paste_to_paste_clearance,
        )
        self._init_num_anchor(
            num_anchor=num_anchor, anchor_to_edge_clearance=anchor_to_edge_clearance
        )
        self._generate_pads()

    def _init_size(self, inner_diameter: float, size: float) -> None:
        id = inner_diameter
        od = size
        if id >= od:
            raise ValueError("Inner diameter must be smaller than size.")
        self.radius = (id + od) / 4
        self.width = (od - id) / 2
        self.size = od
        self.is_circle = id == 0

    def _init_num_anchor(
        self, num_anchor: int, anchor_to_edge_clearance: float
    ) -> None:
        self.num_anchor = int(num_anchor)
        if self.num_anchor < 1:
            raise ValueError("num_anchor must be a positive integer")
        self.anchor_to_edge_clearance = anchor_to_edge_clearance

    def _init_paste_settings(
        self,
        solder_paste_margin: float,
        paste_outer_diameter: float | None,
        paste_inner_diameter: float | None,
        num_paste_zones: int,
        paste_max_round_radius: float | None,
        paste_round_radius_radio: float,
        paste_to_paste_clearance: float | None,
    ) -> None:
        self.solder_paste_margin = solder_paste_margin
        if paste_outer_diameter is not None and paste_inner_diameter is not None:
            self.paste_width = (paste_outer_diameter - paste_inner_diameter) / 2
            self.paste_center = (paste_outer_diameter + paste_inner_diameter) / 4
        else:
            self.paste_width = self.width + 2 * self.solder_paste_margin
            self.paste_center = self.radius

        self.num_paste_zones = int(num_paste_zones)
        if self.num_paste_zones < 1:
            raise ValueError("num_paste_zones must be a positive integer")
        elif self.num_paste_zones > 1:
            self.paste_max_round_radius = paste_max_round_radius
            self.paste_round_radius_radio = paste_round_radius_radio
            if paste_to_paste_clearance is None:
                self.paste_to_paste_clearance = -self.solder_paste_margin
            else:
                self.paste_to_paste_clearance = paste_to_paste_clearance
            if self.paste_round_radius_radio <= 0.0:
                raise ValueError("Paste_round_radius_radio must be > 0.")
            if (
                self.paste_max_round_radius is not None
                and self.paste_max_round_radius <= 0
            ):
                raise ValueError("Paste_max_round_radius must be > 0.")
            if self.paste_to_paste_clearance <= 0:
                raise ValueError("paste_to_paste_clearance must be > 0")

    def _generate_pads(self) -> None:
        if self.num_paste_zones > 1:
            layers = ["F.Cu", "F.Mask"]
            self._generate_paste_pads()
        else:
            layers = Pad.LAYERS_SMT

        if not self.is_circle:
            self._generate_copper_pads()
        else:
            self.append(
                Pad(
                    number=self.number,
                    type=Pad.TYPE_SMT,
                    shape=Pad.SHAPE_CIRCLE,
                    at=(self.at),
                    size=self.size,
                    layers=layers,
                )
            )

    def _generate_paste_pads(self) -> None:
        ref_angle = 360.0 / self.num_paste_zones

        ref_arc = GeomArc(
            center=self.at, start=self.at + (self.paste_center, 0), angle=ref_angle
        )

        pad = _ArcPadPrimitive(
            number="",
            width=self.paste_width,
            round_radius_ratio=self.paste_round_radius_radio,
            max_round_radius=self.paste_max_round_radius,
            layers=["F.Paste"],
            reference_arc=ref_arc,
            minimum_overlap=self.minimum_overlap,
        )

        w = pad.round_radius * 2
        y = (self.paste_to_paste_clearance + w) / 2

        start_line = GeomLine(start=self.at + (0, y), end=self.at + (self.size, y))
        end_line: GeomLine | None = GeomLine(
            start=self.at + (0, -y), end=self.at + (self.size, -y)
        ).rotate(ref_angle, origin=self.at)

        if self.num_paste_zones == 2:
            end_line = None

        pad.set_limiting_lines(start_line=start_line, end_line=end_line)

        self.append(pad)
        for i in range(1, self.num_paste_zones):
            self.append(pad.copy().rotate(i * ref_angle, origin=self.at))

    def _generate_mask_pads(self) -> None:
        w = self.width + 2 * self.solder_mask_margin
        self.append(
            _RingPadPrimitive(
                number="", at=self.at, width=w, layers=["F.Mask"], radius=self.radius
            )
        )

    def _generate_copper_pads(self) -> None:
        # kicad_mod.append(c)
        layers = ["F.Cu"]
        if self.num_paste_zones == 1:
            if self.solder_paste_margin == 0:
                layers.append("F.Paste")
            else:
                self.append(
                    _RingPadPrimitive(
                        number="",
                        at=self.at,
                        width=self.width + 2 * self.solder_paste_margin,
                        layers=["F.Paste"],
                        radius=self.radius,
                    )
                )

        if self.solder_mask_margin == 0:
            # bug in kicad so any clearance other than 0 needs a workaround
            layers.append("F.Mask")
        else:
            self._generate_mask_pads()
        self.append(
            _RingPadPrimitive(
                number=self.number,
                at=self.at,
                width=self.width,
                layers=layers,
                radius=self.radius,
            )
        )
        if self.width - 2 * self.anchor_to_edge_clearance < 0:
            raise ValueError("Anchor pad width must be > 0")
        a = 360 / self.num_anchor
        pos = Vector2D.from_floats(self.radius, 0.0)
        origin = Vector2D.from_floats(0.0, 0.0)
        for _ in range(1, self.num_anchor):
            pos.rotate(a, origin=origin)
            self.append(
                Pad(
                    number=self.number,
                    type=Pad.TYPE_SMT,
                    shape=Pad.SHAPE_CIRCLE,
                    at=(self.at + pos),
                    size=self.width - (2 * self.anchor_to_edge_clearance),
                    layers=["F.Cu"],
                )
            )

    def flatten(self) -> list[Node]:
        """Return the leaf nodes to serialize."""
        nodes: list[Node] = []
        for child in self._children:
            nodes.extend(child.flatten())
        return nodes

    def as_geom_shape(self, inflation: float = 0.0) -> GeomCircle:
        """Return the geometric rectangle that encloses all pads in the pad array.

        Args:
            inflation: Amount in mm that the returned shape is inflated.

        Returns:
            The inflated contour of the pad array.
        """
        return GeomCircle(
            center=self.at, radius=self.radius + self.width / 2 + inflation
        )
