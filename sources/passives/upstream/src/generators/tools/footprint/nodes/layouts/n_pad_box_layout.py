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

from collections.abc import Iterator

from generators.tools.footprint.drawing_tools import SilkArrowSize
from generators.tools.footprint.drawing_tools_silk import (
    auto_silk_triangle_for_pad_and_box,
)
from generators.tools.pad_factory import (
    DevicePadType,
    PadFactory,
    PadInfo,
    pad_info_to_pads,
)
from KicadModTree import Pad
from KicadModTree.util import courtyard_builder
from kilibs.config import global_config as GC
from kilibs.declarative_defs.packages.two_pad_dimensions import TwoPadDimensions
from kilibs.geom import (
    Direction,
    GeomRectangle,
    Vector2D,
)

from .footprint_layout import FabStyle, FootprintLayout, SilkStyle


class NPadBoxLayout(FootprintLayout[GeomRectangle, Pad]):
    """
    This is one of the most common and general layout idioms - some pads, and a body:

    .. aafig::

                +-----------------------+
        +-------|---+               +---|-------+
        |       |   |               |   |       |
        +-------|---+               +---|-------+
                |                       |
        +-------|---+               +---|-------+
        |       |   |               |   |       |
        +-------|---+               +---|-------+
                +-----------------------+

    The pad layouts are not defined, and are injected by a factory function.
    The body is a rectangle, and the silk is a rectangle around the body, and can
    be configured to be tight to the body, or to extend around the pads.
    """

    def __init__(
        self,
        global_config: GC.GlobalConfig,
        pad_factory: PadFactory,
        body_size: Vector2D,
        body_offset: Vector2D,
        silk_style: SilkStyle,
        is_polarized: bool,
        footprint_name: str,
        body_to_courtyard_clearance: (
            Vector2D | float | GC.GlobalConfig.CourtyardType
        ) = GC.GlobalConfig.CourtyardType.DEFAULT,
        additional_silk_clearance: Vector2D | float = 0.0,
        silk_arrow_direction_if_inside: Direction | None = None,
        silk_arrow_size: SilkArrowSize | None = SilkArrowSize.MEDIUM,
    ) -> None:
        """
        Create a two-pad SMD layout.

        Args:
            global_config: The global config object.
            pad_factory: The pad factory that produces the pads.
            body_size: The nominal size of the body, in mm.
            body_offset: The offset (center position) of the body rectangle.
            silk_style: The style of the silk rectangle to draw around the body.
            is_polarized: Whether the footprint is polarised.
            footprint_name: The footprint name (used for automatic label placement).
            body_to_courtyard_clearance: Clearance to add to the courtyard rectangle
                around the body. This can be different in x and y directions.
            fab_to_silk_extra_clearance: Additional clearance between the body and the
                silk.
            silk_arrow_direction_if_inside: The size of the silk arrow to draw around
                the body, if the footprint is polarized. If `None`, no arrow is drawn.
        """
        self.courtyard_body_offset = GC.GlobalConfig.CourtyardType.DEFAULT
        self.body_size = body_size.copy()
        self.body_offset = body_offset.copy()
        self.silk_style = silk_style
        self.is_polarized = is_polarized
        self.body_to_courtyard_clearance = body_to_courtyard_clearance
        self.additional_silk_clearance = Vector2D(additional_silk_clearance)
        self.silk_arrow_direction_if_inside = silk_arrow_direction_if_inside
        self.silk_arrow_size = silk_arrow_size

        pads: list[Pad] = []

        # Collect pads from the factory and append
        for pad_info in pad_factory.pads():
            pads.extend(pad_info_to_pads(pad_info))

        super().__init__(
            global_config=global_config,
            body_shape=GeomRectangle(center=body_offset, size=body_size),
            pads=pads,
        )

        fab_style = FabStyle.CHAMFER_RECT if is_polarized else FabStyle.BODY_SHAPE
        self._add_courtyard()
        self._add_silk_arrow(silk_style)
        self._add_automatic_fab_outline(fab_style)
        self._add_automatic_silk_outline(silk_style)
        self._add_automatic_labels(footprint_name)

    def _get_silk_clearance(self) -> float | Vector2D:
        """
        Get the additional silk clearance. The amount can be different in x and y.
        """
        return self.additional_silk_clearance

    def _add_silk_arrow(self, silk_style: SilkStyle) -> None:
        # Add the silk arrow - fow now we defer to the auto arrow
        # method, but if we have U-shaped silk, we will need to skip.
        if self.is_polarized and self.silk_arrow_size is not None:
            silk_rect = self._get_uncut_silk_shape(silk_style)
            arrow = auto_silk_triangle_for_pad_and_box(
                self.global_config,
                self.pads[0],
                silk_rect,
                self.silk_arrow_size,
                direction_if_inside=self.silk_arrow_direction_if_inside,
            )
            arrow_poly = arrow.as_polygon(self.global_config.silk_line_width * 2)
            self.additional_silk_keepouts.append(arrow_poly)
            self.append(arrow)

    def _add_courtyard(self) -> None:
        courtyard_rect = self.body_shape.copy()
        # Resolve the courtyard offsets
        if isinstance(self.body_to_courtyard_clearance, GC.GlobalConfig.CourtyardType):
            courtyard_body_offset = self.global_config.get_courtyard_offset(
                self.body_to_courtyard_clearance
            )
        elif isinstance(self.body_to_courtyard_clearance, Vector2D):
            # we'll use the min of the two for the auto courtyard
            courtyard_body_offset = self.body_to_courtyard_clearance.min_val
            # If we have an uneven x/y courtyard offset:
            if not self.body_to_courtyard_clearance.x_y_equal:
                courtyard_rect.size += 2 * (
                    self.body_to_courtyard_clearance - courtyard_body_offset
                )
        else:
            courtyard_body_offset = self.body_to_courtyard_clearance

        # This does the usual courtyard building and handles the pads
        crt_builder = courtyard_builder.CourtyardBuilder.from_node(
            node=self.pads,
            global_config=self.global_config,
            offset_fab=courtyard_body_offset,
            outline=courtyard_rect,
        )
        self.courtyard = crt_builder.node
        self.append(self.courtyard)


