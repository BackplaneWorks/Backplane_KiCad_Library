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

"""Pad factories for the grid array (BGA) generator.

Different styles of defining the pads of a grid array are supported via
different PadFactory implementations.
"""

from __future__ import annotations

import itertools
import logging
import math
from collections.abc import Iterator
from typing import TYPE_CHECKING, NamedTuple

from KicadModTree import Pad
from kilibs.config import ipc_rules
from kilibs.geom import Vector2D

from generators.tools.footprint.ipc_pad_size_calculators import ipc_ball_get_pad_size
from generators.tools.pad_factory import PadFactory, PadInfo, DevicePadType

from .config import GridStagger

if TYPE_CHECKING:
    from .spec import GridArraySpec, GridLayout, PinTableEntry


class _GridLayoutPadStyle(NamedTuple):
    """The fully-resolved pad style of one layout.

    The part-level default style is resolved once in `BgaGridPadFactory`, and then
    each layout's overrides are merged over it to produce one `_LayoutPadStyle` per
    layout. This is used to produce the `PadInfo` of each pad in each layout.
    """

    size: Vector2D
    """The pad size in mm."""
    shape: str
    """The pad shape (one of the `Pad.SHAPE_*` strings)."""
    paste_shape: str | None
    """The solder-paste opening shape, or `None` to use `shape`."""
    paste_margin: float
    """The solder-paste margin in mm."""


class PadData(NamedTuple):
    """The name and position of a single pad of a grid layout."""

    name: str
    position: Vector2D


class LayoutData(NamedTuple):
    """The pads of one layout together with the layout that produced them."""

    layout: "GridLayout"
    pad_data_list: list[PadData]


def calculate_stagger(
    layout: "GridLayout",
) -> tuple[float, float, GridStagger]:
    """Calculate the x/y pitch and stagger direction of a layout.

    Args:
        layout: The layout definition.

    Returns:
        The x pitch, the y pitch and the stagger direction (or `None`).
    """
    staggered = layout.staggered
    pitch = layout.pitch
    pitch_x = layout.pitch_x
    pitch_y = layout.pitch_y

    if staggered is not GridStagger.NONE and pitch:
        height = pitch * math.sin(math.radians(60))
        if staggered is GridStagger.X:
            pitch_x = pitch_x or pitch / 2
            pitch_y = pitch_y or height
        elif staggered is GridStagger.Y:
            pitch_x = pitch_x or height
            pitch_y = pitch_y or pitch / 2
    else:
        pitch_x = pitch_x or pitch
        pitch_y = pitch_y or pitch

    if not (pitch_x and pitch_y):
        raise KeyError("Either pitch or both pitch_x and pitch_y must be given.")

    return pitch_x, pitch_y, staggered


def _resolve_row_names(layout: "GridLayout") -> list[str]:
    """Resolve the row names of a layout, applying the layout's overrides."""
    row_names = list(layout.row_names)
    if row_prefix := layout.row_name_prefix:
        row_names = [str(row_prefix) + n for n in row_names]
    if (first_row := layout.first_row) is not None:
        row_names = row_names[row_names.index(first_row) :]
    return row_names[: layout.layout_y]


