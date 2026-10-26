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

"""Geometric shapes."""

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
from .geom_shape import GeomShape, GeomShapeClosed, GeomShapeOpen
from .geom_shape_alias import (
    GeomShapes,
    GeomShapesAtomic,
    GeomShapesClosed,
    GeomShapesNative,
    GeomShapesOpen,
)
from .geom_stadium import GeomStadium
from .geom_trapezoid import GeomTrapezoid

__all__ = [
    "GeomArc",
    "GeomChamferedRectangle",
    "GeomCircle",
    "GeomCompoundPolygon",
    "GeomCross",
    "GeomCruciform",
    "GeomLine",
    "GeomPolygon",
    "GeomRectangle",
    "GeomRoundRectangle",
    "GeomShape",
    "GeomShapeClosed",
    "GeomShapeOpen",
    "GeomShapes",
    "GeomShapesAtomic",
    "GeomShapesClosed",
    "GeomShapesNative",
    "GeomShapesOpen",
    "GeomStadium",
    "GeomTrapezoid",
]
