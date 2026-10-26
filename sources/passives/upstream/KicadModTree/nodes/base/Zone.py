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
# (C) 2023 by John Beard, <john.j.beard@gmail.com>
# (C) The KiCad Librarian Team

"""Class definitions for zones."""

from __future__ import annotations

from typing import Literal

from KicadModTree.nodes.Node import Node
from kilibs.geom import (
    BoundingBox,
    GeomPolygon,
    GeomRectangle,
    Vec2DCompatible,
    Vector2D,
)


class PadConnection(Node):
    """A pad connection class."""

    THRU_HOLE_ONLY = "thru_hole_only"
    FULL = "full"
    NO = "no"
    THERMAL_RELIEF = "thermal_relief"

    def __init__(self, clearance: float = 0.0, type: str = THERMAL_RELIEF) -> None:
        """Create a pad connection.

        Args:
            clearance: Clearance around the pad.
            type: Type of pad connection.
        """

        # Instance attributes:
        self.clearance: float
        """Clearance around the pad."""
        self.type: str
        """Type of pad connection."""

        if type not in [self.THRU_HOLE_ONLY, self.FULL, self.NO, self.THERMAL_RELIEF]:
            raise ValueError("Invalid pad connection type: %s" % type)
        Node.__init__(self)
        self.clearance = clearance
        self.type = type


class Keepouts(Node):
    """A keepout."""

    ALLOW = False
    DENY = True

    tracks: bool
    """Whether to allow tracks in the keepout area."""
    vias: bool
    """Whether to allow vias in the keepout area."""
    copperpour: bool
    """Whether to allow copperpour in the keepout area."""
    pads: bool
    """Whether to allow pads in the keepout area."""
    footprints: bool
    """Whether to allow footprints in the keepout area."""

    def __init__(
        self,
        tracks: bool = ALLOW,
        vias: bool = ALLOW,
        copperpour: bool = ALLOW,
        pads: bool = ALLOW,
        footprints: bool = ALLOW,
    ) -> None:
        """Create a keepout.

        Args:
            tracks: Whether to allow tracks in the keepout area.
            vias: Whether to allow vias in the keepout area.
            copperpour: Whether to allow copper pour in the keepout area.
            pads: Whether to allow pads in the keepout area.
            footprints: whether to allow footprints in the keepout area.
        """
        Node.__init__(self)
        self.tracks = tracks
        self.vias = vias
        self.copperpour = copperpour
        self.pads = pads
        self.footprints = footprints

    def _get_keepout(self, keepout_name: str, keepout_spec: dict[str, bool]) -> bool:
        """Get the value of a keepout rule. The default is to allow everything."""
        allowed = keepout_spec.get(keepout_name, self.ALLOW)

        valid_allowance = [self.ALLOW, self.DENY]
        if allowed not in valid_allowance:
            raise ValueError(
                f"Keepout rule {keepout_name} must be either '{self.ALLOW}' or '{self.DENY}'."
            )

        return allowed


class Hatch(Node):
    """A hatch class."""

    NONE = "none"
    EDGE = "edge"
    FULL = "full"

    style: str
    """The style of the hatch."""
    pitch: float
    """The pitch of the hatch (determines distance between lines)."""

    def __init__(
        self, style: Literal["none"] | Literal["edge"] | Literal["full"], pitch: float
    ) -> None:
        """Create a hatch definition.

        Args:
            style: The style of the hatch (``Hatch.NONE``, ``Hatch.EDGE`` or
            ``Hatch.FULL``).
            pitch: The pitch of the hatch (determines distance between lines).
        """
        Node.__init__(self)
        self.style = style
        self.pitch = pitch

        valid_styles = [self.NONE, self.EDGE, self.FULL]

        if style not in valid_styles:
            raise ValueError("Invalid hatch style: %s" % style)


