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

from kilibs.geom import GeomRectangle
from KicadModTree import Circle, Node, Stadium
from kilibs.config import global_config as GC


def make_round_or_stadium_courtyard(
    global_config: GC.GlobalConfig, bounding_rectangle: GeomRectangle
) -> list[Node]:
    """
    Create a courtyard that fits within the given rectangle, using a stadium
    if the rectangle isn't square, or a circle if it is.

    This will do the necessary grid rounding per GC settings.
    """

    courtyard_rect = bounding_rectangle.copy().round_to_grid(grid=global_config.courtyard_grid, outwards=True)

    layer = "F.CrtYd"
    width = global_config.courtyard_line_width

    # Could make this parameterised, but do we need that?
    tolerance = global_config.courtyard_grid

    # create courtyard
    if abs(courtyard_rect.size.x - courtyard_rect.size.y) > tolerance:
        courtyard = Stadium(
                shape=courtyard_rect,
                layer=layer,
                width=width,
            )
    else:
        courtyard = Circle(
            center=courtyard_rect.center,
            radius=courtyard_rect.max_dimension / 2,
            layer=layer,
            width=width,
        )
    return [courtyard]
