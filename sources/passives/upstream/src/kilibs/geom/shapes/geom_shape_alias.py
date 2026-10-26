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

"""Definition of aliases for the geometric shapes."""

from __future__ import annotations

from .geom_arc import GeomArc
from .geom_chamfered_rectangle import GeomChamferedRectangle
from .geom_circle import GeomCircle
from .geom_compound_polygon import GeomCompoundPolygon
from .geom_cross import GeomCross
from .geom_cruciform import GeomCruciform
from .geom_line import GeomLine
from .geom_polygon import GeomPolygon
from .geom_rectangle import GeomRectangle
from .geom_round_rectangle import GeomRoundRectangle
from .geom_stadium import GeomStadium
from .geom_trapezoid import GeomTrapezoid

GeomShapesAtomic = GeomArc | GeomCircle | GeomLine
"""A union with all the atomic geometric shapes."""

GeomShapesNative = (
    GeomArc | GeomCircle | GeomLine | GeomRectangle | GeomPolygon | GeomCompoundPolygon
)
"""A union with all the geometric shapes that are native to KiCad."""

GeomShapesClosed = (
    GeomChamferedRectangle
    | GeomCompoundPolygon
    | GeomCircle
    | GeomCruciform
    | GeomPolygon
    | GeomRectangle
    | GeomRoundRectangle
    | GeomStadium
    | GeomTrapezoid
)
"""A union with all the closed geometric shapes."""

GeomShapesOpen = GeomArc | GeomLine | GeomCross
"""A union with all the open geometric shapes."""

GeomShapes = GeomShapesOpen | GeomShapesClosed
"""The union with all the geometric shapes."""
