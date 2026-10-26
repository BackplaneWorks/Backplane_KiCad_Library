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

"""Functions for rounding in different ways."""

import math
from typing import overload

from kilibs.geom.tolerances import TOL_MM


# TODO: change the epsilon to TOL_MM once we are ready to review the affected changes
def round_to_grid_up(value: float, grid: float, epsilon: float = 0) -> float:
    """Round a number to a multiple of the grid size, _always_ rounding up.

    Args:
        value: The value to round (up) to the grid.
        grid: The grid.
        epsilon: A small value that helps preventing rounding errors in floating point
            numbers like 0.1999999 or 0.20000001. This value should typically default
            to `TOL_MM`.

    Returns:
        The value(s) rounded to the given grid.
    """
    # epsilon should prevent values like 0.4 (aka 0.40000000000000002) being rounded up to 0.6
    return math.ceil(value / grid - epsilon) * grid


def round_to_grid_down(value: float, grid: float, epsilon: float = 0) -> float:
    """Round a number to a multiple of the grid size, _always_ rounding down.

    Args:
        value: The value to round (down) to the grid.
        grid: The grid.
        epsilon: A small value that helps preventing rounding errors in floating point
            numbers like 0.1999999 or 0.20000001. This value should typically default
            to `TOL_MM`.

    Returns:
        The value(s) rounded to the given grid.
    """
    return math.floor(value / grid + epsilon) * grid


@overload
def round_to_grid(value: float, grid: float, epsilon: float = 0) -> float: ...


@overload
def round_to_grid(
    value: list[float], grid: float, epsilon: float = 0
) -> list[float]: ...


def round_to_grid(
    value: float | list[float], grid: float, epsilon: float = 0
) -> float | list[float]:
    """Round a number to a multiple of the grid size, _always_ rounding away from zero.

    This is the most suitable way to round for many outlines, especially simple
    outlines around objects centred at the origin (e.g. courtyards and silkscreen).

    Args:
        value: The value(s) to round to the grid.
        grid: The grid.
        epsilon: A small value that helps preventing rounding errors in floating point
            numbers like 0.1999999 or 0.20000001. This value should typically default
            to `TOL_MM`.

    Returns:
        The value(s) rounded to the given grid.
    """
    if grid == 0:
        return value
    if isinstance(value, list):
        return_list: list[float] = []
        for value in value:
            return_list.append(round_to_grid(value, grid, epsilon))
        return return_list
    return (
        round(round_to_grid_up(value, grid, epsilon), 6)
        if value > 0
        else round(round_to_grid_down(value, grid, epsilon), 6)
    )


def round_to_grid_e(value: float, grid: float) -> float:
    """Round a number to a multiple of the grid size, _always_ rounding away from zero
    while preventing rounding errors when rounding up to 5e-7 (or 0.5 nm for
    footprints).

    This is the most suitable way to round for many outlines, especially simple
    outlines around objects centred at the origin (e.g. courtyards and silkscreen).

    Args:
        value: The value to round to the grid.
        grid: The grid.

    Returns:
        The value rounded to the given grid.
    """
    return round_to_grid(value, grid, TOL_MM)


def round_to_grid_nearest(value: float, grid: float) -> float:
    """Round a number to a multiple of the grid size, rounding to the nearest multiple
    of the grid size.

    This is the most suitable way to round in case where you are just rounding off
    floating point errors, and you want to round to the nearest grid point.

    Args:
        value: The value to round to the grid.
        grid: The grid.

    Returns:
        The value rounded to the given grid.
    """
    if grid == 0:
        return value
    return round(round(value / grid) * grid, 6)


def round_polygon_to_grid(
    pts: list[list[float]], grid: float, clock_wise: bool, increase_area: bool
) -> None:
    """Round a polygon (defined by a list of points) to the grid such that the enclosed
    area will be either >= or <= as before, depending on the value of the parameter
    "increase_area". Operations are run in-place, i.e. overwriting the polygon points
    given as argument.

    Args:
        pts: the list of points definig the polygon.
        grid: the grid to which the rounding is made.
        clock_wise: True if pts define the polygon in clock-wise orientation, False otherwise.
        increase_area: True when rounding away from the polygon, False otherwise.

    Returns:
        the list of points defining the polygon rounded to the grid.
    """
    # TODO: remove this function
    if clock_wise and increase_area or (not clock_wise and not increase_area):
        round_up = round_to_grid_up
        round_down = round_to_grid_down
    else:
        round_down = round_to_grid_up
        round_up = round_to_grid_down

    num = len(pts)
    for i, pt1 in enumerate(pts):
        pt2 = pts[(i + 1) % num]
        if pt1[0] < pt2[0]:  # going right
            pt1[1] = round_down(pt1[1], grid, TOL_MM)
            pt2[1] = round_down(pt2[1], grid, TOL_MM)
        elif pt1[0] > pt2[0]:  # going left
            pt1[1] = round_up(pt1[1], grid, TOL_MM)
            pt2[1] = round_up(pt2[1], grid, TOL_MM)
        if pt1[1] > pt2[1]:  # going up
            pt1[0] = round_down(pt1[0], grid, TOL_MM)
            pt2[0] = round_down(pt2[0], grid, TOL_MM)
        elif pt1[1] < pt2[1]:  # going down
            pt1[0] = round_up(pt1[0], grid, TOL_MM)
            pt2[0] = round_up(pt2[0], grid, TOL_MM)


def round_to_grid_increasing_area(pts: list[list[float]], grid: float) -> None:
    """Round a polygon (defined by a list of points) to the grid such that the enclosed
    area will be at least as large as before. Operations are run in-place, i.e.
    overwriting the polygon points given as argument.
    """
    # TODO: remove this function
    clock_wise = is_polygon_clockwise(pts)
    round_polygon_to_grid(pts, grid, clock_wise, increase_area=True)


def round_to_grid_decreasing_area(pts: list[list[float]], grid: float) -> None:
    """Round a polygon (defined by a list of points) to the grid such that the enclosed
    area will be smaller or equal as before. Operations are run in-place, i.e.
    overwriting the polygon points given as argument.
    """
    # TODO: remove this function
    clock_wise = is_polygon_clockwise(pts)
    round_polygon_to_grid(pts, grid, clock_wise, increase_area=False)


def is_polygon_clockwise(pts: list[list[float]]) -> bool:
    """Returns True if the polygon points are given in clockwise order, False otherwise."""
    # TODO: remove this function
    sum = 0.0
    num = len(pts)
    for i, pt1 in enumerate(pts):
        pt2 = pts[(i + 1) % num]
        sum += (pt2[0] - pt1[0]) * (pt2[1] + pt1[1])

    if sum < 0:
        return True
    else:
        return False
