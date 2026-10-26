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

"""Node classes."""

# Node must be on top to prevent cyclic imports:
from .Node import Node  # isort: skip
from .base import (
    Arc,
    Circle,
    CompoundPolygon,
    EmbeddedFonts,
    Group,
    Hatch,
    Keepouts,
    Line,
    Model,
    Pad,
    PadConnection,
    Point,
    Polygon,
    Property,
    Rectangle,
    ReferencedPad,
    Text,
    Zone,
    ZoneFill,
)
from .Container import Container, MultipleParentsError, RecursionDetectedError
from .Footprint import Footprint, FootprintType
from .Shape import Shape
from .specialized import (
    ChamferedPad,
    ChamferedPadGrid,
    ChamferedRectangle,
    ChamferSelPadGrid,
    Cross,
    Cruciform,
    ExposedPad,
    PadArray,
    PolygonLine,
    RingPad,
    Rotation,
    RoundRectangle,
    Stadium,
    Translation,
    Trapezoid,
)

__all__ = [
    "Arc",
    "Circle",
    "CompoundPolygon",
    "EmbeddedFonts",
    "Group",
    "Line",
    "Model",
    "Pad",
    "ReferencedPad",
    "Point",
    "Polygon",
    "Rectangle",
    "Property",
    "Text",
    "Hatch",
    "Keepouts",
    "PadConnection",
    "Zone",
    "ZoneFill",
    "Footprint",
    "FootprintType",
    "Container",
    "MultipleParentsError",
    "Node",
    "RecursionDetectedError",
    "Shape",
    "ChamferedPad",
    "ChamferedPadGrid",
    "ChamferedRectangle",
    "ChamferSelPadGrid",
    "Cross",
    "Cruciform",
    "ExposedPad",
    "PadArray",
    "PolygonLine",
    "RingPad",
    "Rotation",
    "RoundRectangle",
    "Stadium",
    "Translation",
    "Trapezoid",
]
