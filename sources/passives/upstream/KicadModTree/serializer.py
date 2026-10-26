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

"""Class definition for a node serializer."""

import functools
import re
from enum import Enum
from typing import Any, cast

from KicadModTree.nodes.base.Arc import Arc
from KicadModTree.nodes.base.Circle import Circle
from KicadModTree.nodes.base.CompoundPolygon import CompoundPolygon
from KicadModTree.nodes.base.EmbeddedFonts import EmbeddedFonts
from KicadModTree.nodes.base.Group import Group
from KicadModTree.nodes.base.Line import Line
from KicadModTree.nodes.base.Model import Model
from KicadModTree.nodes.base.Pad import Pad, ReferencedPad
from KicadModTree.nodes.base.Point import Point
from KicadModTree.nodes.base.Polygon import Polygon
from KicadModTree.nodes.base.Rectangle import Rectangle
from KicadModTree.nodes.base.Text import Property, Text
from KicadModTree.nodes.base.Zone import Hatch, Keepouts, PadConnection, Zone, ZoneFill
from KicadModTree.nodes.Node import TStamp
from KicadModTree.nodes.Shape import Shape
from KicadModTree.util.line_style import LineStyle
from KicadModTree.util.shape_to_node import shape_to_node
from kilibs.geom.tolerances import TOL_MM
from kilibs.geom.vector import Vector2D

_DEFAULT_LAYER_WIDTH = {
    "F.SilkS": 0.12,
    "B.SilkS": 0.12,
    "F.Fab": 0.10,
    "B.Fab": 0.10,
    "F.CrtYd": 0.05,
    "B.CrtYd": 0.05,
}
"""Default width for the most common layers."""

_DEFAULT_WIDTH = 0.15
"""Default width for the layers not listed in _DEFAULT_LAYER_WIDTH."""

_DEFAULT_WIDTH_POLYGON_PAD = 0.0
"""Default width of the outline of custom sized pads."""


