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

"""Class definition for a pad."""

from __future__ import annotations

import copy
import dataclasses
import enum
import math
from collections.abc import Sequence
from typing import Any

from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.base.Padstack import Padstack
from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.corner_handling import ChamferSizeHandler, RoundRadiusHandler
from kilibs.geom import (
    BoundingBox,
    CornerSelection,
    GeomCircle,
    GeomRectangle,
    GeomShapesClosed,
    Vec2DCompatible,
    Vector2D,
)


class ReferencedPad(Node):
    """A pad class for creating copies of an existing pad with different name and
    location."""

    def __init__(
        self, reference_pad: Pad, number: str | int, at: Vector2D, angle: float = 0.0
    ) -> None:
        """Create a referenced pad.

        Args:
            reference_pad: The pad that is referenced.
            number: The new pad number or name.
            at: The new position of the pad.
            angle: The new angle of the pad.
        """

        # Instance attributes:
        self.reference_pad: Pad
        """The pad that is copied."""
        self.number: str | int
        """The number of the pad (used instead of the number of the referenced pad)."""
        self.at: Vector2D
        """The position of the pad (used instead of the position of the referenced pad)."""
        self.rotation: float
        """The rotation of the pad (used instead of the rotation of the referenced pad)."""

        Node.__init__(self)
        self.reference_pad = reference_pad
        self.number = number
        self.at = at
        self.rotation = angle

    @property
    def size(self) -> Vector2D:
        """The size of the referenced pad."""
        return self.reference_pad.size

    @property
    def offset(self) -> Vector2D:
        """The offset of the referenced pad."""
        return self.reference_pad.offset

    @property
    def shape(self) -> str:
        """The shape of the referenced pad."""
        return self.reference_pad.shape

    def bbox(self) -> BoundingBox:
        """The bounding box of the referenced pad."""
        if self.reference_pad.shape in [
            Pad.SHAPE_RECT,
            Pad.SHAPE_ROUNDRECT,
            Pad.SHAPE_OVAL,
            Pad.SHAPE_CIRCLE,
        ]:
            if self.reference_pad.rotation:
                rect = GeomRectangle(
                    center=self.at,
                    size=self.reference_pad.size,
                    angle=self.reference_pad.rotation,
                )
                return rect.bbox()
            else:
                return BoundingBox(
                    self.at - self.reference_pad.size / 2,
                    self.at + self.reference_pad.size / 2,
                )
        else:
            bounding_box = BoundingBox()
            for primitive in self.reference_pad.primitives:
                primitive_bbox = primitive.bbox()
                if primitive.width is not None:
                    primitive_bbox.inflate(primitive.width / 2.0)
                primitive_bbox.translate(self.at)
                bounding_box.include_bbox(primitive_bbox)
            return bounding_box

    def translate(self, vector: Vector2D) -> ReferencedPad:
        """Move the pad.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated pad.
        """
        self.at += vector
        return self

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> ReferencedPad:
        """Rotate the pad around the given origin.

        Args:
            angle: The rotation angle in degrees.
            origin: The coordinates of the point around which the pad is rotated.
        """
        self.at.rotate(angle=angle, origin=origin)
        self.rotation += angle
        return self

    def get_round_radius(self) -> float:
        """Get the round radius of the pad."""
        return self.reference_pad.get_round_radius()

    def get_top_left_corner_midpoint(self) -> Vector2D:
        """Get the midpoint of the top left corner of the pad.
        When the pad has no radius, this _is_ the corner.
        """
        ref_pad = self.reference_pad
        return ref_pad.get_top_left_corner_midpoint() - ref_pad.at + self.at

    def as_geom_shape(self, inflation: float = 0.0) -> GeomShapesClosed:
        """Return the a closed geometric shape of the contour of the pad. As of now all
        shapes are simplified to their bounding box.

        Args:
            inflation: Amount in mm that the returned shape is inflated.

        Returns:
            The inflated contour of the pad.
        """
        return GeomRectangle(shape=self.bbox()).inflate(inflation)

    def __repr__(self) -> str:
        """The string representation of the referenced pad."""
        return (
            f"ReferencedPad("
            f'number="{self.number}", '
            f"at={self.at}, "
            f"rotation={self.rotation}, "
            f"reference_pad={self.reference_pad})"
        )