def _compute_pad_skips(
    layout: "GridLayout", row_names: list[str]
) -> set[str]:
    """Compute the names of the pads that are skipped in a layout.

    A pad can be skipped by an explicit `pad_skips` list, by `row_skips`,
    `area_skips` or by the stagger pattern.
    """
    first_col = layout.first_column
    pad_skips = set(layout.pad_skips)
    _, _, staggered = calculate_stagger(layout)

    for row_start, col_start, row_end, col_end in layout.area_skips:
        rows = row_names[
            row_names.index(row_start.upper()) : row_names.index(row_end.upper()) + 1
        ]
        cols = range(col_start, col_end + 1)
        pad_skips |= {f"{a}{b}" for a, b in itertools.product(rows, cols)}

    for row, skips in zip(row_names, layout.row_skips):
        for skip in skips:
            if isinstance(skip, int):
                pad_skips.add(f"{row}{skip}")
            else:
                pad_skips |= {f"{row}{skip}" for skip in range(*skip)}

    if first_ball := layout.first_ball:
        if staggered is GridStagger.NONE:
            raise ValueError("first_ball only makes sense for staggered layouts.")
        if first_ball not in ("A1", "B1", "A2"):
            raise ValueError('first_ball must be "A1" or "A2".')

    if staggered is not GridStagger.NONE:
        if not first_ball:
            first_ball = "A1"
        skip_even = first_ball == "A1"
        for row_num, row in enumerate(row_names, start=1):
            for col in range(first_col, first_col + layout.layout_x):
                is_even = (row_num + col - first_col) % 2 == 0
                if is_even == skip_even:
                    pad_skips.add(f"{row}{col}")

    return pad_skips


def count_balls_in_layouts(layouts: list["GridLayout"]) -> int:
    """Count the pads of a list of grid layouts without building their positions.

    Args:
        layouts: The layout definitions.

    Returns:
        The total number of pads.
    """
    total = 0
    for layout in layouts:
        row_names = _resolve_row_names(layout)
        pad_skips = _compute_pad_skips(layout, row_names)
        total += layout.layout_x * layout.layout_y - len(pad_skips)
    return total


class BgaGridPadFactory(PadFactory):
    """A pad factory that produces the pads of a grid-array (BGA) part.

    One part can have multiple "grid layouts" (e.g. of different ball pitches),
    and each grid layout usually has multiple pads.

    The pads are defined by the part's grid layouts in the `GridArraySpec`. This
    factory resolves the part-level default pad style and yields one `PadInfo`
    per pad, applying any per-layout overrides.

    This also handles the layout maths.
    """

    def __init__(self, spec: GridArraySpec) -> None:
        """Create the pad factory for the given grid array spec.

        Args:
            spec: The grid array specification.
        """
        self._spec = spec
        self._default_style = _GridLayoutPadStyle(
            size=self._resolve_default_pad_size(spec),
            shape=spec.pad_shape,
            paste_shape=spec.paste_shape,
            paste_margin=spec.paste_margin,
        )

        # Compute the pads of the main and any secondary layouts. The location
        # maths live here, not in the spec.
        self._layout_data_list = [
            self._calculate_pad_names_and_positions_in_layout(layout)
            for layout in spec.layouts
        ]

    def pads(self) -> Iterator[PadInfo]:
        """Yield the resolved `PadInfo` of every pad of the part."""
        for layout in self._layout_data_list:

            style = self._style_for(layout.layout)

            for pad_data in layout.pad_data_list:
                yield PadInfo(
                    name=pad_data.name,
                    position=pad_data.position,
                    size=style.size,
                    shape=style.shape,
                    fp_pad_type=Pad.TYPE_SMT,
                    device_pad_type=DevicePadType.SMD_BALL,
                    fab_property=Pad.FabProperty.BGA,
                    paste_shape=style.paste_shape,
                    paste_margin=style.paste_margin,
                )

    def _calculate_pad_names_and_positions_in_layout(
        self, layout: "GridLayout"
    ) -> LayoutData:
        """Compute the names and positions of the pads of one grid layout.

        Args:
            layout: The layout definition.

        Returns:
            The layout data containing the per-pad names and positions.
        """
        layout_x = layout.layout_x
        layout_y = layout.layout_y
        row_names = _resolve_row_names(layout)
        pad_skips = _compute_pad_skips(layout, row_names)
        first_col = layout.first_column
        pitch_x, pitch_y, _ = calculate_stagger(layout)

        offset_x = layout.offset_x
        offset_y = layout.offset_y
        x_pad_left = -pitch_x * ((layout_x - 1) / 2.0) + offset_x
        y_pad_top = -pitch_y * ((layout_y - 1) / 2.0) + offset_y

        pad_data_list: list[PadData] = []
        for row_num, row in enumerate(row_names):
            row_set = {
                col
                for col in range(first_col, layout_x + first_col)
                if f"{row}{col}" not in pad_skips
            }
            for col in row_set:
                pad_data_list.append(
                    PadData(
                        name=f"{row}{col}",
                        position=Vector2D(
                            x_pad_left + (col - first_col) * pitch_x,
                            y_pad_top + row_num * pitch_y,
                        ),
                    )
                )

        return LayoutData(layout=layout, pad_data_list=pad_data_list)

    def _style_for(self, layout: "GridLayout") -> _GridLayoutPadStyle:
        """Resolve the pad style of one layout by merging its overrides over the
        part-level default."""

        default = self._default_style

        return _GridLayoutPadStyle(
            size=Vector2D(layout.pad_size or default.size),
            shape=layout.pad_shape if layout.pad_shape is not None else default.shape,
            paste_shape=(
                layout.paste_shape if layout.paste_shape is not None else default.paste_shape
            ),
            paste_margin=(
                layout.paste_margin if layout.paste_margin is not None else default.paste_margin
            ),
        )

    @staticmethod
    def _resolve_default_pad_size(spec: GridArraySpec) -> Vector2D:
        """Resolve the part-level default pad size from the spec.

        The size is either set explicitly via `pad_diameter`, or calculated per
        IPC rules from the ball type and diameter.

        Args:
            spec: The grid array specification.

        Returns:
            The default pad size in mm.
        """
        if spec.pad_diameter is not None:
            pad_diameter = spec.pad_diameter
            logging.debug(
                f"Pad size of {spec.id} is set by the footprint definition. "
                "This should only be done for manufacturer-specific footprints."
            )
        else:
            # IPC calculation mode
            ball_diameter = float(spec.ball_diameter)

            ball_rules = ipc_rules.DEFAULT_IPC_BALL_RULES

            pad_diameter = ipc_ball_get_pad_size(
                ball_rules=ball_rules,
                density=spec.ipc_density,
                ball_type=spec.ball_type,
                ball_diameter=ball_diameter,
            )

        return Vector2D(pad_diameter, pad_diameter)