class ZoneFill:
    """A zone fill class."""

    FILL_NONE = "none"
    FILL_SOLID = "solid"
    FILL_HATCHED = "hatched"

    SMOOTHING_CHAMFER = "chamfer"
    SMOOTHING_FILLET = "fillet"

    ISLAND_REMOVAL_REMOVE = "remove"
    ISLAND_REMOVAL_FILL = "fill"
    ISLAND_REMOVAL_MINIMUM_AREA = "minimum_area"

    HATCH_SMOOTHING_NONE = "none"
    HATCH_SMOOTHING_FILLET = "fillet"
    HATCH_SMOOTHING_ARC_MINIMUM = "arc_minimum"
    HATCH_SMOOTHING_ARC_MAXIMUM = "arc_maximum"

    HATCH_BORDER_MINIMUM_THICKNESS = "minimum_thickness"
    HATCH_BORDER_HATCH_THICKNESS = "hatch_thickness"

    fill: str
    """Fill style of the zone."""
    thermal_gap: float
    """Thermal gap of the zone."""
    thermal_bridge_width: float
    """Thermal bridge width of the zone."""
    smoothing: str | None
    """Smoothing of the zone."""
    smoothing_radius: float
    """Radius of the smoothing."""
    island_removal_mode: str | None
    """The island removal mode."""
    island_area_min: float | None
    """The minimum area of islands."""
    hatch_thickness: float | None
    """The hatch thickness."""
    hatch_gap: float | None
    """The hatch gap."""
    hatch_orientation: float | None
    """The hatch orientation."""
    hatch_smoothing_level: str | None
    """The hatch smoothing level."""
    hatch_smoothing_value: float | None
    """The hatch smoothing value."""
    hatch_border_algorithm: str | None
    """The hatch border algorithm."""
    hatch_min_hole_area: float | None
    """The hatch minimum hole area."""

    def __init__(
        self,
        fill: str = FILL_SOLID,
        thermal_gap: float = 0.5,
        thermal_bridge_width: float = 0.5,
        smoothing: str | None = None,
        smoothing_radius: float = 0.0,
        island_removal_mode: str | None = None,
        island_area_min: float | None = None,
        hatch_thickness: float | None = None,
        hatch_gap: float | None = None,
        hatch_orientation: float | None = None,
        hatch_smoothing_level: str | None = None,
        hatch_smoothing_value: float | None = None,
        hatch_border_algorithm: str | None = None,
        hatch_min_hole_area: float | None = None,
    ) -> None:
        """Create a zone fill definition.

        Args:
            fill: Fill style of the zone.
            thermal_gap: Thermal gap of the zone.
            thermal_bridge_width: Thermal bridge width of the zone.
            smoothing: Smoothing of the zone.
            smoothing_radius: Radius of the smoothing.
            island_removal_mode: The island removal mode.
            island_area_min: The minimum area of islands.
            hatch_thickness: The hatch thickness.
            hatch_gap: The hatch gap.
            hatch_orientation: The hatch orientation.
            hatch_smoothing_level: The hatch smoothing level.
            hatch_smoothing_value: The hatch smoothing value.
            hatch_border_algorithm: The hatch border algorithm.
            hatch_min_hole_area: The hatch minimum hole area.
        """
        self.fill = fill

        valid_fills = [self.FILL_SOLID, self.FILL_HATCHED, self.FILL_NONE]
        if self.fill not in valid_fills:
            raise ValueError("Invalid fill style: %s" % self.fill)

        self.thermal_gap = thermal_gap
        self.thermal_bridge_width = thermal_bridge_width

        valid_smoothing = [None, self.SMOOTHING_CHAMFER, self.SMOOTHING_FILLET]
        self.smoothing = smoothing
        if self.smoothing not in valid_smoothing:
            raise ValueError("Invalid smoothing: %s" % self.smoothing)

        self.smoothing_radius = smoothing_radius

        self.island_removal_mode = island_removal_mode

        valid_island_removal_modes = [
            None,
            self.ISLAND_REMOVAL_REMOVE,
            self.ISLAND_REMOVAL_FILL,
            self.ISLAND_REMOVAL_MINIMUM_AREA,
        ]
        if self.island_removal_mode not in valid_island_removal_modes:
            raise ValueError(
                "Invalid island removal mode: %s" % self.island_removal_mode
            )

        self.island_area_min = island_area_min

        if (
            self.island_area_min is not None
            and self.island_removal_mode != self.ISLAND_REMOVAL_MINIMUM_AREA
        ):
            raise ValueError(
                "Island area minimum can only be used with minimum_area island removal mode"
            )
        elif (
            self.island_area_min is None
            and self.island_removal_mode == self.ISLAND_REMOVAL_MINIMUM_AREA
        ):
            raise ValueError(
                "Island area minimum must be specified with minimum_area island removal mode"
            )

        self.hatch_thickness = hatch_thickness
        self.hatch_gap = hatch_gap
        self.hatch_orientation = hatch_orientation
        self.hatch_smoothing_level = hatch_smoothing_level

        valid_hatch_smoothing_levels = [
            None,  # Same as NONE?
            self.HATCH_SMOOTHING_NONE,
            self.HATCH_SMOOTHING_FILLET,
            self.HATCH_SMOOTHING_ARC_MINIMUM,
            self.HATCH_SMOOTHING_ARC_MAXIMUM,
        ]
        if self.hatch_smoothing_level not in valid_hatch_smoothing_levels:
            raise ValueError(
                "Invalid hatch smoothing level: %s" % self.hatch_smoothing_level
            )

        self.hatch_smoothing_value = hatch_smoothing_value

        self.hatch_border_algorithm = hatch_border_algorithm

        valid_hatch_border_algorithms = [
            None,
            self.HATCH_BORDER_MINIMUM_THICKNESS,
            self.HATCH_BORDER_HATCH_THICKNESS,
        ]
        if self.hatch_border_algorithm not in valid_hatch_border_algorithms:
            raise ValueError(
                "Invalid hatch border algorithm: %s" % self.hatch_border_algorithm
            )

        self.hatch_min_hole_area = hatch_min_hole_area


