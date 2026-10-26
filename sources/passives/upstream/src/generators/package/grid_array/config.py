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

import enum
import itertools
from typing import Any

from collections.abc import Generator
from string import ascii_uppercase


class GridStagger(enum.Enum):
    """The stagger direction of a grid layout."""

    NONE = "none"
    """No stagger: the pads are aligned in a rectangular grid."""
    X = "x"
    """x-stagger: the pads are staggered in the x direction."""
    Y = "y"
    """y-stagger: the pads are staggered in the y direction."""


def _row_name_generator() -> Generator[str, Any, None]:
    row_names: list[str] = [x for x in ascii_uppercase if x not in "IOQSXZ"]
    for n in itertools.count(1):
        for s in itertools.product(row_names, repeat=n):
            yield "".join(s)

# generate dict of A, B .. Y, Z, AA, AB .. CY less easily-confused letters
ROW_NAMES = list(itertools.islice(_row_name_generator(), 80))
"""The row names of BGAs."""
