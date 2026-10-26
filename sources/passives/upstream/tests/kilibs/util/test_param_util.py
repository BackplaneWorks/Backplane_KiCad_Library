# KiLibs is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KiLibs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2023 by Kicad Library Generator contributors

import pytest

from kilibs.geom import Vector2D, Vector3D
from kilibs.util import param_util as PU


def test_toVectorUseCopyIfNumber():

    assert PU.toVectorUseCopyIfNumber(1) == Vector2D(1, 1)
    assert PU.toVectorUseCopyIfNumber((1, 2)) == Vector2D(1, 2)

    # Test that low_limit is enforced when must_be_larger=True
    with pytest.raises(ValueError):
        PU.toVectorUseCopyIfNumber((2, 2), low_limit=2, must_be_larger=True)

    # And the default is the same
    with pytest.raises(ValueError):
        PU.toVectorUseCopyIfNumber((2, 2), low_limit=2)

    # Equal is OK with must_be_larger=False
    assert PU.toVectorUseCopyIfNumber(
        (2, 2), low_limit=2, must_be_larger=False
    ) == Vector2D(2, 2)

    # 3D mode
    assert PU.toVectorUseCopyIfNumber(1, length=3) == Vector3D(1, 1, 1)