class SerializerPriority:
    """A class to sort nodes according to their priorities."""

    class _NodePriority(Enum):
        """Node priorities."""

        SHAPE = 100
        """Priority of shape nodes."""
        TEXT = 200
        """Priority of text nodes."""
        PAD = 300
        """Priority of pad nodes."""
        POINT = 350
        """Priority of point nodes."""
        ZONE = 400
        """Priority of zone nodes."""
        GROUP = 600
        """Priority of group nodes."""
        EMBEDDED_FONT = 1000
        """Priority of embedded font nodes."""
        MODEL = 1100
        """Priority of model nodes."""

    class _ShapePriority(Enum):
        """Shape priorities."""

        LINE = 0
        """Priority of a line node."""
        RECTANGLE = 1
        """Priority of a rectangle node."""
        ARC = 2
        """Priority of an arc node."""
        CIRCLE = 3
        """Priority of a circle node."""
        POLYGON = 4
        """Priority of a polygon node."""
        COMPOUND_POLYGON = 4
        """Priority of a compound polygon node."""
        BEZIER = 5
        """Priority of a bezier node."""

    _LAYER_PRIORITY_MAP = {
        # These are specials in this order in formatLayers()
        # which come first
        "*.Cu": -1000,
        "F&B.Cu": -999,
        "*.Adhes": -998,
        "*.Paste": -997,
        "*.SilkS": -996,
        "*.Mask": -995,
        "*.CrtYd": -994,
        "*.Fab": -993,
        # Single layer IDs come after
        # Copper layers are even numbers
        "F.Cu": 0,
        "B.Cu": 2,
        "F.Mask": 1,
        "B.Mask": 3,
        "F.SilkS": 5,
        "B.SilkS": 7,
        "F.Adhes": 9,
        "B.Adhes": 11,
        "F.Paste": 13,
        "B.Paste": 15,
        "Dwgs.User": 17,
        "Cmts.User": 19,
        "Eco1.User": 21,
        "Eco2.User": 23,
        "Edge.Cuts": 25,
        "Margin": 27,
        "B.CrtYd": 29,
        "F.CrtYd": 31,
        "B.Fab": 33,
        "F.Fab": 35,
    }

    @staticmethod
    def sort_layers(layers: list[str]) -> list[str]:
        """Sort layers by their prorities in which they shall be serialized.

        Args:
            layers: The list of layer names.

        Returns:
            The list of layer names sorted by their priorities.
        """
        return sorted(layers, key=SerializerPriority.get_layer_priority)

    @staticmethod
    def get_sorted_layer_priorities(layers: list[str]) -> list[int]:
        """Get the KiCad sorting keys for a list of layer names.

        Args:
            layers: The list of layer names.

        Returns:
            A list of numbers corresponding to the sorted priorities of the given layers.
        """
        priorities: list[int] = []
        for layer in layers:
            priorities.append(SerializerPriority.get_layer_priority(layer))
        priorities.sort()
        return priorities

    @staticmethod
    def get_layer_priority(layer: str) -> int:
        """Get the KiCad sorting key for a layer name.

        Args:
            layer: The layer name.

        Returns:
            The priority of the layer.
        """
        # Approximate sorting order from PCB_IO_KICAD_SEXPR::formatLayers()
        try:
            return SerializerPriority._LAYER_PRIORITY_MAP[layer]
        except KeyError:
            # inner layers: even numbers from 4
            if m := re.match(r"^In(\d+)\.Cu$", layer):
                return (int(m.group(1)) + 1) * 2
            # user layers from 39 onwards
            if m := re.match(r"^User\.(\d)$", layer):
                return 38 + int(m.group(1))

        raise ValueError(f"Unhandled layer for sorting: {layer}")

    @staticmethod
    def get_sort_key_text(text: Text) -> list[Any]:
        """Return the sort key of the text."""
        return [
            SerializerPriority._NodePriority.TEXT.value,
            SerializerPriority.get_layer_priority(text.layer),
            round(text.at.x, 6),
            round(text.at.y, 6),
            round(text.rotation, 6),
            round(text.size.x, 6),
            round(text.size.y, 6),
            round(text.thickness, 6),
            # Bold
            # Italic
            text.mirror,
            # Line spacing
            text.text,
        ]

    @staticmethod
    def get_sort_key_line(line: Line) -> list[Any]:
        """Return the sort key of the line."""
        return [
            SerializerPriority._NodePriority.SHAPE.value,
            SerializerPriority.get_layer_priority(line.layer),
            SerializerPriority._ShapePriority.LINE.value,
            round(line.start.x, 6),
            round(line.start.y, 6),
            round(line.end.x, 6),
            round(line.end.y, 6),
        ]

    @staticmethod
    def get_sort_key_arc(arc: Arc) -> list[Any]:
        """Return the sort key of the arc."""
        start = arc.start
        end = arc.end
        # Match KiCad normalisation of negative arc angles
        # (and the one in _serialize_ArcPoints).
        if arc.angle < 0:
            start, end = end, start
        return [
            SerializerPriority._NodePriority.SHAPE.value,
            SerializerPriority.get_layer_priority(arc.layer),
            SerializerPriority._ShapePriority.ARC.value,
            round(start.x, 6),
            round(start.y, 6),
            round(end.x, 6),
            round(end.y, 6),
            round(arc.center.x, 6),
            round(arc.center.y, 6),
        ]

    @staticmethod
    def get_sort_key_circle(circle: Circle) -> list[Any]:
        """Return the sort key of the circle."""
        return [
            SerializerPriority._NodePriority.SHAPE.value,
            SerializerPriority.get_layer_priority(circle.layer),
            SerializerPriority._ShapePriority.CIRCLE.value,
            round(circle.center.x, 6),
            round(circle.center.y, 6),
            round(circle.radius, 6),
        ]

    @staticmethod
    def get_sort_key_rectangle(rectangle: Rectangle) -> list[Any]:
        """Return the sort key of the rectangle."""
        return [
            SerializerPriority._NodePriority.SHAPE.value,
            SerializerPriority.get_layer_priority(rectangle.layer),
            SerializerPriority._ShapePriority.RECTANGLE.value,
            round(rectangle.top_left.x, 6),
            round(rectangle.top_left.y, 6),
            round(rectangle.bottom_right.x, 6),
            round(rectangle.bottom_right.y, 6),
        ]

    @staticmethod
    def get_sort_key_polygon(polygon: Polygon) -> list[Any]:
        """Return the sort key of the polygon."""
        return [
            SerializerPriority._NodePriority.SHAPE.value,
            SerializerPriority.get_layer_priority(polygon.layer),
            SerializerPriority._ShapePriority.POLYGON.value,
            len(polygon.points),
        ] + [[round(pt.x, 6), round(pt.y, 6)] for pt in polygon.points]

    @staticmethod
    def get_sort_key_compound_polygon(cpoly: CompoundPolygon) -> list[Any]:
        """Return the sort key of the compound polygon."""
        points_and_arcs = cpoly.get_fp_poly_elements()
        keys: list[float] = []
        for point_or_arc in points_and_arcs:
            if isinstance(point_or_arc, Vector2D):
                keys.extend([round(point_or_arc.x, 6), round(point_or_arc.y, 6)])
            # else:
            #     keys.extend(
            #         [
            #             round(point_or_arc.start.x, 6),
            #             round(point_or_arc.start.y, 6),
            #             round(point_or_arc.end.x, 6),
            #             round(point_or_arc.end.y, 6),
            #             round(point_or_arc.center.x, 6),
            #             round(point_or_arc.center.y, 6),
            #         ]
            #     )
        return [
            SerializerPriority._NodePriority.SHAPE.value,
            SerializerPriority.get_layer_priority(cpoly.layer),
            SerializerPriority._ShapePriority.POLYGON.value,
            len(points_and_arcs),
            keys,
        ]

    @staticmethod
    def get_sort_key_zone(zone: Zone) -> list[Any]:
        """Return the sort key of the zone."""
        return [
            SerializerPriority._NodePriority.ZONE.value,
            zone.priority if zone.priority else 0,
            [SerializerPriority.get_layer_priority(layer) for layer in zone.layers],
            len(zone.nodes.points),
            [[round(pt.x, 6), round(pt.y, 6)] for pt in zone.nodes.points],
        ]

    @staticmethod
    def _pad_num_key(n: str) -> list[tuple[int, str] | tuple[int, int]]:
        # We want to sort pads with multiple name components such that A2 comes
        # after A1 and before A10, and all the Ax come before all Bx.
        # Example sort order: "", "0", "1", "2", "10", "A", "A1", "A2", "A10",
        # "A100", "B", "B1"...
        # To achieve this, we split by name components such that digit sequences
        # stay as individual tokens. We will later compare lists of tuples, with the
        # list length being the component count.

        # Split the strings into substrings containing digits and those containing
        # everything else. For example: 'a10.2' => ['a', '10', '.', '2']
        substrings = cast(list[str], re.findall(r"\d+|[^\d]+", n))
        # To avoid comparing ints to strings, we create tuples with each item and
        # its category number. Ints sort before strings, so they are category 1, and
        # strings get category 2.
        # For example: ['a', '10', '.', '2'] => [(2, 'a'), (1, 10), (2, '.'), (1, 2)]
        return [
            (1, int(substr)) if substr.isdigit() else (2, substr)
            for substr in substrings
        ]

    @staticmethod
    def _pad_shape_key_func(shape: str) -> int:
        shapes = ["circle", "rect", "oval", "trapezoid", "roundrect", "custom"]
        try:
            return shapes.index(shape)
        except ValueError:
            return 1000

    @staticmethod
    def get_sort_key_pad(pad: Pad) -> list[Any]:
        """Return the sort key of the pad."""

        # Approximate sorting order from FOOTPRINT::cmp_pads in KiCad's
        # pcbnew/footprint.cpp.
        return [
            SerializerPriority._NodePriority.PAD.value,
            SerializerPriority._pad_num_key(str(pad.number)),
            round(pad.at.x, 6),
            round(pad.at.y, 6),
            round(pad.size.x, 6),
            round(pad.size.y, 6),
            SerializerPriority._pad_shape_key_func(pad.shape),
            # SerializerPriority.get_sorted_layer_priorities(pad.layers),
        ]

    @staticmethod
    def get_sort_key_referenced_pad(referenced_pad: ReferencedPad) -> list[Any]:
        """Return the sort key of the referenced pad."""
        ref_pad = referenced_pad.reference_pad
        return [
            SerializerPriority._NodePriority.PAD.value,
            SerializerPriority._pad_num_key(str(referenced_pad.number)),
            round(referenced_pad.at.x, 6),
            round(referenced_pad.at.y, 6),
            round(ref_pad.size.x, 6),
            round(ref_pad.size.y, 6),
            SerializerPriority._pad_shape_key_func(ref_pad.shape),
            # SerializerPriority.get_sorted_layer_priorities(ref_pad.layers),
        ]

    @staticmethod
    def get_sort_key_embedded_fonts(fonts: EmbeddedFonts) -> list[Any]:
        """Return the sort key of the embedded fonts."""
        return [SerializerPriority._NodePriority.EMBEDDED_FONT.value]

    @staticmethod
    def get_sort_key_group(group: Group) -> list[Any]:
        """Return the sort key of the group."""
        keys: list[Any] = [SerializerPriority._NodePriority.GROUP.value]
        if group.has_valid_timestamp():
            keys += [group.get_timestamp()]
        if member_nodes := group.get_group_member_nodes():
            keys += [len(member_nodes)]
        return keys

    @staticmethod
    def get_sort_key_point(point: Point) -> list[Any]:
        """Return the sort key of the point."""
        return [
            SerializerPriority._NodePriority.POINT.value,
            SerializerPriority.get_layer_priority(point.layer),
            round(point.at.x, 6),
            round(point.at.y, 6),
            round(point.size, 6),
        ]

    @staticmethod
    def get_sort_key_model(model: Model) -> list[Any]:
        """Return the sort key of the embedded font."""
        return [SerializerPriority._NodePriority.MODEL.value]


