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

"""Class definition for a chamfered pad grid."""

from __future__ import annotations, division

from collections.abc import Generator, Sequence

from KicadModTree.nodes.base.Pad import Pad
from KicadModTree.nodes.Node import Node
from KicadModTree.nodes.specialized.ChamferedPad import ChamferedPad
from KicadModTree.util.corner_handling import RoundRadiusHandler
from kilibs.geom import CornerSelection, Vector2D
from kilibs.util.param_util import toIntArray


class ChamferSelPadGrid(CornerSelection):
    """A chamfer selection for pad grids."""

    TOP_EDGE = "t"
    """Corners on the top edge are chamfered."""
    RIGHT_EDGE = "r"
    """Corners on the right edge are chamfered."""
    BOTTOM_EDGE = "b"
    """Corners on the bottom edge are chamfered."""
    LEFT_EDGE = "l"
    """Corners on the left edge are chamfered."""

    def __init__(
        self,
        chamfer_select: (
            ChamferSelPadGrid | list[bool] | dict[str, str | bool | int] | int
        ),
    ) -> None:
        """Create a chamfer selectiom for pad grids.

        Args:
            corner_selection: Can be a `list` of 4 `bools`, a `dict` or an `int` with
            the following interpretation:

                * A list of bools do directly set the corners (top left, top right,
                  bottom right, bottom left)
                * A dict with keys (Constants see below)
                * The integer 1 means all corners and edges
                * The integer 0 means no corners, no edges
        """

        # Instance attributes:
        self.top_edge: bool
        """Whether the top edge is selected."""
        self.right_edge: bool
        """Whether the right edge is selected."""
        self.bottom_edge: bool
        """Whether the bottom edge is selected."""
        self.left_edge: bool
        """Whether the left edge is selected."""

        self.top_edge = False
        self.right_edge = False
        self.bottom_edge = False
        self.left_edge = False

        if isinstance(chamfer_select, int):
            if chamfer_select == 1:
                self.select_all()
                CornerSelection.__init__(self, 1)
                return
            elif chamfer_select == 0:
                CornerSelection.__init__(self, 0)
                return
        elif isinstance(chamfer_select, dict):
            CornerSelection.__init__(self, chamfer_select)
            for key in chamfer_select:
                self[key] = bool(chamfer_select[key])
        else:
            for i, value in enumerate(chamfer_select):
                self[i] = bool(value)

    def set_left(self, value: int | bool = 1) -> None:
        """Select left corners."""
        CornerSelection.set_left(self, value)
        self.left_edge = bool(value)

    def set_top(self, value: int | bool = 1) -> None:
        """Select top corners."""
        CornerSelection.set_top(self, value)
        self.top_edge = bool(value)

    def set_right(self, value: int | bool = 1) -> None:
        """Select right corners."""
        CornerSelection.set_right(self, value)
        self.right_edge = bool(value)

    def set_bottom(self, value: int | bool = 1) -> None:
        """Select bottom corners."""
        CornerSelection.set_bottom(self, value)
        self.bottom_edge = bool(value)

    def set_corners(self, value: int | bool = 1) -> None:
        """Select all corners."""
        self.top_left = bool(value)
        self.top_right = bool(value)
        self.bottom_right = bool(value)
        self.bottom_left = bool(value)

    def set_edges(self, value: int | bool = 1) -> None:
        """Select left edges."""
        self.top_edge = bool(value)
        self.right_edge = bool(value)
        self.bottom_edge = bool(value)
        self.left_edge = bool(value)

    def __len__(self) -> int:
        """Number of items."""
        return 8

    def __iter__(self) -> Generator[bool, None, None]:
        """Return an iterator for all its items."""
        for v in CornerSelection.__iter__(self):
            yield v
        yield self.top_edge
        yield self.right_edge
        yield self.bottom_edge
        yield self.left_edge

    def __getitem__(self, item: int | str) -> bool:
        """Get the given item."""
        if item in [4, ChamferSelPadGrid.TOP_EDGE]:
            return self.top_edge
        if item in [5, ChamferSelPadGrid.RIGHT_EDGE]:
            return self.right_edge
        if item in [6, ChamferSelPadGrid.BOTTOM_EDGE]:
            return self.bottom_edge
        if item in [7, ChamferSelPadGrid.LEFT_EDGE]:
            return self.left_edge
        return CornerSelection.__getitem__(self, item)

    def __setitem__(self, item: int | str, value: bool | int | str) -> None:
        """Set the given item."""
        if item in [4, ChamferSelPadGrid.TOP_EDGE]:
            self.top_edge = bool(value)
        elif item in [5, ChamferSelPadGrid.RIGHT_EDGE]:
            self.right_edge = bool(value)
        elif item in [6, ChamferSelPadGrid.BOTTOM_EDGE]:
            self.bottom_edge = bool(value)
        elif item in [7, ChamferSelPadGrid.LEFT_EDGE]:
            self.left_edge = bool(value)
        else:
            CornerSelection.__setitem__(self, item, value)

    def to_dict(self) -> dict[str, bool]:
        """Convert to a dictionary."""
        result = CornerSelection.to_dict(self)
        result.update(
            {
                ChamferSelPadGrid.TOP_EDGE: self.top_edge,
                ChamferSelPadGrid.RIGHT_EDGE: self.right_edge,
                ChamferSelPadGrid.BOTTOM_EDGE: self.bottom_edge,
                ChamferSelPadGrid.LEFT_EDGE: self.left_edge,
            }
        )
        return result


