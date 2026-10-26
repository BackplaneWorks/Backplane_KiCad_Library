# KicadModTree is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KicadModTree is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>

"""The 'node' library."""

from KicadModTree.KicadFileHandler import KicadFileHandler
from KicadModTree.ModArgparser import ModArgparser
from KicadModTree.nodes import (
    Arc,
    ChamferedPad,
    ChamferedPadGrid,
    ChamferedRectangle,
    ChamferSelPadGrid,
    Circle,
    CompoundPolygon,
    Container,
    Cross,
    Cruciform,
    EmbeddedFonts,
    ExposedPad,
    Footprint,
    FootprintType,
    Group,
    Hatch,
    Keepouts,
    Line,
    Model,
    MultipleParentsError,
    Node,
    Shape,
    Pad,
    PadArray,
    PadConnection,
    Polygon,
    PolygonLine,
    Property,
    Rectangle,
    RecursionDetectedError,
    ReferencedPad,
    RingPad,
    Rotation,
    RoundRectangle,
    Stadium,
    Text,
    Translation,
    Trapezoid,
    Zone,
    ZoneFill,
)
from KicadModTree.util import (
    ChamferSizeHandler,
    LineStyle,
    RoundRadiusHandler,
    shape_to_node,
)
from kilibs.geom.vector import Vector2D  # TODO remove this import.

__all__ = [
    "Arc",
    "ChamferedRectangle",
    "ChamferSelPadGrid",
    "ChamferedPad",
    "ChamferedPadGrid",
    "ChamferSizeHandler",
    "Circle",
    "CompoundPolygon",
    "Container",
    "Cross",
    "Cruciform",
    "EmbeddedFonts",
    "ExposedPad",
    "Footprint",
    "FootprintType",
    "Group",
    "Hatch",
    "Keepouts",
    "KicadFileHandler",
    "Line",
    "LineStyle",
    "ModArgparser",
    "Model",
    "MultipleParentsError",
    "Node",
    "Shape",
    "Pad",
    "PadArray",
    "PadConnection",
    "Polygon",
    "PolygonLine",
    "Property",
    "RecursionDetectedError",
    "Rectangle",
    "ReferencedPad",
    "RingPad",
    "Rotation",
    "RoundRadiusHandler",
    "RoundRectangle",
    "shape_to_node",
    "Stadium",
    "Text",
    "Translation",
    "Trapezoid",
    "Vector2D",
    "Zone",
    "ZoneFill",
]