class Pad(Node):
    """A pad."""

    TYPE_THT = "thru_hole"
    """Pad type: THT."""
    TYPE_SMT = "smd"
    """Pad type: SMD."""
    TYPE_CONNECT = "connect"
    """Pad type: connect."""
    TYPE_NPTH = "np_thru_hole"
    """Pad type: non plated through hole."""
    _TYPES = [TYPE_THT, TYPE_SMT, TYPE_CONNECT, TYPE_NPTH]
    """List of all supported pad types."""

    SHAPE_CIRCLE = "circle"
    """Pad shape: circle."""
    SHAPE_OVAL = "oval"
    """Pad shape: oval."""
    SHAPE_RECT = "rect"
    """Pad shape: rectangular."""
    SHAPE_ROUNDRECT = "roundrect"
    """Pad shape: rounded rectangular."""
    SHAPE_TRAPEZE = "trapezoid"
    """Pad shape: trapezoid."""
    SHAPE_CUSTOM = "custom"
    """Pad shape: custom."""
    _SHAPES = [
        SHAPE_CIRCLE,
        SHAPE_OVAL,
        SHAPE_RECT,
        SHAPE_ROUNDRECT,
        SHAPE_TRAPEZE,
        SHAPE_CUSTOM,
    ]
    """List of all supported pad shapes."""

    LAYERS_SMT = ["F.Cu", "F.Paste", "F.Mask"]
    """Layer set for SMT."""
    LAYERS_THT = ["*.Cu", "*.Mask"]
    """Layer set for THT."""
    LAYERS_NPTH = ["*.Cu", "*.Mask"]
    """Layer set for NPTH."""
    LAYERS_CONNECT_FRONT = ["F.Cu", "F.Mask"]
    """Layer set for front connect."""
    LAYERS_CONNECT_BACK = ["B.Cu", "B.Mask"]
    """Layer set for back connect."""

    ANCHOR_CIRCLE = "circle"
    """Anchor is a circle."""
    ANCHOR_RECT = "rect"
    """Anchor is a rectangle."""
    _ANCHOR_SHAPE = [ANCHOR_CIRCLE, ANCHOR_RECT]
    """List of supported anchor shapes."""

    SHAPE_IN_ZONE_CONVEX = "convexhull"
    """Shape in zone connect is: convex hull."""
    SHAPE_IN_ZONE_OUTLINE = "outline"
    """Shape in zone connect is: outline."""
    _SHAPE_IN_ZONE = [SHAPE_IN_ZONE_CONVEX, SHAPE_IN_ZONE_OUTLINE]
    """List of supported shape in zone types."""

    class FabProperty(enum.Enum):
        """Type-safe pad fabrication property."""

        # Note that these constants do not necessarily correspond to the strings used in
        # the KiCad file format:
        BGA = "bga"
        """Fab property: BGA."""
        FIDUCIAL_GLOBAL = "fiducial_global"
        """Fab property: global fiducial."""
        FIDUCIAL_LOCAL = "fiducial_local"
        """Fab property: local fiducial."""
        TESTPOINT = "testpoint"
        """Fab property: test point."""
        HEATSINK = "heatsink"
        """Fab property: heatsink."""
        MECHANICAL = "mechanical"
        """Fab property: mechanical."""
        CASTELLATED = "castellated"
        """Fab property: castellated."""

    class ZoneConnection(enum.Enum):
        """Type-safe pad zone connection."""

        # Note that these constants do not necessarily correspond to the values used in
        # the KiCad file format, they can be anything:
        INHERIT = -1
        """For a pad, inherits from footprint, for a footprint, inherits from board."""
        NONE = 0
        """Zone not connected to copper of the same net."""
        THERMAL_RELIEF = 1
        """Zone connected with thermal reliefs to pads of the same net."""
        SOLID = 2
        """Zone connected directly to pads of same nets."""

    class UnconnectedLayerMode(enum.Enum):
        """Behaviour of a Padstack on layers without connection.

        (Should move to Padstack when implemented).
        """

        KEEP_ALL = 0
        """Unconnected layer mode: keep all."""
        REMOVE_ALL = 1
        """Unconnected layer mode: remove all."""
        REMOVE_EXCEPT_START_AND_END = 2
        """Unconnected layer mode: remove all except from start and end."""

    @dataclasses.dataclass
    class TuningProperties:
        """
        Complete decription of a pad's die/tuning properties.
        """

        die_length: float = 0.0
        """
        The die length between the component pad and the physical chip bond pad inside
        the component package (in mm). KiCad uses 0 to mean not specfied.
        """
        # die_delay: float // Will be in v10 (units?)

    def __init__(
        self,
        type: str,
        shape: str,
        layers: list[str],
        at: Vec2DCompatible,
        size: float | Vector2D,
        number: int | str = "",
        offset: Vec2DCompatible = [0, 0],
        rotation: float = 0.0,
        fab_property: FabProperty | None = None,
        drill: float | Vec2DCompatible | None = None,
        solder_paste_margin_ratio: float = 0.0,
        solder_paste_margin: float = 0.0,
        solder_mask_margin: float = 0.0,
        tuning_properties: TuningProperties | None = None,
        round_radius_handler: RoundRadiusHandler | None = None,
        zone_connection: ZoneConnection = ZoneConnection.INHERIT,
        shape_in_zone: str = SHAPE_IN_ZONE_OUTLINE,
        unconnected_layer_mode: UnconnectedLayerMode = UnconnectedLayerMode.KEEP_ALL,
        clearance: float | None = None,
        thermal_bridge_width: float | None = None,
        thermal_bridge_angle: float | None = None,
        thermal_gap: float | None = None,
        anchor_shape: str = ANCHOR_CIRCLE,
        chamfer_corners: list[bool] | dict[str, str | bool | int] | int | None = None,
        maximum_chamfer: float | None = None,
        chamfer_size: float | None = None,
        chamfer_exact: float | None = None,
        chamfer_size_handler: ChamferSizeHandler | None = None,
        primitives: Sequence[Shape] | None = None,
        x_mirror: float | None = None,
        y_mirror: float | None = None,
        **kwargs: dict[str, Any],  # TODO: delete this line
    ) -> None:
        """Create a Pad.

        Args:
            type: Type of the pad.
            shape: Shape of the pad.
            layers: Layers which are used for the pad.
            at: Center position of the pad.
            size: Size of the pad.

            number: Number or name of the pad.
            offset: Offset of the pad.
            rotation: Rotation of the pad.
            fab_property: The pad fabrication property.
            drill: Drill-size of the pad.

            solder_paste_margin_ratio: Solder paste margin ratio of the pad.
            solder_paste_margin: Solder paste margin of the pad.
            solder_mask_margin: Solder mask margin of the pad.

            tuning_properties: Pad tuning properties. None for "undefined", which is the
                KiCad default state.
            round_radius_handler: An instance of the RoundRadiusHandler class. Ignored
                for every shape except round rect.
            zone_connection: Zone connection of the pad.
            shape_in_zone: Shape in zone.
            unconnected_layer_mode: Define how the pad behaves on layers where it is not
                connected.
            clearance: The optional clearance token attribute defines the clearance from
                all copper to the pad. If not set, the footprint clearance is used.
            thermal_bridge_width: The optional thermal_width token attribute defines the
                thermal relief spoke width used for zone connection for the pad. This
                only affects a pad connected to a zone with a thermal relief. If not
                set, the footprint thermal_width setting is used.
            thermal_bridge_angle: The optional thermal bridge angle. If not given this
                defaults to the same default as KiCad (45 for circular pads, 90 for
                everything else).
            thermal_gap: The optional thermal_gap token attribute defines the distance
                from the pad to the zone of the thermal relief connection for the pad.
                This only affects a pad connected to a zone with a thermal relief. If
                not set, the footprint thermal_gap setting is used.
            anchor_shape: Anchor shape.

            chamfer_corners: Chamfer corners.
            maximum_chamfer: Maximum chamfer.
            chamfer_size: Chamfer size.
            chamfer_exact: Chamfer exact size.
            chamfer_size_handler: Chamfer size handler.

            primitives: Polygon primitives used for pads with custom shape.
            x_mirror: Mirror x direction around offset "point".
            y_mirror: Mirror y direction around offset "point".

        Example:
            >>> from KicadModTree import *
            >>> Pad(number=1, type=Pad.TYPE_THT, shape=Pad.SHAPE_RECT,
            ...     at=[0, 0], size=[2, 2], drill=1.2, layers=Pad.LAYERS_THT)
        """

        # Instance attributes:
        self.number: str | int
        """Pad number."""
        self.type: str
        """Pad type."""
        self.shape: str
        """Pad shape."""
        self._fab_property: Pad.FabProperty | None
        """Fab property."""
        self.layers: list[str]
        """Layers of the pad."""
        self.at: Vector2D
        """Position of the pad."""
        self.size: Vector2D
        """Size of the pad."""
        self.offset: Vector2D
        """Offset of the pad."""
        self.rotation: float
        """Rotation angle of the pad in degrees."""
        self.drill: Vector2D | None
        """Drill dimensions in mm."""
        self.solder_paste_margin_ratio: float
        """Solder paste margin ratio."""
        self.solder_paste_margin: float
        """Solder paste margin."""
        self.solder_mask_margin: float
        """Solder mask margin."""
        self.tuning_properties: Pad.TuningProperties | None
        """Tuning properties."""
        self._round_radius_handler: RoundRadiusHandler | None
        """Round radius handler."""
        self.zone_connection: Pad.ZoneConnection
        """Zone connection."""
        self.shape_in_zone: str
        """Shape in zone."""
        self.unconnected_layer_mode: Pad.UnconnectedLayerMode
        """Unconnected layer mode."""
        self.clearance: float | None
        """Optional clearance in mm."""
        self.thermal_bridge_width: float | None
        """Optional thermal bridge width. `None` means inherit from the footprint (like
        KiCad)."""
        self._thermal_bridge_angle: float | None
        """Optional thermal bridge angle."""
        self.thermal_gap: float | None
        """Optional thermal gap. `None` means inherit from the footprint (like
        KiCad)."""
        self.anchor_shape: str
        """Anchor shape."""
        self._chamfer_corners: CornerSelection | None
        """Chamfer corners."""
        self.chamfer_size_handler: ChamferSizeHandler | None
        """Chamfer size handler."""
        self.chamfer_ratio: float | None
        """Chamfer ratio."""
        self.primitives: list[Shape]
        """List of primitives defining the pad shape."""
        self.mirror: list[float | None]
        """Location of the optional mirror."""

        Node.__init__(self)
        self.number = number
        self.type = type
        if self.type not in Pad._TYPES:
            raise ValueError(f"{type} is an invalid type for pads.")
        self._fab_property = Pad.FabProperty(fab_property) if fab_property else None
        self.shape = shape
        if self.shape not in Pad._SHAPES:
            raise ValueError(f"{shape} is an invalid shape for pads")

        self.padstack = Padstack()

        self.at = Vector2D(at)
        self.rotation = rotation
        self.size = Vector2D(size)
        self.offset = Vector2D(offset)
        self.solder_paste_margin_ratio = solder_paste_margin_ratio
        self.solder_paste_margin = solder_paste_margin
        self.solder_mask_margin = solder_mask_margin
        self.zone_connection = zone_connection
        self.shape_in_zone = shape_in_zone
        self.anchor_shape = anchor_shape
        self.clearance = clearance
        self.thermal_bridge_width = thermal_bridge_width
        self.thermal_bridge_angle = thermal_bridge_angle  # TODO: use default_value=90
        self.thermal_gap = thermal_gap
        self.unconnected_layer_mode = unconnected_layer_mode
        self.tuning_properties = tuning_properties
        self.layers = layers
        self._chamfer_corners = None
        self.chamfer_size_handler = None
        self.chamfer_ratio = None
        self.primitives = []
        self._round_radius_handler = round_radius_handler
        self._init_drill(drill)  # requires pad type and offset
        self._init_mirror(x_mirror, y_mirror)

        if self.shape == self.SHAPE_OVAL and self.size.x == self.size.y:
            self.shape = self.SHAPE_CIRCLE

        elif self.shape == Pad.SHAPE_ROUNDRECT:
            if chamfer_size_handler:
                self.chamfer_size_handler = chamfer_size_handler
            else:
                self.chamfer_size_handler = ChamferSizeHandler(
                    maximum_chamfer=maximum_chamfer,
                    chamfer_size=chamfer_size,
                    chamfer_exact=chamfer_exact,
                )
            self.chamfer_ratio = self.chamfer_size_handler.get_chamfer_ratio(
                min(self.size)
            )
            self._chamfer_corners = CornerSelection(chamfer_corners)
            if not self._round_radius_handler:
                raise KeyError("round_radius_handler not declared for roundrect pads")

        elif self.shape == Pad.SHAPE_CUSTOM:
            if self.anchor_shape not in Pad._ANCHOR_SHAPE:
                raise ValueError(f"{anchor_shape} is an illegal anchor shape")
            if self.shape_in_zone not in Pad._SHAPE_IN_ZONE:
                raise ValueError(
                    f"{shape_in_zone} is an illegal specifier for the shape in zone option"
                )
            self.primitives = []
            if primitives:
                for primitive in primitives:
                    self.primitives.append(primitive)
            else:
                raise KeyError("primitives must be declared for custom pads")

    def _init_mirror(self, x_mirror: float | None, y_mirror: float | None) -> None:
        """Initialize the mirror setting:

        Args:
            x_mirror: The location of the x-axis mirror.
            y_mirror: The location of the y-axis mirror.
        """
        self.mirror = [None, None]
        if x_mirror is not None:
            self.mirror[0] = x_mirror
            self.at.x = 2 * x_mirror - self.at.x
            self.offset.x *= -1
        if y_mirror is not None:
            self.mirror[1] = y_mirror
            self.at.y = 2 * y_mirror - self.at.y
            self.offset.y *= -1

    def _init_drill(self, drill: float | Vec2DCompatible | None) -> None:
        """Inititlize the drill settings.

        Args:
            drill: The drill dimensions in mm.
        """
        if self.type in [Pad.TYPE_THT, Pad.TYPE_NPTH]:
            if not drill:
                raise KeyError('drill size required (like "drill=1")')
            self.drill = Vector2D(drill)
        else:
            self.drill = None
            if drill:
                pass  # TODO: throw warning because drill is not supported

    def rotate(
        self,
        angle: float,
        origin: Vector2D = Vector2D.zero(),
    ) -> Pad:
        """Rotate the pad around the given origin.

        Args:
            angle: The rotation angle.
            origin: The coordinates of the point around which the pad is rotated.
        """
        self.at.rotate(angle=angle, origin=origin)
        # The sign of the rotation is historically negative. Why? No idea.
        self.rotation -= angle
        return self

    def translate(self, vector: Vector2D) -> Pad:
        """Move the pad.

        Args:
            vector: The direction and distance in mm.

        Returns:
            The translated pad.
        """
        self.at += vector
        return self

    def bbox(self) -> BoundingBox:
        """Return the bounding box of the pad."""
        if self.shape in [
            Pad.SHAPE_RECT,
            Pad.SHAPE_ROUNDRECT,
            Pad.SHAPE_OVAL,
            Pad.SHAPE_CIRCLE,
        ]:
            if self.rotation:
                rect = GeomRectangle(
                    center=self.at, size=self.size, angle=self.rotation
                )
                return rect.bbox()
            else:
                return BoundingBox(
                    self.at - self.size / 2,
                    self.at + self.size / 2,
                )
        else:
            bounding_box = BoundingBox()
            for primitive in self.primitives:
                primitive_bbox = primitive.bbox()
                if primitive.width is not None:
                    primitive_bbox.inflate(primitive.width / 2.0)
                primitive_bbox.translate(self.at)
                bounding_box.include_bbox(primitive_bbox)
            return bounding_box

    def copy_with(
        self,
        at: Vector2D | None = None,
        shape: str | None = None,
        number: str | int | None = None,
    ) -> Pad:
        """
        Helper functon for a very common operation: copying a pad
        with a new position, shape or number.

        You can add more parameters if you want to, but at some
        point it might be better to create a whole new pad yourself.
        """
        new = copy.deepcopy(self)

        if at is not None:
            new.at = at
        if shape is not None:
            new.shape = shape
        if number is not None:
            new.number = number

        return new

    def get_round_radius(self) -> float:
        """Get the round radius of the pad."""
        if self.shape == Pad.SHAPE_CUSTOM:
            r_max = 0.0
            for p in self.primitives:
                width = p.width if p.width is not None else 0.0
                r = width / 2
                if r > r_max:
                    r_max = r
            return r_max
        if self._round_radius_handler:
            return self._round_radius_handler.get_round_radius(min(self.size))
        else:
            raise RuntimeError(
                "get_round_radius() called but _round_radius_handler is None."
            )

    def get_top_left_corner_midpoint(self) -> Vector2D:
        """Get the midpoint of the top left corner of the pad.
        When the pad has no radius, this _is_ the corner.
        """
        if self.shape == Pad.SHAPE_RECT:
            return self.at - (self.size / 2)
        elif self.shape == Pad.SHAPE_ROUNDRECT:
            tl_corner = self.at - (self.size / 2)
            # Move into the corner slightly down and right to account for the radius
            # being on the inside of the bounding box, not the corner.
            inset = (1 - (math.sqrt(2) / 2)) * self.round_radius
            tl_corner += inset
            return tl_corner
        else:
            return self.bbox().top_left

    def as_geom_shape(self, inflation: float = 0.0) -> GeomRectangle | GeomCircle:
        """Return the a closed geometric shape of the contour of the pad. As of now all
        shapes are simplified to their bounding box.

        Args:
            inflation: Amount in mm that the returned shape is inflated.

        Returns:
            The inflated contour of the pad.
        """
        if self.shape in (Pad.SHAPE_RECT, Pad.SHAPE_ROUNDRECT, Pad.SHAPE_OVAL):
            return GeomRectangle(
                center=self.at, size=self.size + 2 * inflation, angle=self.rotation
            )
        elif self.shape is Pad.SHAPE_CIRCLE:
            return GeomCircle(center=self.at, radius=self.size.x / 2 + inflation)
        else:
            bounding_box = BoundingBox()
            for primitive in self.primitives:
                primitive_bbox = primitive.bbox()
                if primitive.width is not None:
                    primitive_bbox.inflate(primitive.width / 2.0)
                primitive_bbox.translate(self.at)
                bounding_box.include_bbox(primitive_bbox)
            return GeomRectangle(shape=bounding_box).inflate(inflation)

    @property
    def fab_property(self) -> FabProperty | None:
        """The fabrication property of the pad.

        Returns:
            One of the Pad.PROPERTY_* constants, or `None`.
        """
        return self._fab_property

    @property
    def thermal_bridge_angle(self) -> float:
        """The thermal bridge angle.

        KiCad has a slightly weird default system here. Rather than trying to update the
        default when the pad shape changes, internally we store a None and return the
        default value as needed.

        But the Pad always does actually have an angle to report.
        """

        if self._thermal_bridge_angle is not None:
            return self._thermal_bridge_angle

        if self.shape == Pad.SHAPE_CIRCLE or (
            self.shape == Pad.SHAPE_CUSTOM and self.anchor_shape == Pad.SHAPE_CIRCLE
        ):
            return 45

        return 90

    @thermal_bridge_angle.setter
    def thermal_bridge_angle(self, angle: float | None) -> None:
        """The thermal bridge angle.

        Args:
            angle: The thermal bridge angle. `None` means the default for the pad shape.
        """
        self._thermal_bridge_angle = angle

    @property
    def round_radius(self) -> float:
        """The round radius of the pad."""
        return self.get_round_radius()

    @property
    def radius_ratio(self) -> float:
        """The round radius ratio of the pad"""
        # A pad shape that doesn't support round radii will return 0.0
        if not self._round_radius_handler:
            return 0.0
        return self._round_radius_handler.get_radius_ratio(
            min(self.size.x, self.size.y)
        )

    @property
    def chamfer_corners(self) -> CornerSelection | None:
        """The corner selection for chamfers."""
        return self._chamfer_corners

    def __repr__(self) -> str:
        """The string representation of the pad."""
        return (
            f"Pad("
            f'number="{self.number}", '
            f"at={self.at}, "
            f"size={self.size}, "
            f"shape={self.shape})"
        )