class TwoPadSmdPadFactory(PadFactory):
    """A pad factory for the two SMD pads of a two-pad layout.

    The pads are simple round-rectangle SMD pads whose geometry is described by
    a `TwoPadDimensions`.
    """

    def __init__(self, pad_dims: TwoPadDimensions) -> None:
        self._pad_size = Vector2D.from_floats(
            pad_dims.size_inline, pad_dims.size_crosswise
        )
        self._positions = [
            Vector2D.from_floats(
                -pad_dims.spacing_centre / 2, -pad_dims.offset_crosswise / 2
            ),
            Vector2D.from_floats(
                pad_dims.spacing_centre / 2, pad_dims.offset_crosswise / 2
            ),
        ]

    def pads(self) -> Iterator[PadInfo]:
        for i, position in enumerate(self._positions):
            yield PadInfo(
                name=f"{i + 1}",
                position=position,
                size=self._pad_size,
                shape=Pad.SHAPE_ROUNDRECT,
                fp_pad_type=Pad.TYPE_SMT,
                device_pad_type=DevicePadType.SMD_LAND,
            )


def make_layout_for_smd_two_pad_dimensions(
    global_config: GC.GlobalConfig,
    pad_dims: TwoPadDimensions,
    body_size: Vector2D,
    silk_style: SilkStyle,
    is_polarized: bool,
    footprint_name: str,
    silk_arrow_direction_if_inside: Direction | None = None,
    silk_arrow_size: SilkArrowSize | None = SilkArrowSize.MEDIUM,
) -> NPadBoxLayout:
    """
    Create a NPadBoxLayout from the given two-pad dimensions, assuming the
    pads are simple SMD pads.

    This is one of the most common layouts - two-lead chips, SMD inductors
    and so on may all want to use this layout.

    Args:
        global_config: The global config object.
        pad_dims: The dimensions of the pads, including spacing and size. This is
            intepreted with the 'inline' direction being in x and the 'crosswise'
            direction being in y.
        body_size: The nominal size of the body, in mm.
        silk_style: The style of the silk rectangle to draw around the body.
        is_polarized: Whether the footprint is polarised.
        footprint_name: The name of the footprint.
        fab_to_silk_extra_clearance: Additional clearance between the body and the silk.
        silk_arrow_direction_if_inside: The size of the silk arrow to draw around the
            body, if the footprint is polarized. If `None`, no arrow is drawn.

    Returns:
        The layout Node.
    """

    pad_factory = TwoPadSmdPadFactory(pad_dims)

    return NPadBoxLayout(
        global_config=global_config,
        pad_factory=pad_factory,
        body_size=body_size,
        body_offset=Vector2D.zero(),
        silk_style=silk_style,
        is_polarized=is_polarized,
        footprint_name=footprint_name,
        silk_arrow_direction_if_inside=silk_arrow_direction_if_inside,
        silk_arrow_size=silk_arrow_size,
    )
