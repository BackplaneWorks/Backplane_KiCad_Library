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

from generators.tools.footprint.drawing_tools import (
    getStandardSilkArrowSize,
    SilkArrowSize,
)
from generators.tools.footprint.nodes import pin1_arrow
from KicadModTree import Pad
from kilibs.config.global_config import GlobalConfig
from kilibs.geom import Direction, Vector2D, GeomRectangle


def draw_silk_triangle_for_pad(
    pad: Pad, arrow_size: SilkArrowSize,
    arrow_direction: Direction,
    stroke_width: float,
    pad_silk_offset: float
):
    """
    Draw a silk arrow of the given size next to the given pad. This is a common
    idiom for drawing a pin 1 marker.

    The arrow direction is the direction the arrow points in - 0 is rightwards.
    It will be placed pointing towards the pad, so a south-pointing arrow
    will be placed north of the pad.

    Only N/S/E/W directions are supported for now.
    45 degree directions should be OK, but will need the 45 degree arrow.

    This assumes the pad size is the right thing to use for the offsets,
    which is true for the normal shapes: rects, circles, ovals, etc.
    """

    if arrow_direction == Direction.SOUTH:
        apex = Vector2D(
            pad.at.x, pad.at.y - pad.size.y / 2 - pad_silk_offset - stroke_width / 2
        )
    elif arrow_direction == Direction.NORTH:
        apex = Vector2D(
            pad.at.x, pad.at.y + pad.size.y / 2 + pad_silk_offset + stroke_width / 2
        )
    elif arrow_direction == Direction.EAST:
        apex = Vector2D(
            pad.at.x - pad.size.x / 2 - pad_silk_offset - stroke_width / 2, pad.at.y
        )
    elif arrow_direction == Direction.WEST:
        apex = Vector2D(
            pad.at.x + pad.size.x / 2 + pad_silk_offset + stroke_width / 2, pad.at.y
        )
    else:
        raise ValueError(f"Unsupported arrow direction: {arrow_direction}")

    # Adjust for the stroke width
    silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
        arrow_size, stroke_width
    )

    return pin1_arrow.Pin1SilkscreenArrow(
        apex_position=apex,
        angle=arrow_direction,
        size=silk_arrow_size,
        length=silk_arrow_length,
        layer="F.SilkS",
        line_width_mm=stroke_width,
    )


def draw_silk_triangle_clear_of_fab_hline_and_pad(
    global_config: GlobalConfig,
    pad: Pad,
    arrow_direction: Direction,
    line_y: float,
    line_clearance_y: float,
    arrow_size: SilkArrowSize,
):
    r"""
    Draw an arrow pointing towards a pad, but clear of some horizontal line.

    This is quite common for SMT parts with quite long gullwings, where putting
    the arrow at the end of the pad is a bit wasteful.

             +---+
    -------  |   |  ------- <-- nominal line
        |\   |   | <--\
        | >  +---+     \-- pad
        |/

    :param global_config: The global configuration
    :param pad: The pad to draw the arrow near
    :param arrow_direction: The direction the arrow points in (EAST or WEST)
    :param line_y: The y position of the line to clear
    :param line_clearance: How far to clear the line (this is the space from the
                           line centre to the node of the arrow)
    :param arrow_size: The size of the arrow
    """

    silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
        arrow_size, global_config.silk_line_width
    )

    # First figure out the apex y
    apex_offset = line_clearance_y + silk_arrow_size / 2
    apex_y = line_y - apex_offset if (line_clearance_y < 0) else line_y + apex_offset

    pad_center_to_node_offset_x  = pad.size.x / 2 + global_config.silk_pad_offset

    if arrow_direction == Direction.EAST:
        apex_x = pad.at.x - pad_center_to_node_offset_x
    elif arrow_direction == Direction.WEST:
        apex_x = pad.at.x + pad_center_to_node_offset_x
    else:
        raise ValueError(f"Unsupported arrow direction: {arrow_direction}")

    return pin1_arrow.Pin1SilkscreenArrow(
        apex_position=Vector2D(apex_x, apex_y),
        angle=arrow_direction,
        size=silk_arrow_size,
        length=silk_arrow_length,
        layer="F.SilkS",
        line_width_mm=global_config.silk_line_width
    )

