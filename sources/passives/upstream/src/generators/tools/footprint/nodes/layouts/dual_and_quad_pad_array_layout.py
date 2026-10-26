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

from math import sqrt

from generators.tools.footprint.drawing_tools import applyKeepouts
from generators.tools.footprint.drawing_tools_silk import (
    SilkArrowSize,
    getStandardSilkArrowSize,
)
from generators.tools.footprint.nodes import pin1_arrow
from KicadModTree import (
    ExposedPad,
    PadArray,
    shape_to_node,
)
from KicadModTree.nodes.specialized.PadArray import find_lowest_numbered_pad
from kilibs.config import global_config as GC
from kilibs.geom import (
    BoundingBox,
    Direction,
    GeomRectangle,
    GeomShapesClosed,
    Vector2D,
)
from kilibs.geom.operations import rounding, subtract

from .footprint_layout import CourtyardStyle, FabStyle, FootprintLayout


class DualAndQuadPadArrayLayout(FootprintLayout[GeomRectangle, PadArray | ExposedPad]):
    """This layout is typically used by gullwing and nolead packages:

    Dual pad array:

    .. aafig::

                 /-----------------------+
                /                        |
            +---+---+                +---+---+
            |   |   |                |   |   |
            +---+---+    +------+    +---+---+
                |        |  EP  |        |
            +---+---+    +------+    +---+---+
            |   |   |                |   |   |
            +---+---+                +---+---+
                |                        |
                +------------------------+

    Quad pad array:

    .. aafig::

                       +---+  +---+
                       |   |  |   |
                 /-----+---+--+---+------+
                /      |   |  |   |      |
            +---+---+  +---+  +---+  +---+---+
            |   |   |                |   |   |
            +---+---+   +--------+   +---+---+
                |       |   EP   |       |
            +---+---+   +--------+   +---+---+
            |   |   |                |   |   |
            +---+---+  +---+  +---+  +---+---+
                |      |   |  |   |      |
                +------+---+--+---+------+
                       |   |  |   |
                       +---+  +---+

    The pad arrays and the optional exposed pad are not defined in the
    `DualAndQuadPadArrayLayout`, but injected to the constructor.
    """

    # Class attributes:
    _ARROW_WIDTHS: list[float]
    """List containing the widths of the LARGE, MEDIUM and SMALL arrow without the
    width of the outline."""
    _ARROW_LENGTHS: list[float]
    """List containing the length of the LARGE, MEDIUM and SMALL arrow without the
    width of the outline."""
    _ROUND_GRID = 0.01
    """Grid to which the arrow vertices are round."""
    _class_attributes_initialized = False
    """Variable used to check whether the class attributes are initialized or not."""

    def __init__(
        self,
        global_config: GC.GlobalConfig,
        courtyard_offset_body: float,
        courtyard_offset_pads: float,
        pad_arrays: list[PadArray],
        exposed_pad: ExposedPad | None,
        body_size: Vector2D,
        footprint_name: str,
    ) -> None:
        """
        Create a two-pad SMD layout.

        Args:
            global_config: The global config object.
            courtyard_offset_body: The clearance between the courtyard and the component
                body.
            courtyard_offset_pads: The clearance between the courtyard and the pads.
            pad_arrays: The pads.
            exposed_pad: The optional exposed pad.
            body_size: The nominal size of the body, in mm.
            footprint_name: The name of the footprint.
        """
        # TODO: Once GlobalConfig is a singleton this won't be necessary anymore:
        DualAndQuadPadArrayLayout._init_class_attributes(global_config.silk_line_width)

        # Instance attributes:
        self.pad_arrays: list[PadArray]
        """The list of the 2 or 4 pad arrays of the footprint."""
        self.exposed_pad: ExposedPad | None
        """Optional exposed pad."""
        self.body_size: Vector2D
        """The nominal size of the rectangular body, in mm."""
        self.courtyard_offset_body: float
        """Offset between the courtyard and the component body."""
        self.courtyard_offset_pads: float
        """Offset between the courtyard and the pads."""

        self.pad_arrays = pad_arrays
        self.exposed_pad = exposed_pad
        self.body_size = body_size
        self.courtyard_offset_body = courtyard_offset_body
        self.courtyard_offset_pads = courtyard_offset_pads

        super().__init__(
            global_config=global_config,
            pads=pad_arrays + [exposed_pad] if exposed_pad is not None else pad_arrays,
            body_shape=GeomRectangle(center=Vector2D.zero(), size=self.body_size),
        )

        self._add_automatic_fab_outline(FabStyle.CHAMFER_RECT)
        self._add_automatic_courtyard(CourtyardStyle.TIGHT)
        self._add_automatic_labels(footprint_name)
        self._create_silk()

    def _get_courtyard_offset_pads(self) -> float | GC.GlobalConfig.CourtyardType:
        """Return the courtyard offset for the pads."""
        return self.courtyard_offset_pads

    def _get_courtyard_offset_body(self) -> float | GC.GlobalConfig.CourtyardType:
        """Return the courtyard offset from the body."""
        return self.courtyard_offset_body

    def _get_bounding_box_of_vertical_pad_arrays(self) -> BoundingBox:
        """Get the bounding box of the vertical pad arrays."""
        bb = BoundingBox()
        for pad_array in self.pad_arrays:
            if pad_array.spacing.y:
                bb.include_bbox(pad_array.bbox())
        return bb

    def _get_bounding_box_of_horizontal_pad_arrays(self) -> BoundingBox:
        """Get the bounding box of the horizontal pad arrays."""
        bb = BoundingBox()
        for pad_array in self.pad_arrays:
            if pad_array.spacing.x:
                bb.include_bbox(pad_array.bbox())
        return bb

    def _get_bounding_box_of_pad_arrays(self) -> BoundingBox:
        """Get the bounding box of the pad arrays."""
        bb = BoundingBox()
        for pad_array in self.pad_arrays:
            bb.include_bbox(pad_array.bbox())
        return bb

    def _get_bounding_box_of_component(self) -> BoundingBox:
        """Get the bounding box of the component."""
        bb = self._get_bounding_box_of_pad_arrays()
        if self.exposed_pad:
            bb.include_bbox(self.exposed_pad.bbox())
        size = self.body_size
        bb.include_point(Vector2D.from_floats(-size.x / 2, -size.y / 2))
        bb.include_point(Vector2D.from_floats(size.x / 2, size.y / 2))
        return bb

    def _create_arrow(
        self,
    ) -> pin1_arrow.Pin1SilkscreenArrow | pin1_arrow.Pin1SilkScreenArrow45Deg:
        silk_line_width = self.global_config.silk_line_width
        silk_pad_offset = self.global_config.silk_pad_clearance + silk_line_width / 2
        silk_fab_offset = self.global_config.silk_fab_offset
        body_x_half = self.body_size.x / 2
        body_y_half = self.body_size.y / 2

        # Find the pin with the lowest pad number (pin1):
        idx_array, idx_pad = find_lowest_numbered_pad(self.pad_arrays)
        pads = self.pad_arrays[idx_array].children
        pad1 = pads[idx_pad]
        pad1_bbox = pad1.bbox()

        # Find the neighboring pads of pad1 in the same pad array and get their bboxes:
        pad1_neighbours_bboxes: list[BoundingBox] = []
        if idx_pad > 0:
            pad1_neighbours_bboxes.append(pads[idx_pad - 1].bbox())
        if idx_pad < len(pads) - 1:
            pad1_neighbours_bboxes.append(pads[idx_pad + 1].bbox())

        # Get the distance between pad1 and the courtyard outline:
        assert self.courtyard, "Create the courtyard first."
        crt_bbox = self.courtyard.bbox()
        clearance = (
            silk_pad_offset - 1.5 * silk_line_width
        )  # Allow arrow to stand out by 1.5*slw
        space_left_of_p1 = pad1_bbox.left - crt_bbox.left - clearance
        space_right_of_p1 = crt_bbox.right - pad1_bbox.right - clearance
        space_top_of_p1 = pad1_bbox.top - crt_bbox.top - clearance
        space_bot_of_p1 = crt_bbox.bottom - pad1_bbox.bottom - clearance

        # Get the distance between pad1 and its neighboring pads:
        clearance = 2 * silk_pad_offset + silk_line_width
        for bbox in pad1_neighbours_bboxes:
            if bbox.left > pad1_bbox.right:
                space_right_of_p1 = bbox.left - pad1_bbox.right - clearance
            elif bbox.right < pad1_bbox.left:
                space_left_of_p1 = pad1_bbox.left - bbox.right - clearance
            elif bbox.top > pad1_bbox.bottom:
                space_bot_of_p1 = bbox.top - pad1_bbox.bottom - clearance
            elif bbox.bottom < pad1_bbox.top:
                space_top_of_p1 = pad1_bbox.top - bbox.bottom - clearance

        # Limit the calculated spaces by the component body:
        if -body_y_half < pad1_bbox.center.y < body_y_half:
            if pad1_bbox.left < 0.0:
                space_right_of_p1 = 0.0
            elif pad1_bbox.right > 0.0:
                space_left_of_p1 = 0.0
        if -body_x_half < pad1_bbox.center.x < body_x_half:
            if pad1_bbox.top < -body_y_half:
                space_bot_of_p1 = 0.0
            elif pad1_bbox.bottom > body_y_half:
                space_top_of_p1 = 0.0

        # For small components, limit the size of the arrow:
        min_body_size = self.body_size.min_val
        if min_body_size > 3.0:  # 3.0 < min_body_size
            max_arrow_range = [0, 1]  # LARGE, MEDIUM
            preferred_size_idx = 1
        elif min_body_size > 2.0:  # 2.0 < min_body_size <= 3.0
            max_arrow_range = [1]  # MEDIUM
            preferred_size_idx = 1
        else:  # 2.0 <= min_body_size
            max_arrow_range = [1, 2]  # MEDIUM, SMALL
            preferred_size_idx = 2

        # If there is more space on the top than on the left, we test if the arrow can
        # be placed on top of the pad without sticking out on the left or on the top:
        #
        # Case #1:
        #
        #    __  --------------  <- silk
        #    \/  +------------+  <- body
        #    =====            ===== <- pad
        #        |            |
        #    =====            =====
        #        +------------+
        #        -------------- <- silk
        #
        # Case #2:
        #
        #        --------------  <- silk
        #        +------------+  <- body
        #    =====            ===== <- pad
        #     /\ |            |
        #     ¯¯ |            |
        #    =====            =====
        #        +------------+
        #        -------------- <- silk
        #
        max_space_horizontal_of_p1 = max(space_left_of_p1, space_right_of_p1)
        max_space_vertical_of_p1 = max(space_top_of_p1, space_bot_of_p1)
        if max_space_vertical_of_p1 >= max_space_horizontal_of_p1:
            if space_top_of_p1 >= space_bot_of_p1:  # Case #1:
                direction = Direction.SOUTH
                apex_y = pad1_bbox.top - silk_pad_offset
                apex_y = rounding.round_to_grid_down(apex_y, self._ROUND_GRID)
                space_on_y_axis = space_top_of_p1
            else:
                direction = Direction.NORTH  # Case #2:
                apex_y = pad1_bbox.bottom + silk_pad_offset
                apex_y = rounding.round_to_grid_up(apex_y, self._ROUND_GRID)
                space_on_y_axis = space_bot_of_p1
            space_on_x_axis = abs(pad1_bbox.left + body_x_half)
            # If pad 1 is very close to the top of the component outline, we can place
            # the arrow closer to the right (i.e. it does not have to be on the left
            # side of the component outline):
            if apex_y <= -body_y_half - silk_fab_offset:
                space_on_x_axis = max(space_on_x_axis, pad1_bbox.right - pad1_bbox.left)
                min_arrow_x_position = pad1_bbox.right
                clearance_to_fab = 0.0
            else:
                # Ideally allow sufficient clearance between the outline of the
                # component on the silk layer and the arrow:
                clearance_to_fab = 2.5 * silk_line_width
                min_arrow_x_position = -body_x_half - silk_fab_offset - clearance_to_fab
            # Find the south/north-pointing arrow that fits:
            for i in max_arrow_range:
                arrow_width = DualAndQuadPadArrayLayout._ARROW_WIDTHS[i]
                arrow_length = DualAndQuadPadArrayLayout._ARROW_LENGTHS[i]
                fits_on_x = space_on_x_axis >= arrow_width
                fits_on_y = space_on_y_axis >= arrow_length
                if fits_on_y and fits_on_x:
                    # Place the arrow as close as possible to the pad center
                    apex_x = min(pad1.at.x, min_arrow_x_position - arrow_width / 2)
                    # If the arrow apex is on the left of the pad, try moving it further
                    # to the right:
                    if apex_x < pad1_bbox.left + silk_line_width:
                        apex_x += max(
                            0.0,
                            min(
                                clearance_to_fab,
                                pad1_bbox.left - apex_x + silk_line_width,
                            ),
                        )
                    # If the arrow apex is above the body (on the right side of the
                    # body's left vertical outline), then we move it closer to the left
                    # in order to reduce the risk of splitting the top horizontal line
                    # of the body's silkscreen outline:
                    elif apex_x > -body_x_half:
                        apex_x = min(
                            apex_x, -body_x_half - silk_line_width + arrow_width / 2
                        )
                    apex_x = rounding.round_to_grid_down(apex_x, self._ROUND_GRID)
                    arrow_apex = Vector2D.from_floats(apex_x, apex_y)
                    return pin1_arrow.Pin1SilkscreenArrow(
                        apex_position=arrow_apex,
                        angle=direction,
                        size=arrow_width,
                        length=arrow_length,
                        layer="F.SilkS",
                        line_width_mm=silk_line_width,
                    )

        # If there is more space on the top than on the left, test if the arrow can be
        # placed on left of the pad without sticking out too much on the top or left:
        #
        # Case #3:
        #
        #         |> +-+  +-+
        #            | |  | |
        #       | +--+-+--+-+--+ |
        #       | |            | |
        #       | |            | |
        #       | |            | |
        #       | +--+-+--+-+--+ |
        #            | |  | |
        #            +-+  +-+
        #
        # Case #4:
        #
        #            +-+  +-+ <|
        #            | |  | |
        #       | +--+-+--+-+--+ |
        #       | |            | |
        #       | |            | |
        #       | |            | |
        #       | +--+-+--+-+--+ |
        #            | |  | |
        #            +-+  +-+
        #
        else:  # max_space_vertical_of_p1 >= max_space_horizontal_of_p1:
            if space_left_of_p1 >= space_right_of_p1:  # Case #3:
                direction = Direction.EAST
                apex_x = pad1_bbox.left - silk_pad_offset
                apex_x = rounding.round_to_grid_down(apex_x, self._ROUND_GRID)
                space_on_x_axis = space_left_of_p1
            else:
                direction = Direction.WEST  # Case #4:
                apex_x = pad1_bbox.right + silk_pad_offset
                apex_x = rounding.round_to_grid_up(apex_x, self._ROUND_GRID)
                space_on_x_axis = space_right_of_p1
            if pad1_bbox.top < 0.0:
                space_on_y_axis = -pad1_bbox.top - body_y_half
            else:
                space_on_y_axis = pad1_bbox.bottom - body_y_half

            # If pad 1 is very close to the left of the component outline, we can place
            # the arrow closer to the bottom (i.e. it does not have to be on the top
            # side of the component outline):
            if apex_x <= -body_x_half - silk_fab_offset:
                space_on_y_axis = max(space_on_y_axis, pad1_bbox.bottom - pad1_bbox.top)
                if pad1_bbox.top < 0.0:
                    min_arrow_y_position = pad1_bbox.bottom
                else:
                    min_arrow_y_position = pad1_bbox.top
                clearance_to_fab = 0.0
            else:
                # Ideally allow sufficient clearance between the outline of the
                # component on the silk layer and the arrow:
                clearance_to_fab = 2.5 * silk_line_width
                min_arrow_y_position = -body_y_half - silk_fab_offset - clearance_to_fab
                if pad1_bbox.top > 0.0:
                    min_arrow_y_position *= -1
            # Find the east/west-pointing arrow that fits:
            for i in max_arrow_range:
                arrow_width = DualAndQuadPadArrayLayout._ARROW_WIDTHS[i]
                arrow_length = DualAndQuadPadArrayLayout._ARROW_LENGTHS[i]
                fits_on_x = space_on_x_axis >= arrow_length
                fits_on_y = space_on_y_axis >= arrow_width
                if fits_on_y and fits_on_x:
                    # Place the arrow as close as possible to the pad center
                    if pad1_bbox.top < 0.0:
                        apex_y = min(pad1.at.y, min_arrow_y_position - arrow_width / 2)
                    else:
                        apex_y = max(pad1.at.y, min_arrow_y_position + arrow_width / 2)
                    # If the arrow apex is on the top of the pad, try moving it further
                    # to the bottom:
                    if apex_y < pad1_bbox.top + silk_line_width:
                        if pad1_bbox.top < 0.0:
                            apex_y += max(
                                0.0,
                                min(
                                    clearance_to_fab,
                                    pad1_bbox.top - apex_y + silk_line_width,
                                ),
                            )
                        else:
                            apex_y += min(
                                0.0,
                                max(
                                    clearance_to_fab,
                                    apex_y - pad1_bbox.bottom - silk_line_width,
                                ),
                            )
                    apex_y = rounding.round_to_grid_down(apex_y, self._ROUND_GRID)
                    arrow_apex = Vector2D.from_floats(apex_x, apex_y)
                    return pin1_arrow.Pin1SilkscreenArrow(
                        apex_position=arrow_apex,
                        angle=direction,
                        size=arrow_width,
                        length=arrow_length,
                        layer="F.SilkS",
                        line_width_mm=silk_line_width,
                    )

        # If it is not possible to point horizontally or vertically to the pad without
        # having a part of the arrow sticking out too much, a diagonal arrow is used:
        #
        # Case 5:
        #
        #      +
        #     /|
        #    +-+  -------------  <- silk
        #        +------------+  <- body
        #    =====            ===== <- pad
        #        |            |
        #    =====            =====
        #        +------------+
        #        -------------- <- silk
        #
        if self.body_size.min_val <= 2.0:
            # Top corner of the top-left pad (inset to be exactly on rounded corners)
            top_left_pad_top_left_corner = pad1.get_top_left_corner_midpoint()
            arrow_apex = top_left_pad_top_left_corner - silk_pad_offset * (sqrt(2) / 2)
            # round off away from the pad edge
            arrow_apex.x = rounding.round_to_grid_down(arrow_apex.x, 0.01)
            arrow_apex.y = rounding.round_to_grid_down(arrow_apex.y, 0.01)
            arrow_width = DualAndQuadPadArrayLayout._ARROW_WIDTHS[preferred_size_idx]
            return pin1_arrow.Pin1SilkScreenArrow45Deg(
                arrow_apex,
                Direction.SOUTHEAST,
                arrow_width,
                "F.SilkS",
                silk_line_width,
            )
        # For large components where the arrow does not fit laterally, we want want to
        # point longitudinally to the pin 1:
        #
        # Case 6:
        #
        #        --------------  <- silk
        #        +------------+  <- body
        # |> =====            ===== <- pad
        #        |            |
        #    =====            =====
        #        +------------+
        #        -------------- <- silk
        #
        else:  # if self.body_size.min_val > 2.0:
            arrow_width = DualAndQuadPadArrayLayout._ARROW_WIDTHS[1]  # MEDIUM
            arrow_length = DualAndQuadPadArrayLayout._ARROW_LENGTHS[1]  # MEDIUM
            if self.pad_arrays[idx_array].spacing.x == 0.0:  # vertical pad array:
                apex_x = pad1_bbox.left - silk_pad_offset
                apex_y = pad1.at.y
                direction = Direction.EAST
            else:
                apex_y = pad1_bbox.top - silk_pad_offset
                apex_x = pad1.at.x
                direction = Direction.SOUTH
            apex_x = rounding.round_to_grid_down(apex_x, self._ROUND_GRID)
            apex_y = rounding.round_to_grid_down(apex_y, self._ROUND_GRID)
            return pin1_arrow.Pin1SilkscreenArrow(
                apex_position=Vector2D.from_floats(apex_x, apex_y),
                angle=direction,
                size=arrow_width,
                length=arrow_length,
                layer="F.SilkS",
                line_width_mm=silk_line_width,
            )

    def _create_silk(self) -> None:
        silk_line_width = self.global_config.silk_line_width
        silk_pad_offset = self.global_config.silk_pad_clearance + silk_line_width / 2
        silk_fab_offset = self.global_config.silk_fab_offset

        body_x_half = self.body_size.x / 2
        body_y_half = self.body_size.y / 2

        arrow = self._create_arrow()
        self.append(arrow)

        # Draw the component outline on the silk screen:
        #
        #      +----------------+  <- silk
        #      | +------------+ |
        #    =====            ==== <- pad
        #        |            |
        #    =====            ====
        #      | +------------+ |
        #      +----------------+
        #
        pads_bbox_vert = self._get_bounding_box_of_vertical_pad_arrays()
        pads_bbox_hor = self._get_bounding_box_of_horizontal_pad_arrays()
        silk_bottom_y = body_y_half + silk_fab_offset
        silk_right_x = body_x_half + silk_fab_offset
        if pads_bbox_vert.is_defined():
            silk_bottom_y = max(pads_bbox_vert.bottom + silk_pad_offset, silk_bottom_y)
        if pads_bbox_hor.is_defined():
            silk_right_x = max(pads_bbox_hor.right + silk_pad_offset, silk_right_x)

        size = (2 * silk_right_x, 2 * silk_bottom_y)
        g_silk = GeomRectangle(center=(0, 0), size=size)
        # The silk outline might need to be trimmed around the arrow:
        g_silk_kept = subtract(g_silk, arrow.as_polygon(inflation=silk_line_width * 2))
        # Trim the silk outline around the pads:
        keepouts: list[GeomShapesClosed] = []
        for pad_array in self.pad_arrays:
            keepouts.extend(pad_array.as_geom_shapes(inflation=silk_pad_offset))
        if self.exposed_pad is not None:
            keepouts.append(self.exposed_pad.as_geom_shape(inflation=silk_pad_offset))
        g_silk_kept = applyKeepouts(items=g_silk_kept, keepouts=keepouts)
        for shape in g_silk_kept:
            self.append(
                shape_to_node(shape=shape, layer="F.SilkS", width=silk_line_width)
            )

    @classmethod
    def _init_class_attributes(cls, silk_line_width: float) -> None:
        if cls._class_attributes_initialized:
            return
        arrow_types = [SilkArrowSize.LARGE, SilkArrowSize.MEDIUM, SilkArrowSize.SMALL]
        cls._ARROW_WIDTHS = []
        cls._ARROW_LENGTHS = []
        for arrow_type in arrow_types:
            width, length = getStandardSilkArrowSize(
                size=arrow_type,
                silk_line_width=silk_line_width,
            )
            cls._ARROW_WIDTHS.append(width)
            cls._ARROW_LENGTHS.append(length)
        cls._class_attributes_initialized = True
