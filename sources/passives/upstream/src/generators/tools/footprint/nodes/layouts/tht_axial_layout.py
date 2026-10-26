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

from generators.tools.footprint import drawing_tools as DT
from generators.tools.footprint.drawing_tools_silk import (
    draw_silk_triangle_for_pad,
)
from generators.tools.footprint.nodes import pin1_arrow
from KicadModTree import Line, Pad
from KicadModTree.util import courtyard_builder
from kilibs.config import global_config as GC
from kilibs.geom import Direction, GeomLine, GeomRectangle, Vector2D

from .footprint_layout import FabStyle, FootprintLayout, SilkStyle


class ThtAxialLayout(FootprintLayout[GeomRectangle, Pad]):
    """
    A layout node that represents a simple axial leaded device with a number of
    pads on either side of the body, such as:

               +--------------------------+
    +---+      |                          |      +---+
    | o |------|                          |------| o |
    +---+      |                          |      +---+
               +--------------------------+

    Usually there will be 2 pads, but there can be more, e.g. some gas
    discharge tubes have a pin in the middle.
    """

    courtyard_body_offset: float | GC.GlobalConfig.CourtyardType

    def __init__(
        self,
        global_config: GC.GlobalConfig,
        pad_prototype: Pad,
        num_pads: int,
        pitch: float,
        body_size: Vector2D,
        lead_diameter: float,
        footprint_name: str,
        pad_numbers: list[str] | None = None,
        has_pin1_arrow: bool = False,
        adjust_pin1_shape: bool = True,
        total_length: float | None = None,
        shrink_fit_lead_courtyard: bool = True,
    ) -> None:
        """
        Args:
            global_config: The global config object
            pad_prototype: The prototype pad to use for the pads - most pad properties
                will be copied from this pad, but the position and number will be set, and
                the shape may be overridden for pin 1.
            num_pads: The number of pads to create
            pad_pitch: The pitch of the pads in mm
            body_size: The size of the body in mm (width, height)
            lead_diameter: The diameter of the lead in mm
            pad_numbers: A list of pad numbers to use, or None to use the default numbering
            fab_style: The style of pin 1 marking to use.
            adjust_pin1_shape: If True, adjust the shape of the first pad to be a
                round rectangle
            total_length: The total length of the device, including the leads, if this is
                different from the overall pad-to-pad length.
                If None, the total length will be calculated from the pads.
            shrink_fit_lead_courtyard: If True, the courtyard around the lead will be
                shrunk to fit the lead diameter, otherwise it will be the same height as the body
        """
        self.body_size = body_size.copy()
        self.total_length = total_length
        self.num_pads = num_pads
        self.pitch = pitch
        self.pad_prototype = pad_prototype
        self.pad_numbers = pad_numbers
        self.adjust_pin1_shape = adjust_pin1_shape
        self.lead_diameter = lead_diameter
        self.shrink_fit_lead_courtyard = shrink_fit_lead_courtyard

        super().__init__(
            global_config=global_config,
            body_shape=GeomRectangle(center=Vector2D.zero(), size=self.body_size),
            pads=self._get_pads(),
            translation_offset=Vector2D.from_floats((num_pads - 1) * pitch / 2, 0.0),
        )

        fab_style = FabStyle.CHAMFER_RECT if has_pin1_arrow else FabStyle.BODY_SHAPE
        self._add_courtyard()
        self._add_nodes(has_pin1_arrow)
        self._add_automatic_fab_outline(fab_style)
        self._add_automatic_silk_outline(SilkStyle.TIGHT)
        self._add_automatic_labels(footprint_name)

    def _get_pads(self) -> list[Pad]:
        """Create all the pads of this component."""
        pads: list[Pad] = []
        pad_mid_x = (self.num_pads - 1) * self.pitch / 2
        for i in range(self.num_pads):
            shape_override = None
            if (
                i == 0
                and self.adjust_pin1_shape
                and self.pad_prototype.type == Pad.TYPE_THT
            ):
                # Adjust the shape of the first pad if it's a THT pad
                shape_override = Pad.SHAPE_ROUNDRECT
            pad_number = self.pad_numbers[i] if self.pad_numbers else str(i + 1)
            pad = self.pad_prototype.copy_with(
                at=Vector2D(i * self.pitch - pad_mid_x, 0),
                number=pad_number,
                shape=shape_override,
            )
            pads.append(pad)
        return pads

    def _add_nodes(self, has_pin1_arrow: bool) -> None:

        silk_off = self.global_config.silk_fab_offset

        pitch_length = self.pitch * (self.num_pads - 1)
        if self.total_length is not None:
            total_length = self.total_length
        else:
            # Work it out from the pads
            total_length = pitch_length

        # Add the axial lead if longer than the body:
        if total_length > self.body_size.x:
            # Fab lines:
            start = Vector2D.from_floats(-total_length / 2, 0.0)
            end = Vector2D.from_floats(-self.body_size.x / 2, 0.0)
            self.append(Line(start=start, end=end, layer="F.Fab"))
            self.append(Line(start=-end, end=-start, layer="F.Fab"))

            # Silk lines:
            end = Vector2D.from_floats(-self.body_size.x / 2 - silk_off, 0.0)
            lines = [GeomLine(start=start, end=end), GeomLine(start=-end, end=-start)]
            self += DT.makeNodesWithKeepout(
                geom_items=lines,
                keepouts=self._get_silk_keepouts_around_pads(),
                layer="F.SilkS",
                width=self.global_config.silk_line_width,
            )

        # Silk 1 arrow - only used when there's a body chamfer as the other styles
        # either have no pin 1 marking or use another system (e.g. notched body)
        if has_pin1_arrow:
            # Add a pin 1 arrow on the body chamfer

            # Adjust for the stroke width
            silk_arrow_size, silk_arrow_length = DT.getStandardSilkArrowSize(
                DT.SilkArrowSize.LARGE,
                self.global_config.silk_line_width,
            )

            # The pin 1 arrow is at the end of the body rectangle or pad
            # unless it can fit above the pad
            silk_gap = 3 * self.global_config.silk_line_width
            arrow_x = self.body_size.x / 2 - silk_gap

            # If the pad extends past the body, we need to move the arrow
            arrow_x = min(
                arrow_x,
                self.pad_prototype.at.x
                - self.pad_prototype.size.x / 2
                - self.global_config.silk_pad_offset,
            )

            if self.body_size.x < pitch_length - (silk_arrow_size + silk_gap * 2):
                # The pad sticks out more than the lead (usual for a resistor),
                # and there's space for it, so we can put the pin 1 arrow above the pad
                self += draw_silk_triangle_for_pad(
                    pad=self.pad_prototype,
                    arrow_size=DT.SilkArrowSize.LARGE,
                    arrow_direction=Direction.SOUTH,
                    stroke_width=self.global_config.silk_line_width,
                    pad_silk_offset=self.global_config.silk_pad_offset,
                )

            elif total_length > pitch_length + self.pad_prototype.size.x:
                # If the lead sticks out MORE than the outer pad,
                # move the pin 1 arrow up and out of the way of the lead graphic

                self += pin1_arrow.Pin1SilkScreenArrow45Deg(
                    apex_position=Vector2D(arrow_x, silk_gap),
                    angle=Direction.SOUTHEAST,
                    size=silk_arrow_size,
                    layer="F.SilkS",
                    line_width_mm=self.global_config.silk_line_width,
                )

            else:
                # there's no stick-out lead, so we can put the pin 1 arrow
                # at the end of the body rectangle/pad

                self += pin1_arrow.Pin1SilkscreenArrow(
                    apex_position=Vector2D(arrow_x, 0),
                    angle=Direction.EAST,
                    size=silk_arrow_size,
                    length=silk_arrow_length,
                    layer="F.SilkS",
                    line_width_mm=self.global_config.silk_line_width,
                )

    def _add_courtyard(self) -> None:
        # Add the implicit axial lead, which may overrun the pads
        if self.total_length is not None:
            if not self.shrink_fit_lead_courtyard:
                courtyard_height = max(self.lead_diameter, self.body_size.y)
            else:
                courtyard_height = self.lead_diameter

            length = max(self.total_length, self.body_shape.size.x)
            courtyard_body_rect = GeomRectangle(
                center=Vector2D.zero(),
                size=Vector2D.from_floats(length, courtyard_height),
            )
        else:
            courtyard_body_rect = self.body_shape
        self.courtyard = courtyard_builder.CourtyardBuilder.from_node(
            node=self.pads,
            global_config=self.global_config,
            offset_fab=self._courtyard_to_mm(self._get_courtyard_offset_body()),
            offset_pads=self._courtyard_to_mm(self._get_courtyard_offset_pads()),
            outline=courtyard_body_rect,
        ).node
        self.append(self.courtyard)
