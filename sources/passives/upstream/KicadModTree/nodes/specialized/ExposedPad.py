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
# (C) 2017 by @SchrodingersGat
# (C) 2017 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) 2018 by Rene Poeschl, github @poeschlr
# (C) The KiCad Librarian Team

"""Class definition for an exposed pad."""

from __future__ import division

from copy import copy
from math import sqrt

from KicadModTree.nodes.base.Pad import Pad, ReferencedPad
from KicadModTree.nodes.Container import Container
from KicadModTree.nodes.specialized.ChamferedPadGrid import (
    ChamferedPadGrid,
    ChamferSelPadGrid,
)
from KicadModTree.nodes.specialized.PadArray import PadArray
from KicadModTree.util.corner_handling import RoundRadiusHandler
from kilibs.geom import BoundingBox, GeomRectangle, Vector2D
from kilibs.util.param_util import toIntArray


class ExposedPad(Container[Pad | ReferencedPad]):
    """An exposed pad."""

    VIA_TENTED = "all"
    """Via fully tented."""
    VIA_TENTED_TOP_ONLY = "top"
    """Via only tented on the top."""
    VIA_TENTED_BOTTOM_ONLY = "bottom"
    """Via only tented on the bottom."""
    VIA_NOT_TENTED = "none"
    """Via not tented."""

    def __init__(
        self,
        number: str | int,
        size: Vector2D | float,
        round_radius_handler: RoundRadiusHandler,
        paste_radius_handler: RoundRadiusHandler,
        at: Vector2D = Vector2D.zero(),
        mask_size: Vector2D | float | None = None,
        size_round_base: float = 0.01,
        grid_round_base: float | None = None,
        via_drill: float = 0.3,
        min_annular_ring: float = 0.15,
        via_tented: str = VIA_TENTED,
        via_layout: list[int] = [0, 0],
        via_grid: Vector2D | None = None,
        remove_corner_vias: bool = False,
        paste_avoid_via: bool = False,
        paste_coverage: float = 0.65,
        paste_between_vias: list[int] | None = None,
        paste_rings_outside: list[int] | None = None,
        via_paste_clarance: float = 0.05,
        paste_layout: list[int] | None = None,
        bottom_pad_min_size: Vector2D | float = 0.0,
        bottom_pad_layers: list[str] | None = ["B.Cu"],
    ) -> None:
        """Create an exposed pad.

        Complete with correct paste, mask and via handling.

        Args:
            number: Number or name of the pad.
            size: Size of the pad.
            round_radius_handler: The radius handler for the copper pads.
            paste_radius_handler: The radius handler for the paste pads.
            at: The center of the exposed pad.
            mask_size: Size of the mask cutout (If not given, mask will be part of the
                top pad)
            size_round_base: Base used for rounding calculated sizes. 0.0 means no
                rounding.
            grid_round_base: Base used for rounding calculated grids. 0.0 means no
                rounding.
            via_drill: Via drill diameter.
            min_annular_ring: Annular ring for thermal vias.
            via_tented: Determines which side of the thermal vias is covered in solder
                mask. On the top only vias outside the defined mask area can be covered
                in solder mask. Valid values are VIA_TENTED, VIA_TENTED_TOP_ONLY,
                VIA_TENTED_BOTTOM_ONLY, and VIA_NOT_TENTED.
            via_layout: Thermal via layout specification. Contains the number of vias in
                x- and y-direction. If only a single integer is given, x- and y-
                direction use the same count.
            via_grid: Thermal via grid specification. Grid used for thermal vias in x-
                and y-direction. If only a single integer given, x- and y-direction use
                the same count. If none is given then the via grid will be automatically
                calculated to have them distributed across the top pad.
            remove_corner_vias: Remove vias in the corners of the pad.
            paste_avoid_via: Paste automatically generated to avoid vias.
            paste_coverage: The amount of the mask's free area that is covered with
                paste.
            paste_between_vias: Alternative for `paste_layout` with more control. This
                defines how many pads will be between 4 vias in x- and y-direction.
                If only a single integer is given, x- and y-direction use the same
                count.
            paste_rings_outside: Alternative for `paste_layout` with more control. Defines
                the number of rings outside of the vias in x- and y-direction. If only a
                single integer is given, x- and y-direction use the same count.
            via_paste_clarance: Clearance between paste and via drills. Only used if
                `paste_avoid_via` is set.
            paste_layout: Paste layout specification. The number of pads in x- and y-
                direction. If only a single integer given, x- and y-direction use the
                same count.
            bottom_pad_min_size: Minimum size for bottom pad. Ignored if no bottom pad
                is given.
            bottom_pad_layers: Select layers for the bottom pad. Ignored if no thermal
                vias are added or if `None` (then no bottom pad is added).
        """

        # Instance attributes:
        self.at: Vector2D
        """The center of the exposed pad."""
        self.size_round_base: float
        """Base used for rounding calculated sizes."""
        self.grid_round_base: float
        """Base used for rounding calculated grids."""
        self.round_radius_handler: RoundRadiusHandler
        """The radius handler for the copper pads."""
        self.paste_round_radius_handler: RoundRadiusHandler
        """The radius handler for the paste pads."""
        self.number: str | int
        """ Number or name of the pad."""
        self.size: Vector2D
        """Size of the pad."""
        self.mask_size: Vector2D
        """Size of the mask cutout."""
        self.has_vias: bool
        """Whether the exposed pad has vias."""
        self.via_layout: list[int]
        """The number of vias in x- and y-direction."""
        self.via_drill: float
        """Via drill diameter."""
        self.via_size: float
        """Outer diameter of the vias."""
        self.via_grid: Vector2D
        """Grid used for thermal vias in x- and y-direction."""
        self.via_tented: str
        """which side of the thermal vias is covered in solder mask."""
        self.bottom_pad_layers: list[str] | None
        """ Select layers for the bottom pad."""
        self.add_bottom_pad: bool
        """Whether to add a bottom pad."""
        self.bottom_size: Vector2D
        """Size of the bottom pad."""
        self.paste_avoid_via: bool
        """Whether to place the paste so to avoid the vias."""
        self.paste_reduction: float
        """The length to remove from the border of the maximally sized paste mask openings
        to obtain the desired paste coverage."""
        self.paste_area_size: Vector2D
        """The effective size of the paste areas."""
        self.vias_in_mask: list[int]
        """The number of vias in x- and y-direction."""
        self.via_clarance: float
        """Clearance between paste and via drills."""
        self.paste_between_vias: list[int]
        """How many pads will be between 4 vias in x- and y-direction."""
        self.paste_rings_outside: list[int]
        """The number of rings outside of the vias in x- and y-direction."""
        self.paste_layout: list[int]
        """The number of pads in x- and y-direction."""

        super().__init__()
        self.at = at
        self.size_round_base = size_round_base
        self.grid_round_base = grid_round_base if grid_round_base is not None else 0.01
        self.round_radius_handler = round_radius_handler
        self.paste_round_radius_handler = paste_radius_handler
        self.number = number
        self.size = Vector2D(size)
        if mask_size is None:
            self.mask_size = self.size
        else:
            self.mask_size = Vector2D(mask_size)

        self._init_thermal_vias(
            via_drill=via_drill,
            min_annular_ring=min_annular_ring,
            via_tented=via_tented,
            bottom_pad_min_size=bottom_pad_min_size,
            bottom_pad_layers=bottom_pad_layers,
            via_layout=via_layout,
            via_grid=via_grid,
            remove_corner_vias=remove_corner_vias,
            grid_round_base=grid_round_base if grid_round_base is not None else 0.0,
        )
        self._init_paste(
            paste_avoid_via=paste_avoid_via,
            paste_coverage=paste_coverage,
            paste_between_vias=paste_between_vias,
            paste_rings_outside=paste_rings_outside,
            via_paste_clarance=via_paste_clarance,
            paste_layout=paste_layout,
        )
        self._create_pads()

    def _set_via_layout(self, layout: list[int]) -> bool:
        """Set the via layout and return whether there are vias.

        Args:
            layout: The via layout.
        """
        self.has_vias = True
        self.via_layout = toIntArray(layout, min_value=0)
        if self.via_layout[0] == 0 or self.via_layout[1] == 0:
            self.has_vias = False
        return self.has_vias

    def _init_via_grid(self, via_grid: Vector2D | None, grid_round_base: float) -> None:
        """Initialize the via grid.

        Args:
            via_grid: The unrounded via grid.
            grid_round_base: The base to which the via grid is rounded.
        """
        nx = self.via_layout[0] - 1
        ny = self.via_layout[1] - 1

        if via_grid is not None:
            self.via_grid = Vector2D(via_grid)
        else:
            self.via_grid = Vector2D(
                [
                    (self.size.x - self.via_size) / (nx if nx > 0 else 1),
                    (self.size.y - self.via_size) / (ny if ny > 0 else 1),
                ]
            )
        self.via_grid = self.via_grid.round_to(grid_round_base)

    def _init_thermal_vias(
        self,
        via_drill: float,
        min_annular_ring: float,
        via_tented: str,
        bottom_pad_min_size: Vector2D | float,
        bottom_pad_layers: list[str] | None,
        via_layout: list[int],
        via_grid: Vector2D | None,
        remove_corner_vias: bool,
        grid_round_base: float,
    ) -> None:
        """Initialize the thermal vias.

        Args:
            via_drill: Via drill diameter.
            min_annular_ring: Annular ring for thermal vias.
            via_tented: Determines which side of the thermal vias is covered in solder
                mask. On the top only vias outside the defined mask area can be covered
                in solder mask. Valid values are VIA_TENTED, VIA_TENTED_TOP_ONLY,
                VIA_TENTED_BOTTOM_ONLY, and VIA_NOT_TENTED.
            bottom_pad_min_size: Minimum size for bottom pad. Ignored if no bottom pad
                is given.
            bottom_pad_layers: Select layers for the bottom pad. Ignored if no thermal
                vias are added or if `None` (then no bottom pad is added).
            via_layout: Thermal via layout specification. Contains the number of vias in
                x- and y-direction. If only a single integer is given, x- and y-
                direction use the same count.
            via_grid: Thermal via grid specification. Grid used for thermal vias in x-
                and y-direction. If only a single integer given, x- and y-direction use
                the same count. If none is given then the via grid will be automatically
                calculated to have them distributed across the top pad.
            remove_corner_vias: Remove vias in the corners of the pad.
            grid_round_base: Base used for rounding calculated grids. 0.0 means no
                rounding.
        """
        if not self._set_via_layout(via_layout):
            return

        self.via_drill = via_drill
        self.via_size = self.via_drill + 2 * min_annular_ring
        self._init_via_grid(via_grid, grid_round_base)
        self.via_tented = via_tented

        self.remove_corner_vias = remove_corner_vias
        if (
            self.remove_corner_vias
            and self.via_layout[0] <= 2
            and self.via_layout[1] <= 2
        ):
            raise ValueError("All vias would be deleted by remove_corner_vias option.")

        self.bottom_pad_layers = bottom_pad_layers

        self.add_bottom_pad = True
        if self.bottom_pad_layers is None or len(self.bottom_pad_layers) == 0:
            self.add_bottom_pad = False
        else:
            bottom_pad_min_size = Vector2D(bottom_pad_min_size)
            self.bottom_size = Vector2D(
                [
                    max(
                        (self.via_layout[0] - 1) * self.via_grid.x + self.via_size,
                        bottom_pad_min_size.x,
                    ),
                    max(
                        (self.via_layout[1] - 1) * self.via_grid.y + self.via_size,
                        bottom_pad_min_size.y,
                    ),
                ]
            )

    def _vias_in_mask_count(self, idx: int) -> int:
        """Determine the number of vias within the solder mask area.

        Args:
            idx: Determines if the x- or y-direction is used.
        """
        if (self.via_layout[idx] - 1) * self.via_grid[idx] <= self.paste_area_size[idx]:
            return self.via_layout[idx]
        else:
            return int(self.paste_area_size[idx] // (self.via_grid[idx]))

    def _init_paste_avoiding_vias(
        self,
        paste_between_vias: list[int] | None,
        paste_rings_outside: list[int] | None,
        via_paste_clarance: float,
        paste_layout: list[int] | None,
    ) -> None:
        """Initialize the paste pads while avoiding the vias.

        Args:
            paste_between_vias: Alternative for `paste_layout` with more control. This
                defines how many pads will be between 4 vias in x- and y-direction.
                If only a single integer is given, x- and y-direction use the same
                count.
            paste_rings_outside: Alternative for `paste_layout` with more control.
                Defines the number of rings outside of the vias in x- and y-direction.
                If only a single integer is given, x- and y-direction use the same
                count.
            via_paste_clarance: Clearance between paste and via drills. Only used if
                `paste_avoid_via` is set.
            paste_layout: Paste layout specification. The number of pads in x- and y-
                direction. If only a single integer given, x- and y-direction use the
                same count.
        """
        self.via_clarance = via_paste_clarance

        # check get against none to allow the caller to use None as the sign to ignore these.
        if paste_between_vias is not None or paste_rings_outside is not None:
            if paste_between_vias is None:
                self.paste_between_vias = [0, 0]
            else:
                self.paste_between_vias = toIntArray(paste_between_vias, min_value=0)
            if paste_rings_outside is None:
                paste_rings_outside = [0, 0]
            else:
                self.paste_rings_outside = toIntArray(paste_rings_outside, min_value=0)
        else:
            if paste_layout is None:
                # allows initializing with 'paste_layout=None' to force default value
                paste_layout = [cl - 1 for cl in self.via_layout]
            self.paste_layout = toIntArray(paste_layout)

            # int(floor(paste_count/(vias_in_mask-1)))
            self.paste_between_vias = [
                p // (v - 1) if v > 1 else p // v
                for p, v in zip(self.paste_layout, self.vias_in_mask)
            ]
            inner_count = [
                (v - 1) * p for v, p in zip(self.vias_in_mask, self.paste_between_vias)
            ]
            self.paste_rings_outside = [
                (p - i) // 2 for p, i in zip(self.paste_layout, inner_count)
            ]

    def _init_paste(
        self,
        paste_avoid_via: bool,
        paste_coverage: float,
        paste_between_vias: list[int] | None,
        paste_rings_outside: list[int] | None,
        via_paste_clarance: float,
        paste_layout: list[int] | None,
    ) -> None:
        """Initialize the paste pads.

        Args:
            paste_avoid_via: Paste automatically generated to avoid vias.
            paste_coverage: The amount of the mask's free area that is covered with
                paste.
            paste_between_vias: Alternative for `paste_layout` with more control. This
                defines how many pads will be between 4 vias in x- and y-direction.
                If only a single integer is given, x- and y-direction use the same
                count.
            paste_rings_outside: Alternative for `paste_layout` with more control.
                Defines the number of rings outside of the vias in x- and y-direction.
                If only a single integer is given, x- and y-direction use the same
                count.
            via_paste_clarance: Clearance between paste and via drills. Only used if
                `paste_avoid_via` is set.
            paste_layout: Paste layout specification. The number of pads in x- and y-
                direction. If only a single integer given, x- and y-direction use the
                same count.
        """
        self.paste_avoid_via = paste_avoid_via
        self.paste_reduction = sqrt(paste_coverage)

        self.paste_area_size = Vector2D(
            [min(m, c) for m, c in zip(self.mask_size, self.size)]
        )
        if self.has_vias:
            self.vias_in_mask = [self._vias_in_mask_count(i) for i in range(2)]

        if not self.has_vias or not all(self.vias_in_mask):
            self.paste_avoid_via = False

        if self.has_vias and self.paste_avoid_via:
            self._init_paste_avoiding_vias(
                paste_between_vias=paste_between_vias,
                paste_rings_outside=paste_rings_outside,
                via_paste_clarance=via_paste_clarance,
                paste_layout=paste_layout,
            )
        else:
            if paste_layout is None:
                self.paste_layout = [1, 1]
            else:
                self.paste_layout = toIntArray(paste_layout)

    def _create_paste_ignore_via(self) -> None:
        """Create the paste while ignoring the vias."""
        nx = self.paste_layout[0]
        ny = self.paste_layout[1]

        sx = self.paste_area_size.x
        sy = self.paste_area_size.y

        paste_size = Vector2D(
            [sx * self.paste_reduction / nx, sy * self.paste_reduction / ny]
        ).round_to(self.size_round_base)

        dx = (sx - paste_size.x * nx) / (nx)
        dy = (sy - paste_size.y * ny) / (ny)

        paste_grid = Vector2D(paste_size.x + dx, paste_size.y + dy).round_to(
            self.grid_round_base
        )

        self._children.extend(
            ChamferedPadGrid(
                number="",
                type=Pad.TYPE_SMT,
                center=self.at,
                size=paste_size,
                layers=["F.Paste"],
                chamfer_size=0,
                chamfer_selection=0,
                pincount=self.paste_layout,
                grid=paste_grid,
                round_radius_handler=self.paste_round_radius_handler,
            ).flatten()
        )

    def _create_paste_grids(
        self,
        original: ChamferedPadGrid,
        grid: Vector2D,
        count: list[int],
        center: float | Vector2D,
    ) -> None:
        """Helper function for creating grids of ChamferedPadGrid sections.

        Args:
            original: This instance will be shallow copied to create a grid.
            grid: The spacing between instances.
            count: Determines how many copies will be created in x- and y-direction.
                If only one number is given, both directions use the same count.
            center: Center of the resulting grid of grids.
        """
        top_left = Vector2D(center) - Vector2D(grid) * (Vector2D(count) - 1) / 2
        for idx_x in range(count[0]):
            x = top_left.x + idx_x * grid.x
            for idx_y in range(count[1]):
                y = top_left.y + idx_y * grid.y
                pad = copy(original)
                pad.center = Vector2D(x, y)
                self._children.extend(pad.flatten())

    def _create_paste_avoid_vias_inside(self) -> None:
        """Create the paste pads while avoiding the vias inside."""
        self.inner_grid = self.via_grid / Vector2D(self.paste_between_vias)

        if any(self.paste_rings_outside):
            self.inner_size = (
                self.via_grid / Vector2D(self.paste_between_vias) * self.paste_reduction
            )
        else:
            # inner_grid = mask_size/(inner_count)
            self.inner_size = (
                self.paste_area_size / (self.inner_count) * self.paste_reduction
            )

        corner = ChamferSelPadGrid(0)
        corner.set_corners()
        pad = ChamferedPadGrid(
            number="",
            type=Pad.TYPE_SMT,
            size=self.inner_size,
            layers=["F.Paste"],
            chamfer_size=0,
            chamfer_selection=corner,
            pincount=self.paste_between_vias,
            grid=self.inner_grid,
            round_radius_handler=self.paste_round_radius_handler,
        )

        pad.get_chamfer_to_avoid_circle(
            center=self.via_grid / 2,
            diameter=self.via_drill,
            clearance=self.via_clarance,
        )

        count = [self.vias_in_mask[0] - 1, self.vias_in_mask[1] - 1]
        self._create_paste_grids(
            original=pad, grid=self.via_grid, count=count, center=self.at
        )

    def _create_paste_outside_x(self) -> None:
        """Create the paste pads on the left and right side."""
        corner = ChamferSelPadGrid(
            {ChamferSelPadGrid.TOP_RIGHT: 1, ChamferSelPadGrid.BOTTOM_RIGHT: 1}
        )
        x = self.top_left_via.x - self.ring_size.x / 2
        y = self.at.y - (self.via_layout[1] - 2) / 2 * self.via_grid.y

        pad_side = ChamferedPadGrid(
            number="",
            type=Pad.TYPE_SMT,
            center=Vector2D(x, y),
            size=Vector2D(self.outer_size.x, self.inner_size.y),
            layers=["F.Paste"],
            chamfer_size=0,
            chamfer_selection=corner,
            pincount=[self.paste_rings_outside[0], self.paste_between_vias[1]],
            grid=Vector2D(self.outer_paste_grid.x, self.inner_grid.y),
            round_radius_handler=self.paste_round_radius_handler,
        )

        pad_side.get_chamfer_to_avoid_circle(
            center=self.top_left_via,
            diameter=self.via_drill,
            clearance=self.via_clarance,
        )

        self._create_paste_grids(
            original=pad_side,
            grid=self.via_grid,
            count=[1, self.via_layout[1] - 1],
            center=Vector2D(x, self.at.y),
        )

        corner = ChamferSelPadGrid(
            {ChamferSelPadGrid.TOP_LEFT: 1, ChamferSelPadGrid.BOTTOM_LEFT: 1}
        )
        pad_side.chamfer_selection = corner

        x = 2 * self.at.x - x
        self._create_paste_grids(
            original=pad_side,
            grid=self.via_grid,
            count=[1, self.via_layout[1] - 1],
            center=Vector2D(x, self.at.y),
        )

    def _create_paste_outside_y(self) -> None:
        """Create the paste on the top and bottom side."""
        corner = ChamferSelPadGrid(
            {ChamferSelPadGrid.BOTTOM_LEFT: 1, ChamferSelPadGrid.BOTTOM_RIGHT: 1}
        )

        x = self.at.x - (self.via_layout[0] - 2) / 2 * self.via_grid.x
        y = self.top_left_via.y - self.ring_size.y / 2

        pad_side = ChamferedPadGrid(
            number="",
            type=Pad.TYPE_SMT,
            center=Vector2D.from_floats(x, y),
            size=Vector2D.from_floats(self.inner_size.x, self.outer_size.y),
            layers=["F.Paste"],
            chamfer_size=0,
            chamfer_selection=corner,
            pincount=[self.paste_between_vias[0], self.paste_rings_outside[1]],
            grid=Vector2D.from_floats(self.inner_grid.x, self.outer_paste_grid.y),
            round_radius_handler=self.paste_round_radius_handler,
        )

        pad_side.get_chamfer_to_avoid_circle(
            center=self.top_left_via,
            diameter=self.via_drill,
            clearance=self.via_clarance,
        )

        self._create_paste_grids(
            original=pad_side,
            grid=self.via_grid,
            count=[self.via_layout[0] - 1, 1],
            center=Vector2D.from_floats(self.at.x, y),
        )

        corner = ChamferSelPadGrid(
            {ChamferSelPadGrid.TOP_LEFT: 1, ChamferSelPadGrid.TOP_RIGHT: 1}
        )
        pad_side.chamfer_selection = corner

        y = 2 * self.at.y - y
        self._create_paste_grids(
            original=pad_side,
            grid=self.via_grid,
            count=[self.via_layout[0] - 1, 1],
            center=Vector2D.from_floats(self.at.x, y),
        )

    def _create_paste_outside_corners(self) -> None:
        """Create the corner paste pads."""
        left = self.top_left_via.x - self.ring_size.x / 2
        top = self.top_left_via.y - self.ring_size.y / 2
        corner: list[list[dict[str, str | bool | int]]] = [
            [{ChamferSelPadGrid.BOTTOM_RIGHT: 1}, {ChamferSelPadGrid.TOP_RIGHT: 1}],
            [{ChamferSelPadGrid.BOTTOM_LEFT: 1}, {ChamferSelPadGrid.TOP_LEFT: 1}],
        ]
        pad_side = ChamferedPadGrid(
            number="",
            type=Pad.TYPE_SMT,
            center=Vector2D.from_floats(left, top),
            size=self.outer_size,
            layers=["F.Paste"],
            chamfer_size=0,
            chamfer_selection=0,
            pincount=self.paste_rings_outside,
            grid=self.outer_paste_grid,
            round_radius_handler=self.paste_round_radius_handler,
        )

        pad_side.get_chamfer_to_avoid_circle(
            center=self.top_left_via,
            diameter=self.via_drill,
            clearance=self.via_clarance,
        )

        for idx_x in range(2):
            for idx_y in range(2):
                x = left if idx_x == 0 else 2 * self.at.x - left
                y = top if idx_y == 0 else 2 * self.at.y - top
                pad_side.center = Vector2D(x, y)
                pad_side.chamfer_selection = ChamferSelPadGrid(corner[idx_x][idx_y])
                self._children.extend(copy(pad_side).flatten())

    def _create_paste_avoid_vias_outside(self) -> None:
        """Create the paste pads while avoiding the outer vias."""
        self.ring_size = (
            self.paste_area_size - (Vector2D(self.vias_in_mask) - 1) * self.via_grid
        ) / 2
        self.outer_paste_grid = Vector2D(
            [
                s / p if p != 0 else s
                for s, p in zip(self.ring_size, self.paste_rings_outside)
            ]
        )
        self.outer_size = self.outer_paste_grid * self.paste_reduction

        if self.paste_rings_outside[0] and self.inner_count.y > 0:
            self._create_paste_outside_x()

        if self.paste_rings_outside[1] and self.inner_count.x:
            self._create_paste_outside_y()

        if all(self.paste_rings_outside):
            self._create_paste_outside_corners()

    def _create_paste(self) -> None:
        """Create the paste pads."""
        if self.has_vias:
            self.top_left_via = (
                -(Vector2D(self.vias_in_mask) - 1) * self.via_grid / 2 + self.at
            )
        if self.has_vias and self.paste_avoid_via:
            self.inner_count = (Vector2D(self.vias_in_mask) - 1) * Vector2D(
                self.paste_between_vias
            )

            if all(self.vias_in_mask) and all(self.paste_between_vias):
                self._create_paste_avoid_vias_inside()
            if any(self.paste_rings_outside):
                self._create_paste_avoid_vias_outside()
        else:
            self._create_paste_ignore_via()

    def _create_top_pad(self) -> None:
        """Create the top pad(s)."""
        if self.size == self.mask_size:
            layers_top = ["F.Cu", "F.Mask"]
        else:
            layers_top = ["F.Cu"]
            self.append(
                Pad(
                    number="",
                    at=self.at,
                    size=self.mask_size,
                    shape=Pad.SHAPE_ROUNDRECT,
                    type=Pad.TYPE_SMT,
                    layers=["F.Mask"],
                    round_radius_handler=self.round_radius_handler,
                )
            )

        self.append(
            Pad(
                number=self.number,
                at=self.at,
                size=self.size,
                shape=Pad.SHAPE_ROUNDRECT,
                type=Pad.TYPE_SMT,
                fab_property=Pad.FabProperty.HEATSINK,
                layers=layers_top,
                round_radius_handler=self.round_radius_handler,
                zone_connection=Pad.ZoneConnection.SOLID,
            )
        )

    def _create_vias(self) -> None:
        """Create the thermal vias."""
        via_layers = ["*.Cu"]
        if (
            self.via_tented == ExposedPad.VIA_NOT_TENTED
            or self.via_tented == ExposedPad.VIA_TENTED_BOTTOM_ONLY
        ):
            via_layers.append("F.Mask")
        if (
            self.via_tented == ExposedPad.VIA_NOT_TENTED
            or self.via_tented == ExposedPad.VIA_TENTED_TOP_ONLY
        ):
            via_layers.append("B.Mask")

        cy = -((self.via_layout[1] - 1) * self.via_grid.y) / 2 + self.at.y

        for row in range(self.via_layout[1]):
            vias_in_row = self.via_layout[0]
            if self.remove_corner_vias and (row == 0 or row == self.via_layout[1] - 1):
                vias_in_row = vias_in_row - 2
            if vias_in_row > 0:
                self._children.extend(
                    PadArray(
                        center=[self.at.x, cy],
                        initial=self.number,
                        increment=0,
                        pincount=vias_in_row,
                        x_spacing=self.via_grid.x,
                        size=self.via_size,
                        type=Pad.TYPE_THT,
                        shape=Pad.SHAPE_CIRCLE,
                        fab_property=Pad.FabProperty.HEATSINK,
                        drill=self.via_drill,
                        layers=via_layers,
                    )._children
                )
            cy += self.via_grid.y

        if self.add_bottom_pad and self.bottom_pad_layers:
            self.append(
                Pad(
                    number=self.number,
                    at=self.at,
                    size=self.bottom_size,
                    shape=Pad.SHAPE_ROUNDRECT,
                    type=Pad.TYPE_SMT,
                    fab_property=Pad.FabProperty.HEATSINK,
                    layers=self.bottom_pad_layers,
                    round_radius_handler=self.round_radius_handler,
                    zone_connection=Pad.ZoneConnection.SOLID,
                )
            )

    def _create_pads(self) -> None:
        """Return the leaf nodes to serialize."""
        if self.has_vias:
            self.round_radius_handler.limit_max_radius(self.via_size / 2)
        self._create_top_pad()
        if self.has_vias:
            self._create_vias()
        self._create_paste()

    def bbox(self) -> BoundingBox:
        """Get the bounding box of the pad array."""
        bbox = BoundingBox()
        if not self._children:
            self._create_pads()
        for child in self._children:
            child_bbox = child.bbox()
            bbox.include_bbox(child_bbox)
        return bbox

    def as_geom_shape(self, inflation: float = 0.0) -> GeomRectangle:
        """Return the geometric rectangle that encloses all pads in the exposed pad.

        Args:
            inflation: Amount in mm that the returned shape is inflated.

        Returns:
            The inflated contour of the exposed pad.
        """
        return GeomRectangle(center=self.at, size=self.size + 2 * inflation)

    def flatten(self) -> list[Pad | ReferencedPad]:
        """Return the leaf nodes to serialize."""
        return self._children

    def get_round_radius(self) -> float:
        """Return the round radius."""
        return self.round_radius_handler.get_round_radius(min(self.size))
