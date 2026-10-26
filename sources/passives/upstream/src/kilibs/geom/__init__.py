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

"""Geometric shapes and tools."""

# We don't have to import everything here, but the basics avoid a lot of verbose
# imports in client code (e.g. `from kilibs.geom import Vector2D, Rectangle`,
# rather than importing in two statements).

from __future__ import annotations

from .bounding_box import BoundingBox
from .corner_selection import CornerSelection
from .direction import Direction
from .shapes import (
    GeomArc,
    GeomChamferedRectangle,
    GeomCircle,
    GeomCompoundPolygon,
    GeomCross,
    GeomCruciform,
    GeomLine,
    GeomPolygon,
    GeomRectangle,
    GeomRoundRectangle,
    GeomShape,
    GeomShapeClosed,
    GeomShapeOpen,
    GeomShapes,
    GeomShapesAtomic,
    GeomShapesClosed,
    GeomShapesNative,
    GeomShapesOpen,
    GeomStadium,
    GeomTrapezoid,
)
from .tolerances import MIN_SEGMENT_LENGTH, TOL_MM, tol_deg
from .vector import Vec2DCompatible, Vec3DCompatible, Vector2D, Vector3D

__all__ = [
    "BoundingBox",
    "CornerSelection",
    "Direction",
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
    "GeomShapes",
    "GeomShapeClosed",
    "GeomShapesClosed",
    "GeomShapeOpen",
    "GeomShapesOpen",
    "GeomShapesAtomic",
    "GeomShapesNative",
    "GeomStadium",
    "GeomTrapezoid",
    "MIN_SEGMENT_LENGTH",
    "TOL_MM",
    "tol_deg",
    "Vec2DCompatible",
    "Vec3DCompatible",
    "Vector2D",
    "Vector3D",
]