class Serializer:
    """A class to serialize properties."""

    def __init__(self, indent: str = "") -> None:
        """Create an instance of a serializer.

        Args:
            indent: The initial indentation level.
        """

        # Instance attributes:
        self.indent: str
        """The current indentation level."""
        self.content: list[str]
        """The content of the serializer."""

        self.indent = indent
        self.content = []

    def to_string(self) -> str:
        """Convert the serializer's content to a string."""
        return "".join(self.content)

    def start_block(self, text: str) -> None:
        """Start a new block.

        Args:
            text: The designator of the new block.
        """
        self.content.append(f"{self.indent}({text}\n")
        self.indent += "\t"

    def end_block(self) -> None:
        """End a block."""
        self.indent = self.indent[:-1]
        self.content.append(f"{self.indent})\n")

    def add_symbol(self, designator: str, symbol: str) -> None:
        """Add a symbol to the serializer.

        Symbols are strings that are not quoted in the output.

        Args:
            designator: The designator.
            symbol: The symbol.
        """
        self.content.append(f"{self.indent}({designator} {symbol})\n")

    def add_symbols(self, designator: str, symbols: list[str]) -> None:
        """Add a list of symbol to the serializer.

        Symbols are strings that are not quoted in the output.

        Args:
            designator: The designator.
            symbols: The list of symbols.
        """
        symbol_list: list[str] = []
        for symbol in symbols:
            symbol_list.append(f" {symbol}")
        self.content.append(f"{self.indent}({designator}{''.join(symbol_list)})\n")

    def add_string(self, designator: str, string: str) -> None:
        """Add a string to the serializer.

        Strings are quoted in the output.

        Args:
            designator: The designator.
            string: The string.
        """
        clean_string = string.replace('"', '\\"')
        self.content.append(f'{self.indent}({designator} "{clean_string}")\n')

    def add_strings(self, designator: str | None, strings: list[str]) -> None:
        """Add a list of strings to the serializer.

        Strings are quoted in the output.

        Args:
            designator: The designator. None if no designator is to be used.
            strings: The list of strings.
        """
        symbol_list: list[str] = []
        for string in strings:
            clean_string = string.replace('"', '\\"')
            symbol_list.append(f'"{clean_string}"')

        if designator is None:
            designator = ""
        elif strings:
            designator += " "

        self.content.append(f"{self.indent}({designator}{' '.join(symbol_list)})\n")

    @staticmethod
    def _float_to_str(number: float) -> str:
        """Convert a float to a string.

        Args:
            number: the number to convert.

        Returns:
            The converted float as a string. The number is rounded to 6 decimal places after
            the dot.
        """
        result = ("%f" % number).rstrip("0").rstrip(".")
        if result == "-0":
            return "0"
        return result

    def add_float(self, designator: str, f1: float) -> None:
        """Add a float to the serializer.

        Args:
            designator: The designator.
            f1: The float.
        """
        s1 = Serializer._float_to_str(f1)
        self.content.append(f"{self.indent}({designator} {s1})\n")

    def add_2_floats(self, designator: str, f1: float, f2: float) -> None:
        """Add two floats to the serializer.

        Args:
            designator: The designator.
            f1: The first float.
            f2: The second float.
        """
        s1 = Serializer._float_to_str(f1)
        s2 = Serializer._float_to_str(f2)
        self.content.append(f"{self.indent}({designator} {s1} {s2})\n")

    def add_3_floats(self, designator: str, f1: float, f2: float, f3: float) -> None:
        """Add three floats to the serializer.

        Args:
            designator: The designator.
            f1: The first float.
            f2: The second float.
            f3: The third float.
        """
        s1 = Serializer._float_to_str(f1)
        s2 = Serializer._float_to_str(f2)
        s3 = Serializer._float_to_str(f3)
        self.content.append(f"{self.indent}({designator} {s1} {s2} {s3})\n")

    def add_int(self, designator: str, num: int) -> None:
        """Add an integer to the serializer.

        Args:
            designator: The designator.
            num: The integer.
        """
        self.content.append(f"{self.indent}({designator} {str(num)})\n")

    def add_bool(self, designator: str, b: bool) -> None:
        """Add a boolean to the serializer.

        Args:
            designator: The designator.
            b: The boolean.
        """
        self.content.append(f"{self.indent}({designator} {'yes' if b else 'no'})\n")

    def add_optional_bool(self, designator: str, b: bool | None) -> None:
        """Add an optional boolean to the serializer (yes/no/none).

        See KICAD_FORMAT::FormatOptBool in KiCad
        """
        if b is not None:
            self.add_bool(designator, b)
        else:
            self.add_symbol(designator, "none")

    def _add_stroke(self, node: Shape) -> None:
        """Serialize a stroke.

        Args:
            node: The node whose stroke is to be serialized.
        """
        self.content.append(self._get_stroke_string(node.layer, node.width, node.style))

    @functools.cache
    def _get_stroke_string(
        self, layer: str, width: float | None, style: LineStyle
    ) -> str:
        """Return a cachable string for the stroke parameters.

        Args:
            layer: The layer to draw on (used to fetch default values).
            width: The stroke width.
            style: The stroke style.
        """
        ser = Serializer(self.indent)
        if width is None:
            width = _DEFAULT_LAYER_WIDTH.get(layer, _DEFAULT_WIDTH)
        ser.start_block("stroke")
        ser.add_float("width", width)
        ser.add_symbol("type", style.value)
        ser.end_block()
        return ser.to_string()

    def _add_layer(self, node: Shape) -> None:
        """Serialize the layer of a node.

        Args:
            node: The node whose layer is to be serialized.
        """
        self.add_string("layer", node.layer)

    def _add_fill(self, node: Shape) -> None:
        """Serialize the fill type of a node.

        Args:
            node: The node whose fill type is to be serialized.
        """
        self.add_symbol("fill", "yes" if node.fill else "no")

    def _add_text_base(self, text_base: Text | Property) -> None:
        """Serialize a text base.

        Args:
            text_base: The text base.
        """
        # KiCad 8 always writes the 0 rotation
        rotation = 0.0 if not text_base.rotation else text_base.rotation
        self.add_3_floats("at", text_base.at.x, text_base.at.y, rotation)
        if text_base.unlocked:
            self.add_bool("unlocked", True)
        self.add_string("layer", text_base.layer)
        if text_base.hide:
            self.add_bool("hide", True)
        self.start_block("effects")
        self.start_block("font")
        self.add_2_floats("size", text_base.size.x, text_base.size.y)
        self.add_float("thickness", text_base.thickness)
        self.end_block()
        just: list[str] = []
        if text_base.mirror:
            just.append("mirror")
        if text_base.justify:
            if isinstance(text_base.justify, list):
                just.extend(text_base.justify)
            else:
                just.append(text_base.justify)
        if just:
            self.add_symbols("justify", just)
        self.end_block()

    def add_property(self, property: Property) -> None:
        """Serialize a property.

        Args:
            property: The property.
        """
        self.start_block(f'property "{property.name}" "{property.text}"')
        self._add_text_base(property)
        self.end_block()

    def add_text(self, text: Text) -> None:
        """Serialize a text.

        Args:
            text: The text.
        """
        self.start_block(f'fp_text user "{text.text}"')
        self._add_text_base(text)
        self.end_block()

    def add_pad_zone_connection(self, zone_connection: Pad.ZoneConnection) -> None:
        """Serialize a zone connection.

        Args:
            zone_connection: The zone connection.
        """
        # Inherited zone connection is implicit in the s-exp by a
        # missing zone_connection node:
        if not zone_connection == Pad.ZoneConnection.INHERIT:
            self.add_int("zone_connect", zone_connection.value)

    def _add_line_points(self, line: Line) -> None:
        """Serialize the end points of a line.

        Args:
            line: The line.
        """
        self.add_2_floats("start", line.start.x, line.start.y)
        self.add_2_floats("end", line.end.x, line.end.y)

    def _add_rect_points(self, rect: Rectangle) -> None:
        """Serialize the start/end corners points of a rectangle.

        Args:
            rect: The rectangle.
        """
        if not rect.angle:
            self.add_2_floats("start", rect.top_left.x, rect.top_left.y)
            self.add_2_floats("end", rect.bottom_right.x, rect.bottom_right.y)
        else:
            raise ValueError("Cannot serialize a rotated rectangle as two points")

    def add_line(self, line: Line) -> None:
        """Serialize a line.

        Args:
            line: The line.
        """
        self.start_block("fp_line")
        # self.add_2_floats("start", line.start.x, line.start.y):
        start_x = Serializer._float_to_str(line.start.x)
        start_y = Serializer._float_to_str(line.start.y)
        end_x = Serializer._float_to_str(line.end.x)
        end_y = Serializer._float_to_str(line.end.y)
        self.content.append(
            f"{self.indent}(start {start_x} {start_y})\n"
            f"{self.indent}(end {end_x} {end_y})\n"
        )
        self._add_stroke(line)
        # self._add_layer(line)
        self.add_string("layer", line.layer)
        self.end_block()

    def _add_arc_points_back_compatible(self, arc: Arc) -> None:
        """Serialize the points of an arc.

        Args:
            arc: The arc.
        """
        start = arc.start
        end = arc.end
        # Match KiCad normalisation of negative arc angles. Swap start and end for
        # negative angles to overcome a bug in KiCAD v6 and some v7 versions.
        if arc.angle < 0:
            start, end = end, start
        self.add_2_floats("start", start.x, start.y)
        self.add_2_floats("mid", arc.mid.x, arc.mid.y)
        self.add_2_floats("end", end.x, end.y)

    def _add_arc_points(self, arc: Arc) -> None:
        """Serialize the points of an arc.

        Args:
            arc: The arc.
        """
        self.add_2_floats("start", arc.start.x, arc.start.y)
        self.add_2_floats("mid", arc.mid.x, arc.mid.y)
        self.add_2_floats("end", arc.end.x, arc.end.y)

    def add_arc(self, arc: Arc) -> None:
        """Serialize an arc.

        Args:
            ser: The serializer that converts the serial expressions and stores the
                result.
        """
        self.start_block("fp_arc")
        self._add_arc_points_back_compatible(arc)
        self._add_stroke(arc)
        self._add_layer(arc)
        self.end_block()

    def _add_circle_points(self, circle: Circle) -> None:
        """Serialize the points of a circle.

        Args:
            circle: The circle.
        """
        self.add_2_floats("center", circle.center.x, circle.center.y)
        self.add_2_floats("end", circle.center.x + circle.radius, circle.center.y)

    def add_circle(self, circle: Circle) -> None:
        """Serialize a circle.

        Args:
            circle: The circle.
        """
        self.start_block("fp_circle")
        self.add_2_floats("center", circle.center.x, circle.center.y)
        self.add_2_floats("end", circle.center.x + circle.radius, circle.center.y)
        self._add_stroke(circle)
        self._add_fill(circle)
        self._add_layer(circle)
        self.end_block()

    def add_rectangle(self, rect: Rectangle) -> None:
        """Serialize a rectangle.

        Args:
            rect: The rectangle.
        """
        if not rect.angle:
            self.start_block("fp_rect")
            self._add_rect_points(rect)
        else:
            # Treat as a polygon
            self.start_block("fp_poly")
            self._add_polygon_point_list(rect.points)

        # These are the same for both rectangles and polygons
        self._add_stroke(rect)
        self._add_fill(rect)
        self._add_layer(rect)
        self.end_block()

    def _add_polygon_point_list(self, points: list[Vector2D]) -> None:
        """Serialize the points of a polygon.

        Args:
            polygon: The polygon.
        """
        self.start_block("pts")
        for point in points:
            self.add_2_floats("xy", point.x, point.y)
        self.end_block()

    def add_polygon(self, polygon: Polygon) -> None:
        """Serialize a polygon.

        Args:
            polygon: The polygon
        """
        self.start_block("fp_poly")
        self._add_polygon_point_list(polygon.points)
        self._add_stroke(polygon)
        self._add_fill(polygon)
        self._add_layer(polygon)
        self.end_block()

    def add_compound_polygon(self, cpoly: CompoundPolygon) -> None:
        """Serialize a compound polygon.

        Args:
            cpoly: The compound polygon.
        """
        self.start_block("fp_poly")
        self.start_block("pts")
        for geom in cpoly.get_fp_poly_elements():
            if isinstance(geom, Vector2D):
                self.add_2_floats("xy", geom.x, geom.y)
            else:
                self.start_block("arc")
                self._add_arc_points(geom)
                self.end_block()
        self.end_block()
        self._add_stroke(cpoly)
        self._add_fill(cpoly)
        self._add_layer(cpoly)
        self.end_block()

    def _add_pad_connection(self, pad_connection: PadConnection) -> None:
        """Serialize a pad connection.

        Args:
            pad_connection: The pad connection
        """
        if pad_connection.type is not PadConnection.THERMAL_RELIEF:
            self.start_block(f"connect_pads {pad_connection.type}")
        else:
            self.start_block("connect_pads")
        self.add_float("clearance", pad_connection.clearance)
        self.end_block()

    def _add_keepouts(self, keepouts: Keepouts) -> None:
        """Serialize a keepout.

        Args:
            keepout: The keepout
        """

        def is_allowed(property: bool) -> str:
            return "allowed" if property == Keepouts.ALLOW else "not_allowed"

        self.start_block("keepout")
        self.add_symbol("tracks", is_allowed(keepouts.tracks))
        self.add_symbol("vias", is_allowed(keepouts.vias))
        self.add_symbol("pads", is_allowed(keepouts.pads))
        self.add_symbol("copperpour", is_allowed(keepouts.copperpour))
        self.add_symbol("footprints", is_allowed(keepouts.footprints))
        self.end_block()

    def _add_hatch(self, hatch: Hatch) -> None:
        """Serialize a hatch.

        Args:
            hatch: The hatch.
        """
        self.add_float(f"hatch {hatch.style}", hatch.pitch)

    def _add_zone_fill(self, zone_fill: ZoneFill) -> None:
        """Serialize the keepout.

        Args:
            ser: The serializer that converts the serial expressions and stores the
                result.
        """
        # "yes" if we do have a fill
        self.start_block("fill yes" if zone_fill.fill != ZoneFill.FILL_NONE else "fill")

        # soild is encoded as no mode
        if zone_fill.fill not in [ZoneFill.FILL_NONE, ZoneFill.FILL_SOLID]:
            self.add_string("mode", zone_fill.fill)

        # Thermal gap and bridge with aren't optional
        self.add_float("thermal_gap", zone_fill.thermal_gap)
        self.add_float("thermal_bridge_width", zone_fill.thermal_bridge_width)

        if zone_fill.smoothing is not None:
            self.add_symbol("smoothing", zone_fill.smoothing)
            if zone_fill.smoothing_radius > 0:
                self.add_float("radius", zone_fill.smoothing_radius)

        # KiCad only outputs the island removal mode if it's not the 'remove' default
        if (
            zone_fill.island_removal_mode is not None
            and zone_fill.island_removal_mode != ZoneFill.ISLAND_REMOVAL_REMOVE
        ):
            # Look up the encoding
            island_removal_mode = {
                ZoneFill.ISLAND_REMOVAL_REMOVE: 0,
                ZoneFill.ISLAND_REMOVAL_FILL: 1,
                ZoneFill.ISLAND_REMOVAL_MINIMUM_AREA: 2,
            }[zone_fill.island_removal_mode]
            self.add_int("island_removal_mode", island_removal_mode)

            # only valid in mode 2
            if (
                zone_fill.island_removal_mode == "minimum_area"
                and zone_fill.island_area_min is not None
            ):
                self.add_float("island_area_min", zone_fill.island_area_min)

        if zone_fill.hatch_thickness:
            self.add_float("hatch_thickness", zone_fill.hatch_thickness)
        if zone_fill.hatch_gap:
            self.add_float("hatch_gap", zone_fill.hatch_gap)
        if zone_fill.hatch_orientation:
            self.add_float("hatch_orientation", zone_fill.hatch_orientation)
        if zone_fill.hatch_smoothing_level:
            self.add_string("hatch_smoothing_level", zone_fill.hatch_smoothing_level)
        if zone_fill.hatch_smoothing_value:
            self.add_float("hatch_smoothing_value", zone_fill.hatch_smoothing_value)
        if zone_fill.hatch_border_algorithm:
            self.add_string("hatch_border_algorithm", zone_fill.hatch_border_algorithm)
        if zone_fill.hatch_min_hole_area:
            self.add_float("hatch_min_hole_area", zone_fill.hatch_min_hole_area)

        self.end_block()

    def add_zone(self, zone: Zone) -> None:
        """Serialize a zone.

        Args:
            zone: The zone
        """
        self.start_block("zone")
        self.add_int("net", zone.net)
        self.add_string("net_name", zone.net_name)
        self.add_strings("layers", SerializerPriority.sort_layers(zone.layers))
        self.add_string("name", zone.name)
        self._add_hatch(zone.hatch)

        # Optional node
        if zone.priority is not None:
            self.add_int("priority", zone.priority)

        self._add_pad_connection(zone.connect_pads)
        # technically optional, but we can just always put it in
        self.add_float("min_thickness", zone.min_thickness)
        self.add_bool("filled_areas_thickness", zone.filled_areas_thickness)

        # Rule areas always seem to output keepout and placement
        if zone.keepouts is not None:  # is_rule_area
            self._add_keepouts(zone.keepouts)
            self.start_block("placement")
            self.add_bool("enabled", False)
            self.add_string("sheetname", "")
            self.end_block()

        self._add_zone_fill(zone.fill)
        self.start_block("polygon")
        self.start_block("pts")
        for point in zone.nodes.points:
            self.add_2_floats("xy", point.x, point.y)
        self.end_block()
        self.end_block()
        self.end_block()

    def _add_fab_property(self, fab_property: Pad.FabProperty) -> None:
        """Serialize a fab property.

        Args:
            fab_property: The fab property.
        """
        mapping = {
            Pad.FabProperty.BGA: "pad_prop_bga",
            Pad.FabProperty.FIDUCIAL_GLOBAL: "pad_prop_pad_prop_heatsink",
            Pad.FabProperty.FIDUCIAL_LOCAL: "pad_prop_fiducial_loc",
            Pad.FabProperty.HEATSINK: "pad_prop_heatsink",
            Pad.FabProperty.MECHANICAL: "pad_prop_mechanical",
            Pad.FabProperty.TESTPOINT: "pad_prop_testpoint",
            Pad.FabProperty.CASTELLATED: "pad_prop_castellated",
        }
        self.add_symbol("property", mapping[fab_property])

    def _add_pad_thermal_bridge_angle(self, pad: Pad) -> None:
        """Serialize the pad's thermal bridge angle.

        Args:
            pad: The pad.
        """
        # KiCad (9, at least) doesn't output this in the s-expr in it's slightly
        # esoteric default state, but pads do always have a valid angle.
        if pad.shape == Pad.SHAPE_CIRCLE or (
            pad.shape == Pad.SHAPE_CUSTOM and pad.anchor_shape == Pad.SHAPE_CIRCLE
        ):
            tba_default = 45
        else:
            tba_default = 90
        if abs(pad.thermal_bridge_angle - tba_default):
            self.add_float("thermal_bridge_angle", pad.thermal_bridge_angle)

    def _add_pad_custom_primitives(self, pad: Pad) -> None:
        """Serialize the pad's custom primitives.

        Args:
            pad: The pad.
        """
        from KicadModTree.nodes.base import Arc, Circle, Line, Polygon

        SUPPORTED_TYPES = [
            "Arc",
            "Circle",
            "Rectangle",
            "Line",
            "Pad",
            "Polygon",
            "Text",
        ]

        all_primitives: list[Shape] = []
        for p in pad.primitives:
            if p.__class__.__name__ in SUPPORTED_TYPES:
                all_primitives.append(p)
            else:
                for shape in p.get_atomic_shapes():
                    all_primitives.append(
                        shape_to_node(shape, p.layer, p.width, p.style)
                    )

        grouped_nodes: dict[str, list[Shape]] = {}

        for single_node in all_primitives:
            node_type = single_node.__class__.__name__
            current_nodes = grouped_nodes.get(node_type, [])
            current_nodes.append(single_node)
            grouped_nodes[node_type] = current_nodes

        self.start_block("primitives")

        for key, value in sorted(grouped_nodes.items()):
            # check if key is a base node, except Model
            if key not in SUPPORTED_TYPES:
                continue
            # render base nodes
            for p in value:
                fill = None
                if isinstance(p, Polygon):
                    self.start_block("gr_poly")
                    self._add_polygon_point_list(p.points)
                    fill = p.fill
                elif isinstance(p, Line):
                    self.start_block("gr_line")
                    self._add_line_points(p)
                elif isinstance(p, Rectangle):
                    if not p.angle:
                        # Rectangle without angle
                        self.start_block("gr_rect")
                        self._add_rect_points(p)
                        fill = p.fill
                    else:
                        # Rectangle with angle, treated as a polygon
                        self.start_block("gr_poly")
                        self._add_polygon_point_list(p.points)
                        fill = p.fill
                elif isinstance(p, Circle):
                    self.start_block("gr_circle")
                    self._add_circle_points(p)
                    fill = p.fill
                elif isinstance(p, Arc):
                    self.start_block("gr_arc")
                    self._add_arc_points_back_compatible(p)
                else:
                    raise TypeError("Unsuported type of primitive for custom pad.")
                width = _DEFAULT_WIDTH_POLYGON_PAD if p.width is None else p.width
                self.add_float("width", width)
                if fill:
                    self.add_symbol("fill", "yes")
                self.end_block()
        self.end_block()

    def _add_pad_chamfer_corner(self, pad: Pad) -> None:
        """Serialize the pad's corner chamfers.

        Args:
            pad: The pad.
        """
        lst: list[str] = []
        chamfer_corners = pad.chamfer_corners
        if chamfer_corners is not None:
            if chamfer_corners.top_left:
                lst += ["top_left"]
            if chamfer_corners.top_right:
                lst += ["top_right"]
            if chamfer_corners.bottom_left:
                lst += ["bottom_left"]
            if chamfer_corners.bottom_right:
                lst += ["bottom_right"]
            if len(lst) > 0:
                self.add_symbols("chamfer", lst)

    def _add_pad_string(
        self, number: str | int, at: Vector2D, rotation: float, pad: Pad
    ) -> None:
        """Serialize the pad and add the string to the pad instance for future reference.

        Args:
            number: The pad number.
            shape: The pad shape.
            at: The pad center position.
            pad: The pad.
        """
        # Round rects decay to rectangles if the radius ratio is 0
        if pad.shape == Pad.SHAPE_ROUNDRECT and pad.radius_ratio == 0:
            shape = Pad.SHAPE_RECT
        else:
            shape = pad.shape
        self.start_block(f'pad "{str(number)}" {pad.type} {shape}')
        rotation %= 360
        if rotation:
            self.add_3_floats("at", at.x, at.y, rotation)
        else:
            self.add_2_floats("at", at.x, at.y)
        if not hasattr(pad, "partial_serialization_string"):
            setattr(
                pad,
                "partial_serialization_string",
                self._get_pad_string_second_part(pad),
            )
        self.content.append(getattr(pad, "partial_serialization_string"))
        self.end_block()

    def _get_pad_string_second_part(self, pad: Pad) -> str:
        """Return a cachable string containing the serialized pad parameters that for a
        pad array typically don't change. This string is stored inside the pad instance
        for future reference.

        Args:
            pad: The pad.
        """
        ser = Serializer(self.indent)
        shape = pad.shape
        # Round rects decay to rectangles if the radius ratio is 0
        if shape == Pad.SHAPE_ROUNDRECT:
            if pad.radius_ratio == 0:
                shape = Pad.SHAPE_RECT
        ser.add_2_floats("size", pad.size.x, pad.size.y)

        if pad.type in [Pad.TYPE_THT, Pad.TYPE_NPTH] and (pad.drill is not None):

            if abs(pad.drill.x - pad.drill.y) < TOL_MM:
                ser.add_float("drill", pad.drill.x)
            else:
                ser.add_2_floats("drill oval", pad.drill.x, pad.drill.y)

            # append offset only if necessary
            if abs(pad.offset.x) > TOL_MM or abs(pad.offset.y) > TOL_MM:
                ser.add_2_floats("offset", pad.offset.x, pad.offset.y)

        # As of format 20231231, 'property' contains only the fab value.
        if pad.fab_property is not None:
            ser._add_fab_property(pad.fab_property)

        ser.add_strings("layers", SerializerPriority.sort_layers(pad.layers))

        if pad.type == Pad.TYPE_THT:
            unconn_mode = pad.unconnected_layer_mode
            remove_unconn = unconn_mode != Pad.UnconnectedLayerMode.KEEP_ALL
            ser.add_bool("remove_unused_layers", remove_unconn)

            if remove_unconn:
                b = unconn_mode == Pad.UnconnectedLayerMode.REMOVE_EXCEPT_START_AND_END
                ser.add_bool("keep_end_layers", b)

        if shape == Pad.SHAPE_ROUNDRECT:
            ser.add_float("roundrect_rratio", pad.radius_ratio)

            if (
                pad.chamfer_ratio is not None
                and pad.chamfer_corners is not None
                and pad.chamfer_corners.is_any_selected()
            ):
                ser.add_float("chamfer_ratio", pad.chamfer_ratio)
                ser._add_pad_chamfer_corner(pad)

        elif shape == Pad.SHAPE_CUSTOM:
            # gr_line, gr_arc, gr_circle or gr_poly
            ser.start_block("options")
            ser.add_symbol("clearance", pad.shape_in_zone)
            ser.add_symbol("anchor", pad.anchor_shape)
            ser.end_block()

            ser._add_pad_custom_primitives(pad)

        if pad.tuning_properties is not None:
            if pad.tuning_properties.die_length > TOL_MM:
                ser.add_float("die_length", pad.tuning_properties.die_length)

        if pad.solder_mask_margin:
            ser.add_float("solder_mask_margin", pad.solder_mask_margin)
        if pad.solder_paste_margin_ratio:
            ser.add_float("solder_paste_margin_ratio", pad.solder_paste_margin_ratio)
        if pad.solder_paste_margin:
            ser.add_float("solder_paste_margin", pad.solder_paste_margin)

        ser.add_pad_zone_connection(pad.zone_connection)

        if pad.clearance is not None and abs(pad.clearance) > TOL_MM:
            ser.add_float("clearance", pad.clearance)

        if pad.thermal_bridge_width is not None and pad.thermal_bridge_width > TOL_MM:
            ser.add_float("thermal_bridge_width", pad.thermal_bridge_width)

        ser._add_pad_thermal_bridge_angle(pad)

        if pad.thermal_gap is not None and abs(pad.thermal_gap) > TOL_MM:
            ser.add_float("thermal_gap", pad.thermal_gap)

        # KiCad writes this only if either side is set explicitly
        if (
            pad.padstack.front_mask_props.has_solder_mask is not None
            or pad.padstack.back_mask_props.has_solder_mask is not None
        ):
            ser.start_block("tenting")
            ser.add_optional_bool("front", pad.padstack.front_mask_props.has_solder_mask)
            ser.add_optional_bool("back", pad.padstack.back_mask_props.has_solder_mask)
            ser.end_block()

        return ser.to_string()

    def add_referenced_pad(self, pad: ReferencedPad) -> None:
        """Serialize a referenced pad.

        Args:
            pad: The referenced pad.
        """
        self._add_pad_string(
            number=pad.number, at=pad.at, rotation=pad.rotation, pad=pad.reference_pad
        )

    def add_pad(self, pad: Pad) -> None:
        """Serialize a pad.

        Args:
            pad: The pad.
        """
        self._add_pad_string(
            number=pad.number, at=pad.at, rotation=pad.rotation, pad=pad
        )

    def add_embedded_fonts(self, fonts: EmbeddedFonts) -> None:
        """Serialize the embedded fonts.

        Args:
            fonts: The embedded fonts.
        """
        if not fonts.enabled:
            return self.add_bool("embedded_fonts", False)
        else:
            raise NotImplementedError("'enabled' embedded fonts are not yet supported!")

    def add_group(self, group: Group) -> None:
        """Serialize a group.

        Args:
            group: The group.
        """
        self.start_block(f'group "{group.get_group_name()}"')
        if group.has_valid_timestamp():
            tstamp_uuid = str(group.get_timestamp())
        else:
            if group.has_valid_seed_for_timestamp():
                group.get_timestamp_class().recalculate_timestamp()
                if group.has_valid_timestamp():
                    tstamp_uuid = str(group.get_timestamp())
                else:
                    raise ValueError(
                        "TStamp for Group must be valid once serialization happpens"
                    )
            else:
                raise ValueError(
                    "TStamp Seed for Group must be valid once serialization happpens"
                )
        self.add_string("uuid", tstamp_uuid)
        grp_member_ids: list[str] = []
        for gid in group.get_sorted_group_member_timestamps():
            grp_member_ids.append(gid)
        grp_member_ids.sort()  # sort IDs, this is what KiCad does. ToDo: check order
        self.add_strings("members", grp_member_ids)

    def add_point(self, point: Point) -> None:
        """Serialize a point.

        Args:
            point: The point.
        """
        self.start_block("point")
        self.add_2_floats("at", point.at.x, point.at.y)
        self.add_float("size", point.size)
        self.add_string("layer", point.layer)
        self.end_block()

    def add_model(self, model: Model) -> None:
        """Serialize a model.

        Args:
            model: The model.
        """
        self.start_block(f'model "{model.filename}"')
        self.start_block("offset")
        self.add_3_floats("xyz", model.at.x, model.at.y, model.at.z)
        self.end_block()
        self.start_block("scale")
        self.add_3_floats("xyz", model.scale.x, model.scale.y, model.scale.z)
        self.end_block()
        self.start_block("rotate")
        self.add_3_floats("xyz", model.rotation.x, model.rotation.y, model.rotation.z)
        self.end_block()
        self.end_block()

    def add_tstamp(self, tstamp: TStamp) -> None:
        """Serialize a time stamp.

        Args:
            model: The time stamp.
        """
        if tstamp.is_timestamp_valid():
            self.add_string("tstamp", str(tstamp.get_timestamp()))
