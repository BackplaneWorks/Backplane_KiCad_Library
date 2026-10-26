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

"""Tolerance definitions."""

import math

TOL_MM = 1e-7
"""Standard tolerance in mm for geometric calculations. It is typically used to define
within which tolerance two elements are considered to be equal.
"""


MIN_SEGMENT_LENGTH = 1e-6
"""The minimum segment length. Shapes resulting from an operation (cut, keepout, etc.)
that are smaller than that are typically discarded from the results.
"""


def tol_deg(tol: float = TOL_MM, radius: float = 10) -> float | None:
    """Convert the distance tolerance given in mm to an angular tolerance in degrees.

    Standard tolerance in degrees for geometric calculations. Arcs with dimensions
    smaller than that are typically considered null and discarded from the results.

    Args:
        tol: The distance tolerance in mm.
        radius: The radius of the arc for which the angular tolerance shall be
            established.

    Returns:
        The angular tolerance in degrees or None if the radius is zero.
    """
    if radius:
        return math.degrees(tol / radius)
    else:
        return None