class PadTableFactory(PadFactory):
    """A pad factory that takes its pads from an explicit pin table.

    Each pad carries its full geometry (position, size and solder-mask
    aperture) in the table, in contrast to the grid-based `BgaGridPadFactory`
    which derives them from some declarative layout definition.
    """

    def __init__(self, spec: GridArraySpec) -> None:
        assert spec.pin_table is not None, "Pin table must be present for PadTableFactory"

        self._pin_table = spec.pin_table
        self._flip_x = spec.pin_position_flip_x
        self._flip_y = spec.pin_position_flip_y

    def pads(self) -> Iterator[PadInfo]:
        for entry in self._pin_table:

            pos = entry.position

            if self._flip_x:
                pos = Vector2D(-pos.x, pos.y)
            if self._flip_y:
                pos = Vector2D(pos.x, -pos.y)

            yield PadInfo(
                name=entry.name,
                position=pos,
                size=entry.size,
                shape=Pad.SHAPE_CIRCLE,
                mask_size=entry.mask_size,
                fp_pad_type=Pad.TYPE_SMT,
                device_pad_type=DevicePadType.SMD_BALL,
                fab_property=Pad.FabProperty.BGA,
            )


def make_pad_factory(spec: GridArraySpec) -> PadFactory:
    """Create the pad factory matching the part's pad definition style.

    Parts with an explicit pin table use `PadTableFactory`. All other parts use
    the grid-based `BgaGridPadFactory`.

    Args:
        spec: The grid array specification.

    Returns:
        A pad factory suitable for the spec.
    """
    if spec.pin_table is not None:
        return PadTableFactory(spec)

    return BgaGridPadFactory(spec)
