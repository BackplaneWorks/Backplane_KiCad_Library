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

from itertools import accumulate

from generators.tools.footprint import drawing_tools_silk
from KicadModTree import Pad
from kilibs.config import global_config as GC
from kilibs.geom import Direction, GeomRectangle, Vector2D

from .footprint_layout import CourtyardStyle, FabStyle, FootprintLayout, SilkStyle


class CrossBodyPadLayout(FootprintLayout[GeomRectangle, Pad]):
    """
    A layout node that represents a rectangular device with a number of pads
    that cross the body vertically:

         +------+     +------+     +------+ <--- pads
         |      |     |      |     |      |
    +-------------------------------------------+
    |    |      |     |      |     |      |     |
    |    |      |     |      |     |      |     | <--- body
    |    |      |     |      |     |      |     |
    +-------------------------------------------+
         |      |     |      |     |      |
         +------+     +------+     +------+

    THe pads may or may not extend beyond the body at the ends.

    In the 2-pad case, this is a lot like a 2-pad chip, and either could be
    appropriate (if the device has 2/3-pad variants, it's a good sign).
    """

    courtyard_body_offset: float | GC.GlobalConfig.CourtyardType

    def __init__(
        self,
        global_config: GC.GlobalConfig,
        pad_size: Vector2D | list[Vector2D],
        pitch: float | list[float],
        pad_count: int,
        body_size: Vector2D,
        footprint_name: str,
        pads_body_offset: Vector2D = Vector2D(0, 0),
        silk_style: SilkStyle = SilkStyle.TIGHT,
        has_pin1_arrow: bool = False,
    ) -> None:
        """
        Args:
            global_config: The global config object.
            pad_size: The size of the pads.
            pitch: The pitch of the pads in x/y.
            pad_count: The number of pads.
            body_size: The size of the body.
            footprint_name: The name of the footprint. Used for the automatic label
                placement.
            pads_body_offset: The offset of the pads centre relative to the centre of
                the body.
            silk_style: The style of the silk outline.
            has_pin1_arrow: Draw a polarized silk marker (currently, a U shape).
        """
        self._pad_size = pad_size.copy()
        self._pad_count = pad_count
        self._silk_style = silk_style
        self._has_pin1_arrow = has_pin1_arrow
        self._pad_count = pad_count
        self._pitch = pitch
        self._pads_body_offset = pads_body_offset
        self._silk_keepouts: list[GeomRectangle] = []

        body_shape = GeomRectangle(center=Vector2D.zero(), size=body_size)
        super().__init__(
            global_config=global_config,
            body_shape=body_shape,
            pads=self._get_pads(global_config),
        )

        if silk_style is not SilkStyle.NONE and has_pin1_arrow:
            self._add_silk_arrow(body_shape)
        fab_style = FabStyle.CHAMFER_RECT if has_pin1_arrow else FabStyle.BODY_SHAPE
        self._add_automatic_fab_outline(fab_style)
        self._add_automatic_silk_outline(silk_style)
        self._add_automatic_courtyard(CourtyardStyle.TIGHT)
        self._add_automatic_labels(footprint_name)

    def _get_pads(self, global_config: GC.GlobalConfig) -> list[Pad]:
        """Create all the pads of this component."""

        def _get_pad_size(n: int) -> Vector2D:
            if isinstance(self._pad_size, list):
                assert (
                    len(self._pad_size) == self._pad_count
                ), "pad_size must be a list of the same length as pad_count"
                return self._pad_size[n]
            else:
                return self._pad_size

        def _get_pad_positions() -> list[Vector2D]:
            if isinstance(self._pitch, list):
                assert (
                    len(self._pitch) == self._pad_count - 1
                ), "pad_pitch must be a list of the same length as pad_count - 1"
                pad_pos_x: list[float] = list(accumulate([0.0] + self._pitch))
            else:
                pad_pos_x = [i * self._pitch for i in range(self._pad_count)]
            center_shift_x = self._pads_body_offset.x - pad_pos_x[-1] / 2
            y = self._pads_body_offset.y
            return [Vector2D.from_floats(x + center_shift_x, y) for x in pad_pos_x]

        pads: list[Pad] = []
        for i, pad_pos in enumerate(_get_pad_positions()):
            pad_size = _get_pad_size(i)
            pad = Pad(
                at=pad_pos,
                number=i + 1,
                size=pad_size,
                type=Pad.TYPE_SMT,
                shape=Pad.SHAPE_ROUNDRECT,
                layers=Pad.LAYERS_SMT,
                round_radius_handler=global_config.roundrect_radius_handler,
            )
            pads.append(pad)
        return pads

    def _add_silk_arrow(self, body_rect: GeomRectangle) -> None:
        # If the left pad extends past the body, we'll use an end-on eastward arrow
        # Otherwise, we'll nestle it in the corner of the body and pad.
        pad = self.pads[0]
        left_edge_pad_defined = (pad.at.x - pad.size.x / 2) < (
            body_rect.left + 2 * self.global_config.silk_fab_offset
        )

        if left_edge_pad_defined:
            triangle = drawing_tools_silk.draw_silk_triangle_for_pad(
                pad,
                arrow_direction=Direction.EAST,
                arrow_size=drawing_tools_silk.SilkArrowSize.MEDIUM,
                pad_silk_offset=self.global_config.silk_pad_offset,
                stroke_width=self.global_config.silk_line_width,
            )
            self.append(triangle)
        else:
            triangle = (
                drawing_tools_silk.draw_silk_triangle45_clear_of_fab_hline_and_pad(
                    global_config=self.global_config,
                    pad=pad,
                    arrow_direction=Direction.NORTHEAST,
                    line_y=body_rect.bottom,
                    line_clearance_y=self.global_config.silk_fab_offset,
                    arrow_size=drawing_tools_silk.SilkArrowSize.MEDIUM,
                )
            )
            keepout = triangle.bbox()
            keepout.inflate(self.global_config.silk_line_width * 2.5)
            self.additional_silk_keepouts.append(GeomRectangle(shape=keepout))
            self.append(triangle)
