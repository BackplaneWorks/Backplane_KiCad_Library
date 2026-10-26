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
# (C) The KiCad Librarian Team

"""Geometric tools."""

from .intersection import intersect
from .rounding import (
    is_polygon_clockwise,
    round_polygon_to_grid,
    round_to_grid,
    round_to_grid_decreasing_area,
    round_to_grid_down,
    round_to_grid_e,
    round_to_grid_increasing_area,
    round_to_grid_nearest,
    round_to_grid_up,
)
from .splitting import split
from .subtraction import subtract, subtract_many
from .union import unite

__all__ = [
    "is_polygon_clockwise",
    "round_polygon_to_grid",
    "round_to_grid",
    "round_to_grid_decreasing_area",
    "round_to_grid_down",
    "round_to_grid_e",
    "round_to_grid_increasing_area",
    "round_to_grid_nearest",
    "round_to_grid_up",
    "split",
    "intersect",
    "subtract",
    "subtract_many",
    "unite",
]