class Zone(Node):
    """A zone."""

    shape: GeomPolygon | list[Vec2DCompatible] | GeomRectangle | BoundingBox
    """Shape element defining the polygon of the zone."""
    hatch: Hatch
    """Hatch parameters of the zone."""
    keepout: Keepouts | None
    """Keepout rules for the zone."""
    fill: ZoneFill
    """Zone fill parameters."""
    connect_pads: PadConnection
    """Pad connection rule."""
    layers: list[str]
    """Layers the zone is present on."""
    net: int
    """Net number of the zone."""
    net_name: str
    """Net name of the zone."""
    name: str
    """Human readable name of the zone"""
    filled_areas_thickness: bool
    """Whether the zone line width should be used when determining the fill area."""
    min_thickness: float
    """Minimum thickness of the zone."""
    priority: int | None
    """Priority of the zone."""

    def __init__(
        self,
        shape: GeomPolygon | list[Vec2DCompatible] | GeomRectangle | BoundingBox,
        hatch: Hatch,
        keepouts: Keepouts | None = None,
        fill: ZoneFill | None = None,
        connect_pads: PadConnection = PadConnection(),
        layers: list[str] = [],
        net: int = 0,
        net_name: str = "",
        name: str = "",
        filled_areas_thickness: bool = False,
        min_thickness: float = 0.25,
        priority: int | None = None,
    ) -> None:
        """Create a zone.

        Args:
            shape: Shape element defining the polygon of the zone.
            hatch: Hatch parameters of the zone.
            keepout: Keepout rules for the zone.
            fill: Zone fill parameters.
            connect_pads: Pad connection rule.
            layers: Layers the zone is present on.
            net: Net number of the zone.
            net_name: Net name of the zone.
            name: Human readable name of the zone
            filled_areas_thickness: Whether the zone line width should be used when
                determining the fill area.
            min_thickness: Minimum thickness of the zone.
            priority: Priority of the zone.
        """

        Node.__init__(self)

        self.layers = layers
        self.nodes = GeomPolygon(shape=shape)
        self.net = net
        self.net_name = net_name
        self.name = name
        self.hatch = hatch
        self.filled_areas_thickness = filled_areas_thickness
        self.min_thickness = min_thickness
        self.keepouts = keepouts
        self.connect_pads = connect_pads
        self.priority = priority

        if fill is not None:
            self.fill = fill
        else:
            self.fill = ZoneFill(fill=ZoneFill.FILL_NONE)

    def translate(self, vector: Vector2D) -> Zone:
        """Move the zone.

        Args:
            vector: The distance in mm in the x- and y-direction.

        Returns:
            The translated zone.
        """
        self.nodes.translate(vector)
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Zone:
        """Rotate the zone around a given point.

        Args:
            angle: Rotation angle in degrees.
            origin: Coordinates (in mm) of the point around which to rotate.

        Returns:
            The rotated zone.
        """
        self.nodes.rotate(angle, origin)
        return self
