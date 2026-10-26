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

import pytest

from kilibs.geom.operations import rounding as R


@pytest.mark.parametrize(
    "val, grid, expected",
    [
        (0, 0, 0),
        (0.6, 0.05, 0.60),
        # Check epsilon near grid points
        (0.600000001, 0.05, 0.60),
        (0.599999999, 0.05, 0.60),
        # And for the down rounding
        (-0.600000001, 0.05, -0.60),
        (-0.599999999, 0.05, -0.60),
    ],
)
def test_round_to_grid(val, grid, expected):
    result = R.round_to_grid(val, grid, epsilon=1e-7)
    assert result == pytest.approx(expected)