def draw_silk_triangle45_clear_of_fab_hline_and_pad(
    global_config: GlobalConfig,
    pad: Pad,
    arrow_direction: Direction,
    line_y: float,
    line_clearance_y: float,
    arrow_size: SilkArrowSize,
):
    r"""
    Draw an arrow pointing towards a pad, but clear of some horizontal line.

    This is quite common for SMT parts with quite short gullwings, where putting
    the arrow at the end of the pad is a bit wasteful, but there isn't enough
    protruding pad for a 90 degree arrow.

             +---+
    -------  |   |  ------- <-- nominal line
        --+  |   | <--\
         \|  +---+     \-- pad

    :param global_config: The global configuration
    :param pad: The pad to draw the arrow near
    :param arrow_direction: The direction the arrow points in (NE, NW, SE, SW)
    :param line_y: The y position of the line to clear
    :param line_clearance: How far to clear the line (this is the space from the
                           line centre to the apex of the arrow)
    :param arrow_size: The size of the arrow
    """

    silk_arrow_size, _ = getStandardSilkArrowSize(
        arrow_size, global_config.silk_line_width
    )

    line_width = global_config.silk_line_width

    # First figure out the apex y
    apex_offset = line_clearance_y
    apex_y = line_y - apex_offset if (line_clearance_y < 0) else line_y + apex_offset

    pad_center_to_node_offset_x  = pad.size.x / 2 + global_config.silk_pad_offset

    if arrow_direction in [Direction.NORTHEAST, Direction.SOUTHEAST]:
        apex_x = pad.at.x - pad_center_to_node_offset_x
    elif arrow_direction in [Direction.NORTHWEST, Direction.SOUTHWEST]:
        apex_x = pad.at.x + pad_center_to_node_offset_x
    else:
        raise ValueError(f"Unsupported arrow direction: {arrow_direction}")

    return pin1_arrow.Pin1SilkScreenArrow45Deg(
        apex_position=Vector2D(apex_x, apex_y),
        angle=arrow_direction,
        size=silk_arrow_size,
        layer="F.SilkS",
        line_width_mm=line_width,
    )


