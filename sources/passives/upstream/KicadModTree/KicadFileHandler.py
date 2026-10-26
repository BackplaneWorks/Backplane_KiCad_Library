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
# (C) 2016-2018 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
# (C) The KiCad Librarian Team

"""Class definitions for the KiCad file handler."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from KicadModTree.FileHandler import FileHandler
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
from KicadModTree.nodes.base.Zone import Zone
from KicadModTree.nodes.Footprint import Footprint, FootprintType
from KicadModTree.nodes.Node import Node
from KicadModTree.serializer import Serializer, SerializerPriority

# This is the version of the .kicad_mod format that this serialiser produces
# It is used to set the version field in the .kicad_mod file
#
# The version number is a date in the format YYYYMMDD and corresponds to the
# version in the pcb_io_kicad_sexpr.h file for a stable release of KiCad.
_FORMAT_VERSION: int = 20260206

# The name of the generator (this is put in the .kicad_mod file)
#
# In theory, this could also encode which sub-generator was used, but for now
# this is just a fixed string, same as for KiCad v7 generators.
_GENERATOR_NAME: str = "kicad-footprint-generator"


class KicadFileHandler(FileHandler):
    """Implementation of the `FileHandler` for `.kicad_mod` files."""

    _NODE_SORT_KEY_MAP: dict[type[Node], Callable[[Any], list[Any]]] = {
        Text: SerializerPriority.get_sort_key_text,
        Line: SerializerPriority.get_sort_key_line,
        Arc: SerializerPriority.get_sort_key_arc,
        Circle: SerializerPriority.get_sort_key_circle,
        Rectangle: SerializerPriority.get_sort_key_rectangle,
        Polygon: SerializerPriority.get_sort_key_polygon,
        CompoundPolygon: SerializerPriority.get_sort_key_compound_polygon,
        Zone: SerializerPriority.get_sort_key_zone,
        Pad: SerializerPriority.get_sort_key_pad,
        ReferencedPad: SerializerPriority.get_sort_key_referenced_pad,
        EmbeddedFonts: SerializerPriority.get_sort_key_embedded_fonts,
        Model: SerializerPriority.get_sort_key_model,
        Group: SerializerPriority.get_sort_key_group,
        Point: SerializerPriority.get_sort_key_point,
    }

    _NODE_SERIALIZER_MAP: dict[type[Node], Callable[[Serializer, Any], None]] = {
        Text: Serializer.add_text,
        Line: Serializer.add_line,
        Arc: Serializer.add_arc,
        Circle: Serializer.add_circle,
        Rectangle: Serializer.add_rectangle,
        Polygon: Serializer.add_polygon,
        CompoundPolygon: Serializer.add_compound_polygon,
        Zone: Serializer.add_zone,
        Pad: Serializer.add_pad,
        ReferencedPad: Serializer.add_referenced_pad,
        EmbeddedFonts: Serializer.add_embedded_fonts,
        Model: Serializer.add_model,
        Group: Serializer.add_group,
        Point: Serializer.add_point,
    }

    def __init__(self, kicad_mod: Footprint) -> None:
        """Create an instance of the KiCad file handler.

        Args:
            kicad_mod: The footprint node (contianing all other nodes as child nodes).

        Example:
            >>> from KicadModTree import *
            >>> kicad_mod = Footprint("example_footprint")
            >>> file_handler = KicadFileHandler(kicad_mod)
            >>> file_handler.writeFile('example_footprint.kicad_mod')
        """

        # Instance attributes:
        self.kicad_mod: Footprint
        """The footprint node."""
        self.properties: list[Property]
        """The property nodes."""
        self.nodes: list[Node]
        """The non-property nodes."""
        self.serializer: Serializer
        """The serializer."""

        super().__init__()
        self.serializer = Serializer()
        self.kicad_mod = kicad_mod
        self._create_flattened_tree()

    def _create_flattened_tree(self) -> None:
        """Make a flattened tree.

        Create a (flattened) list of all child nodes that need to be serialized. If
        transformations need to be applied, it creates a copy of the nodes and applies
        then the transforms on them.
        """
        property_nodes: list[Property] = []
        other_nodes: list[Node] = []
        for node in self.kicad_mod.flatten():
            if isinstance(node, Property):
                property_nodes.append(node)
            else:
                other_nodes.append(node)

        # Reorder the nodes to the KiCad native order:
        other_nodes.sort(
            key=lambda item: KicadFileHandler._get_sort_key_func(type(item))(item)
        )
        self.property_nodes = property_nodes
        self.nodes = other_nodes

    def serialize(self) -> str:
        """Transform the footprint and its child nodes into a string (to save as a
        `*.kicad_mod` file).
        """
        kicad_mod = self.kicad_mod
        self.serializer.start_block(f'footprint "{kicad_mod.name}"')
        self.serializer.add_int("version", _FORMAT_VERSION)
        self.serializer.add_string("generator", _GENERATOR_NAME)
        self.serializer.add_string("layer", "F.Cu")
        if kicad_mod.description:
            self.serializer.add_string("descr", kicad_mod.description)
        if tags := kicad_mod.tags:
            tag_string = ""
            for tag in tags[:-1]:
                tag_string += f"{tag} "
            tag_string += f"{tags[-1]}"
            self.serializer.add_string("tags", tag_string)
        if kicad_mod.maskMargin:
            self.serializer.add_float("solder_mask_margin", kicad_mod.maskMargin)
        if kicad_mod.pasteMargin:
            self.serializer.add_float("solder_paste_margin", kicad_mod.pasteMargin)
        if kicad_mod.pasteMarginRatio:
            self.serializer.add_float("solder_paste_ratio", kicad_mod.pasteMarginRatio)

        # Serialize the initial property nodes:
        for property in self.property_nodes:
            self.serializer.add_property(property)
        if kicad_mod.clearance is not None:
            self.serializer.add_float("clearance", kicad_mod.clearance)
        self.serializer.add_pad_zone_connection(kicad_mod.zone_connection)
        # Kicad 9 puts the attributes at the end of the properties:
        attributes = {
            FootprintType.UNSPECIFIED: [],
            FootprintType.SMD: ["smd"],
            FootprintType.THT: ["through_hole"],
        }[kicad_mod.footprintType]
        if kicad_mod.not_in_schematic:
            attributes.append("board_only")
        if kicad_mod.excludeFromPositionFiles:
            attributes.append("exclude_from_pos_files")
        if kicad_mod.excludeFromBOM:
            attributes.append("exclude_from_bom")
        if kicad_mod.allow_soldermask_bridges:
            attributes.append("allow_soldermask_bridges")
        if kicad_mod.allow_missing_courtyard:
            attributes.append("allow_missing_courtyard")
        if kicad_mod.dnp:
            attributes.append("dnp")

        if attributes:
            self.serializer.add_symbols("attr", attributes)

        if kicad_mod.net_tie_pad_groups:
            # Unlike jumper_pad_groups, net_tie_pad_groups are comma-separated strings
            # at least as of V10.
            group_strings = [",".join(group) for group in kicad_mod.net_tie_pad_groups]
            self.serializer.add_strings("net_tie_pad_groups", group_strings)

        # More modern "typed" attributes come after the (attr) list
        self.serializer.add_bool(
            "duplicate_pad_numbers_are_jumpers",
            kicad_mod.duplicate_pad_numbers_are_jumpers,
        )

        if kicad_mod.jumper_pad_groups:
            self.serializer.start_block("jumper_pad_groups")

            for group in kicad_mod.jumper_pad_groups:
                self.serializer.add_strings(None, group)

            self.serializer.end_block()

        # Serialize the ordered nodes:
        for node in self.nodes:
            KicadFileHandler._get_serializer_func(type(node))(self.serializer, node)
        self.serializer.end_block()
        return self.serializer.to_string()

    @staticmethod
    def _get_sort_key_func(node_type: type[Node]) -> Callable[[Any], list[Any]]:
        """
        Retrieves the sort key function for the given node type.

        If the specific type is missing, it recursively searches the type's direct
        parent classes (its MRO) until a match is found in the map.
        """
        try:
            return KicadFileHandler._NODE_SORT_KEY_MAP[node_type]
        except KeyError:
            return KicadFileHandler._get_sort_key_func(node_type.__bases__[0])

    @staticmethod
    def _get_serializer_func(
        node_type: type[Node],
    ) -> Callable[[Serializer, Any], None]:
        """
        Retrieves the serializer function for the given node type.

        If the specific type is missing, it recursively searches the type's direct
        parent classes (its MRO) until a match is found in the map.
        """
        try:
            return KicadFileHandler._NODE_SERIALIZER_MAP[node_type]
        except KeyError:
            return KicadFileHandler._get_serializer_func(node_type.__bases__[0])