class ChamferedPadGrid(Node):
    """A chamfered pad grid."""

    def __init__(
        self,
        pincount: int | Sequence[int],
        size: Vector2D,
        grid: float | Vector2D,
        round_radius_handler: RoundRadiusHandler,
        layers: list[str],
        chamfer_selection: (
            list[bool] | dict[str, str | bool | int] | int | ChamferSelPadGrid
        ),
        type: str = Pad.TYPE_SMT,
        chamfer_size: Vector2D | float = 0.0,
        number: str | int = "",
        center: Vector2D = Vector2D.zero(),
    ) -> None:
        """Create a chamfered pad grid.

        Args:
            pincount: Pad count in x- and y-direction. If only one float is given, it
                will be used for both directions.
            size: Size of the pads.
            grid: Pad grid in x- and y- direction. If only one float is given, it will
                be used for both directions.
            round_radius_handler: An instance of a `RoundRadiusHandler`.
            layers: Layers which are used for the pad.
            chamfer_selection: Select which corner and edge pads to chamfer.
            type: Type of the pad.
            chamfer_size: Size of the chamfer.
            number: Number or name of the pads.
            center: Center position of the pad grid.
        """

        # Instance attributes:
        self.number: str | int
        """Pad number or name."""
        self.center: Vector2D
        """Center position of the pad grid."""
        self.size: Vector2D
        """Size of the pads."""
        self.type: str
        """Type of the pad."""
        self.layers: list[str]
        """Layers which are used for the pad."""
        self.pincount: list[int]
        """Pad count in x- and y-direction."""
        self.grid: Vector2D
        """Pad grid in x- and y- direction."""
        self.chamfer_selection: ChamferSelPadGrid
        """Select which corner and edge pads to chamfer."""
        self.chamfer_size: Vector2D
        """Size of the chamfer."""
        self.round_radius_handler: RoundRadiusHandler
        """An instance of a `RoundRadiusHandler`."""

        Node.__init__(self)
        self.number = number
        self.center = center
        self.size = size
        self.type = type
        self.layers = layers
        self.pincount = toIntArray(pincount)
        self.grid = Vector2D(grid)
        self.chamfer_selection = ChamferSelPadGrid(chamfer_selection)
        self.chamfer_size = Vector2D(chamfer_size)
        self.round_radius_handler = round_radius_handler

    def get_chamfer_to_avoid_circle(
        self, center: Vector2D, diameter: Vector2D | float, clearance: float = 0.0
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
        relative_center = Vector2D(center) - self.center

        left = -self.grid.x * (self.pincount[0] - 1) / 2
        top = -self.grid.y * (self.pincount[1] - 1) / 2

        nearest_x = left
        nearest_y = top

        min_dist_x = abs(relative_center.x - nearest_x)
        min_dist_y = abs(relative_center.y - nearest_y)

        for i in range(self.pincount[0]):
            x = left + i * self.grid.x
            dx = abs(x - relative_center.x)
            if dx < min_dist_x:
                min_dist_x = dx
                nearest_x = x

        for i in range(self.pincount[1]):
            y = top + i * self.grid.y
            dy = abs(y - relative_center.y)
            if dy < min_dist_y:
                min_dist_y = dy
                nearest_y = y

        self.chamfer_size = ChamferedPad.get_chamfer_to_avoid_circle(
            center=relative_center,
            diameter=diameter,
            clearance=clearance,
            at=Vector2D(nearest_x, nearest_y),
            size=self.size,
        )
        return self.chamfer_size

    def __padCornerSelection(self, idx_x: int, idx_y: int) -> CornerSelection:
        """Get the corner selection of the given element in the chamfered pad grid.

        Args:
            idx_x: The index of the pad in x-direction.
            idx_y: The index of the pad in y-direction.

        Returns:
            The corner selection of the given pad.
        """
        corner = CornerSelection(0)
        if idx_x == 0:
            if idx_y == 0:
                if self.chamfer_selection[ChamferSelPadGrid.TOP_LEFT]:
                    corner[CornerSelection.TOP_LEFT] = True
                if self.chamfer_selection[ChamferSelPadGrid.LEFT_EDGE]:
                    corner[CornerSelection.BOTTOM_LEFT] = True
            if idx_y == self.pincount[1] - 1:
                if self.chamfer_selection[ChamferSelPadGrid.BOTTOM_LEFT]:
                    corner[CornerSelection.BOTTOM_LEFT] = True
                if self.chamfer_selection[ChamferSelPadGrid.LEFT_EDGE]:
                    corner[CornerSelection.TOP_LEFT] = True
            if idx_y != 0 and idx_y != self.pincount[1] - 1:
                if self.chamfer_selection[ChamferSelPadGrid.LEFT_EDGE]:
                    corner.set_left()
        if idx_x == self.pincount[0] - 1:
            if idx_y == 0:
                if self.chamfer_selection[ChamferSelPadGrid.TOP_RIGHT]:
                    corner[CornerSelection.TOP_RIGHT] = True
                if self.chamfer_selection[ChamferSelPadGrid.RIGHT_EDGE]:
                    corner[CornerSelection.BOTTOM_RIGHT] = True
            if idx_y == self.pincount[1] - 1:
                if self.chamfer_selection[ChamferSelPadGrid.BOTTOM_RIGHT]:
                    corner[CornerSelection.BOTTOM_RIGHT] = True
                if self.chamfer_selection[ChamferSelPadGrid.RIGHT_EDGE]:
                    corner[CornerSelection.TOP_RIGHT] = True
            if idx_y != 0 and idx_y != self.pincount[1] - 1:
                if self.chamfer_selection[ChamferSelPadGrid.RIGHT_EDGE]:
                    corner.set_right()
        if idx_x != 0 and idx_x != self.pincount[0] - 1:
            if idx_y == 0:
                if self.chamfer_selection[ChamferSelPadGrid.TOP_EDGE]:
                    corner.set_top()
            if idx_y == self.pincount[1] - 1:
                if self.chamfer_selection[ChamferSelPadGrid.BOTTOM_EDGE]:
                    corner.set_bottom()
        return corner

    def _generate_pads(self) -> list[ChamferedPad]:
        """Generate all the pads of the grid."""
        left = -self.grid.x * (self.pincount[0] - 1) / 2 + self.center.x
        top = -self.grid.y * (self.pincount[1] - 1) / 2 + self.center.y

        pads: list[ChamferedPad] = []
        for idx_x in range(self.pincount[0]):
            x = left + idx_x * self.grid.x
            for idx_y in range(self.pincount[1]):
                y = top + idx_y * self.grid.y
                corner = self.__padCornerSelection(idx_x, idx_y)
                pads.append(
                    ChamferedPad(
                        type=self.type,
                        at=Vector2D.from_floats(x, y),
                        number=self.number,
                        size=self.size,
                        layers=self.layers,
                        chamfer_size=self.chamfer_size,
                        corner_selection=corner,
                        round_radius_handler=self.round_radius_handler,
                    )
                )
        return pads

    def flatten(self) -> list[ChamferedPad]:
        """Return the leaf nodes to serialize."""
        return self._generate_pads()

    def __copy__(self) -> ChamferedPadGrid:
        newone = ChamferedPadGrid.__new__(ChamferedPadGrid)
        newone.__dict__.update(self.__dict__)
        return newone