def auto_silk_triangle_for_pad_and_box(
    global_config: GlobalConfig,
    pad: Pad,
    silk_rect: GeomRectangle,
    arrow_size: SilkArrowSize,
    direction_if_inside: Direction | None,
) -> pin1_arrow.SilkscreenArrow:
    """
    Draw an automatic silk arrow for a pad relative to some nominal
    body rectangle with a best-effort placement:

        - if the pad is inside the rect, the arrow goes on the nearesr
          side (NSEW direction)
        - if the pad sticks out of the rect, the arrow either points
          into it directly (NSEW), or, if it doesn't stick out enough,
          into the corner made of the pad and the body side at 45 degrees.

    Args:
        global_config: The global config to use for clearances
        pad: The pad to give a pin 1 arrow
        silk_rect: The body rectangle with silkscreen outset already applied
        arrow_size: The nominal arrow size
        direction_if_inside: If the pad is inside the body, use this direction
            instead of guessing from the nearest edge. If None, guess.
    """

    silk_arrow_size, silk_arrow_length = getStandardSilkArrowSize(
        arrow_size, global_config.silk_line_width
    )

    apex_pos: Vector2D | None = None
    arrow_direction = Direction.EAST

    pad_bbox = pad.bbox()

    # Bbox of the keepout around the pad
    pad_silk_bbox = pad_bbox.copy()
    pad_silk_bbox.inflate(global_config.silk_pad_offset)

    # Bbox of the body silk rectagle
    body_bbox = silk_rect.bbox()

    # For all these, < 0 means the pad silk keepout
    # extends out of the body silk shape
    l_dist = pad_bbox.left - silk_rect.left
    r_dist = silk_rect.right - pad_bbox.right
    t_dist = pad_silk_bbox.top - silk_rect.top
    b_dist = silk_rect.bottom - pad_silk_bbox.bottom

    # Does the arrow point directly inwards from an edge? (i.e. not placed next
    # to a pad, but poiinting towards it from a distance). Common for boxy modules
    # that have the pins all inside the body boundary box.
    #
    # We do this if the pad is entirely inside the body bbox, or if we have a
    # given direction to use.
    arrow_points_inwards = (
        body_bbox.contains_bbox(pad_bbox) or direction_if_inside is not None
    )

    if arrow_points_inwards:

        if direction_if_inside is not None:
            # If we have a given direction, use that
            arrow_direction = direction_if_inside
        else:
            # Figure out which side is closer to the pad and put the arrow
            # on that side
            sorted_dists = [l_dist, r_dist, t_dist, b_dist]
            sorted_dists.sort()

            if sorted_dists[0] == l_dist:
                arrow_direction = Direction.EAST
            elif sorted_dists[0] == r_dist:
                arrow_direction = Direction.WEST
                apex_x = max(pad_silk_bbox.right, silk_rect.right)
                apex_pos = Vector2D.from_floats(apex_x, pad.at.y)
            elif sorted_dists[0] == t_dist:
                arrow_direction = Direction.SOUTH
                apex_y = min(pad_silk_bbox.top, silk_rect.top)
                apex_pos = Vector2D.from_floats(pad.at.x, apex_y)
            else:
                arrow_direction = Direction.NORTH
                apex_y = max(pad_silk_bbox.bottom, silk_rect.bottom)
                apex_pos = Vector2D.from_floats(pad.at.x, apex_y)

        match arrow_direction:
            case Direction.EAST:
                apex_x = min(pad_silk_bbox.left, silk_rect.left)
                apex_pos = Vector2D.from_floats(apex_x, pad.at.y)
            case Direction.WEST:
                apex_x = max(pad_silk_bbox.right, silk_rect.right)
                apex_pos = Vector2D.from_floats(apex_x, pad.at.y)
            case Direction.SOUTH:
                apex_y = min(pad_silk_bbox.top, silk_rect.top)
                apex_pos = Vector2D.from_floats(pad.at.x, apex_y)
            case Direction.NORTH:
                apex_y = max(pad_silk_bbox.bottom, silk_rect.bottom)
                apex_pos = Vector2D.from_floats(pad.at.x, apex_y)
            case _:
                raise ValueError(f"Unsupported arrow direction: {arrow_direction}. ")

    else:
        # If we get here, the pad sticks out on at least one side

        # Place either pointing directly at the arrow from the side if there is space,
        # else nestle into the corner

        # Apex any closer than this, and the corner of the arrow will hit the body outline
        arrow_closest_body_approach = (
            silk_arrow_size / 2 + 3 * global_config.silk_line_width
        )

        # Min space require to fit the arrow at the side of the pad rather in the corner
        # More than half the arrow size, so that the apex isn't right at the pad corner
        min_arrow_pad_side_space = silk_arrow_size * 0.7

        if l_dist < 0:  # Stick out of left

            if -l_dist > min_arrow_pad_side_space and t_dist > 0:
                # it sticks out enough to fit arrow, bot not at the top
                arrow_direction = Direction.SOUTH
                apex_pos = Vector2D.from_floats(
                    body_bbox.left - arrow_closest_body_approach, pad_silk_bbox.top
                )
            else:
                # Point into corner
                arrow_direction = Direction.SOUTHEAST
                apex_pos = Vector2D.from_floats(body_bbox.left, pad_silk_bbox.top)
        elif t_dist < 0:
            # Sticks out of the top (but not the left)
            if -t_dist > min_arrow_pad_side_space:
                arrow_direction = Direction.EAST
                apex_pos = Vector2D.from_floats(
                    pad_silk_bbox.left, body_bbox.top - arrow_closest_body_approach
                )
            else:
                # Point into corner
                arrow_direction = Direction.SOUTHEAST
                apex_pos = Vector2D.from_floats(pad_silk_bbox.left, body_bbox.top)
        elif r_dist < 0:
            # Sticks out of the right
            if -r_dist > min_arrow_pad_side_space and t_dist > 0:
                # it sticks out enough to fit arrow, bot not at the top
                arrow_direction = Direction.SOUTH
                apex_pos = Vector2D.from_floats(
                    body_bbox.right + arrow_closest_body_approach, pad_silk_bbox.top
                )
            else:
                # Point into corner
                arrow_direction = Direction.SOUTHWEST
                apex_pos = Vector2D.from_floats(body_bbox.right, pad_silk_bbox.top)
        elif b_dist < 0:
            # Sticks out of the top (but not the left or right
            if -b_dist > min_arrow_pad_side_space:
                arrow_direction = Direction.EAST
                apex_pos = Vector2D.from_floats(
                    pad_silk_bbox.left, body_bbox.bottom + arrow_closest_body_approach
                )
            else:
                # Point into corner
                arrow_direction = Direction.NORTHEAST
                apex_pos = Vector2D.from_floats(pad_silk_bbox.left, body_bbox.bottom)
        else:
            raise RuntimeError(
                "Doesn't stick out of any side, but the bbox contain check failed?"
            )

    # Construct the right kind of arrows
    if arrow_direction.is_cardinal():

        arrow = pin1_arrow.Pin1SilkscreenArrow(
            apex_position=apex_pos,
            angle=arrow_direction,
            size=silk_arrow_size,
            length=silk_arrow_length,
            layer="F.SilkS",
            line_width_mm=global_config.silk_line_width,
        )
    else:
        arrow = pin1_arrow.Pin1SilkScreenArrow45Deg(
            apex_position=apex_pos,
            angle=arrow_direction,
            # Compensate for the chunkier 45 degree arrow
            size=silk_arrow_size * 0.8,
            layer="F.SilkS",
            line_width_mm=global_config.silk_line_width,
        )

    return arrow
