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

"""Class definition for a chamfered pad."""

from __future__ import annotations, division

from collections.abc import Iterable
from math import sqrt
from typing import Any

from KicadModTree.nodes.base.Pad import Pad
from KicadModTree.nodes.base.Polygon import Polygon
from KicadModTree.nodes.Node import Node
from KicadModTree.util.corner_handling import RoundRadiusHandler
from kilibs.geom import CornerSelection, Vec2DCompatible, Vector2D
from kilibs.geom.tolerances import TOL_MM


class ChamferedPad(Pad):
    """A chamfered pad."""

    def __init__(
        self,
        size: float | Vector2D,
        at: Vector2D,
        corner_selection: (
            CornerSelection | Iterable[bool] | dict[str, str | bool | int] | int
        ),
        round_radius_handler: RoundRadiusHandler,
        type: str,
        layers: list[str],
        number: int | str = "",
        chamfer_size: float | Vector2D = 0.0,
        offset: Vec2DCompatible = [0, 0],
        rotation: float = 0.0,
        fab_property: Pad.FabProperty | None = None,
        drill: float | Vec2DCompatible | None = None,
        solder_paste_margin_ratio: float = 0,
        solder_paste_margin: float = 0,
        solder_mask_margin: float = 0,
        tuning_properties: Pad.TuningProperties | None = None,
        zone_connection: Pad.ZoneConnection = Pad.ZoneConnection.INHERIT,
        shape_in_zone: str = Pad.SHAPE_IN_ZONE_OUTLINE,
        unconnected_layer_mode: Pad.UnconnectedLayerMode = Pad.UnconnectedLayerMode.KEEP_ALL,
        clearance: float | None = None,
        thermal_bridge_width: float | None = None,
        thermal_bridge_angle: float | None = None,
        thermal_gap: float | None = None,
        anchor_shape: str = Pad.ANCHOR_CIRCLE,
        x_mirror: float | None = None,
        y_mirror: float | None = None,
        **kwargs: dict[str, Any],  # TODO: delete this line
    ) -> None:
        """Create a chamfered pad.

        Args:
            type: Type of the pad.
            layers: Layers which are used for the pad.
            at: Center position of the pad.
            size: Size of the pad.

            number: Number/name of the pad.
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

            chamfer_size: Chamfer size.
            corner_selection: The corner(s) where the chamfer is.
            x_mirror: Mirror x direction around offset "point".
            y_mirror: Mirror y direction around offset "point".
        """

        # Instance attributes:
        self.corner_selection: CornerSelection
        """The corner selection."""
        self.chamfer_size: Vector2D
        """The chamfer size."""

        Node.__init__(self)
        size = Vector2D(size)
        self.corner_selection = CornerSelection(corner_selection)
        self.chamfer_size = Vector2D(chamfer_size)

        # Compute the pad primitive and create the pad:
        if self.chamfer_size.x >= size.x or self.chamfer_size.y >= size.y:
            raise ValueError(
                f"Chamfer size ({self.chamfer_size}) is too large for given pad size "
                f"({size})."
            )

        is_chamfered = False
        if (
            self.corner_selection.is_any_selected()
            and self.chamfer_size[0] > 0
            and self.chamfer_size[1] > 0
        ):
            is_chamfered = True

        radius = round_radius_handler.get_round_radius(min(size))

        if is_chamfered:
            outside = Vector2D(size.x / 2, size.y / 2)

            inside = [
                Vector2D(outside.x, outside.y - self.chamfer_size.y),
                Vector2D(outside.x - self.chamfer_size.x, outside.y),
            ]

            polygon_width = 0.0
            if round_radius_handler.rounding_requested():
                if (
                    abs(self.chamfer_size[0] - self.chamfer_size[1]) > TOL_MM
                ):  # consider rounding errors
                    raise NotImplementedError(
                        "Rounded chamfered pads are only supported for 45 degree chamfers."
                        " Chamfer {}".format(self.chamfer_size)
                    )
                # We prefer the use of rounded rectangle over chamfered pads.
                r_chamfer = self.chamfer_size[0] + sqrt(2) * self.chamfer_size[0] / 2
                if radius >= r_chamfer:
                    is_chamfered = False
                elif radius > 0:
                    shortest_sidlength = min(
                        min(size - self.chamfer_size),
                        self.chamfer_size[0] * sqrt(2),
                    )
                    if radius > shortest_sidlength / 2:
                        radius = shortest_sidlength / 2
                    polygon_width = radius * 2
                    outside -= radius
                    inside[0].y -= radius * (2 / sqrt(2) - 1)
                    inside[0].x -= radius
                    inside[1].x -= radius * (2 / sqrt(2) - 1)
                    inside[1].y -= radius

            if is_chamfered:
                points: list[Vec2DCompatible] = []
                corner_vectors = [
                    Vector2D(-1, -1),
                    Vector2D(1, -1),
                    Vector2D(1, 1),
                    Vector2D(-1, 1),
                ]
                for i in range(4):
                    if self.corner_selection[i]:
                        points.append(corner_vectors[i] * inside[i % 2])
                        points.append(corner_vectors[i] * inside[(i + 1) % 2])
                    else:
                        points.append(corner_vectors[i] * outside)

                primitives = [
                    Polygon(
                        shape=points,
                        width=polygon_width,
                        fill=True,
                        x_mirror=x_mirror,
                        y_mirror=y_mirror,
                    )
                ]
                # TODO make size calculation more resilient
                size = min(size.x, size.y) - max(
                    self.chamfer_size[0], self.chamfer_size[1]
                ) / sqrt(2)
                if size <= 0:
                    raise ValueError(
                        "Anchor pad size calculation failed."
                        "Chamfer size ({}) to large for given pad size ({})".format(
                            size, self.chamfer_size
                        )
                    )
                shape = Pad.SHAPE_CUSTOM
                rr_handler = None
            else:
                shape = Pad.SHAPE_ROUNDRECT
                primitives = None
                rr_handler = round_radius_handler
        else:
            shape = Pad.SHAPE_ROUNDRECT
            primitives = None
            rr_handler = round_radius_handler

        super().__init__(
            type=type,
            layers=layers,
            at=at,
            shape=shape,
            size=size,
            round_radius_handler=rr_handler,
            primitives=primitives,
            number=number,
            offset=offset,
            rotation=rotation,
            fab_property=fab_property,
            drill=drill,
            solder_paste_margin_ratio=solder_paste_margin_ratio,
            solder_paste_margin=solder_paste_margin,
            solder_mask_margin=solder_mask_margin,
            tuning_properties=tuning_properties,
            zone_connection=zone_connection,
            shape_in_zone=shape_in_zone,
            unconnected_layer_mode=unconnected_layer_mode,
            clearance=clearance,
            thermal_bridge_width=thermal_bridge_width,
            thermal_bridge_angle=thermal_bridge_angle,
            thermal_gap=thermal_gap,
            anchor_shape=anchor_shape,
        )

    @staticmethod
    def get_chamfer_to_avoid_circle(
        center: Vector2D,
        at: Vector2D,
        size: Vector2D,
        diameter: float | Vector2D,
        clearance: float = 0.0,
    ) -> Vector2D:
        """Set the chamfer such that the pad avoids a circle located at near corner.

        Args:
            center: The center of the circle to avoid.
            diameter: The diameter of the circle. If Vector2D given only the x-direction
                is used.
            clearance: Additional clearance around the circle.

        Returns:
            The chamfer dimensions such that the pad avoids the given circle.
        """
        relative_center = center - at
        # pad and circle are symmetric so we do not care which corner the
        # reference circle is located at.
        #  -> move it to bottom right to get only positive relative coordinates.
        relative_center.positive()
        d = diameter if isinstance(diameter, float | int) else diameter.x

        # Where should the chamfer be if the center of the reference circle
        # would be in line with the pad edges
        # (meaning exactly at the bottom right corner)
        reference_point = relative_center - sqrt(2) * (clearance + d / 2)
        chamfer_size = size / 2 - reference_point

        # compensate for reference circles not placed exactly at the corner
        edge_to_center = relative_center - size / 2
        chamfer_size -= [edge_to_center.y, edge_to_center.x]
        chamfer_size = Vector2D([x if x > 0 else 0 for x in chamfer_size])
        return chamfer_size

    def __repr__(self) -> str:
        """The string representation of the chamfered pad."""
        return (
            f"ChamferedPad("
            f'number="{self.number}", '
            f"at={self.at}, "
            f"size={self.size}, "
            f"chamfer_size={self.chamfer_size})"
        )
