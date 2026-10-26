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

from KicadModTree.nodes.specialized.ChamferedRectangle import (
    ChamferedRectangle,
    CornerSelection,
)
from KicadModTree import PolygonLine, Rectangle
from kilibs.geom import Vector2D, Direction

from kilibs.config.global_config import GlobalConfig


def draw_chamfer_rect_fab(
    size: Vector2D, global_config: GlobalConfig, has_chamfer: bool = True
) -> ChamferedRectangle | Rectangle:
    """
    Constructor for a optionally-chamfered Fab-layer rectangle with a chamfer on
    the top-left corner, centered on the origin.

    Mostly just glue between the ChamferedRectangle constructor and the global config.

    :param size: The size of the rectangle
    :param global_config: The global configuration object (drives line width)
    :param has_chamfer: Whether to draw the chamfer or not (default: True)

    :return: The drawing node
    """
    if has_chamfer:
        return ChamferedRectangle(
            center=Vector2D(0, 0),
            size=size,
            chamfer=global_config.fab_bevel,
            corners=CornerSelection({CornerSelection.TOP_LEFT: True}),
            layer="F.Fab",
            width=global_config.fab_line_width,
            fill=False,
        )
    else:
        return Rectangle(
            start=-size / 2,
            end=size / 2,
            width=global_config.fab_line_width,
            layer="F.Fab",
            fill=False,
        )


def draw_pin1_chevron_on_hline(
    line_y: float,
    apex_x: float,
    direction: Direction,
    global_config: GlobalConfig,
    chevron_length: float | None = None,
) -> PolygonLine:
    """
    Draw a v-shaped chevron on the Fab layer, pointing in the given direction, from
    horizontal line at the given y-coordinate.

            /\
           /  \
    ------------------

    : param line_y: The y-coordinate of the horizontal line
    : param apex_x: The x-coordinate of the apex of the chevron
    : param direction: The direction of the chevron (NORTH or SOUTH - i.e. above
                       or below the line.
    : param global_config: The global configuration object (drives line width)
    : param chevron_length: The length of the chevron (top to bottom). None for default
                       from global config.

    : return: A PolygonLine object representing the chevron
    """

    if chevron_length is None:
        chevron_length = global_config.fab_pin1_marker_length

    # Seems about right
    chevron_width = round(chevron_length * 1.3)

    if direction == Direction.NORTH:
        pass
    elif direction == Direction.SOUTH:
        chevron_length = -chevron_length
    else:
        raise ValueError(f"Invalid direction {direction}")

    return PolygonLine(
        shape=[
            [apex_x - chevron_width / 2, line_y],
            [apex_x, line_y - chevron_length],
            [apex_x + chevron_width / 2, line_y],
        ],
        layer="F.Fab",
        width=global_config.fab_line_width,
    )
