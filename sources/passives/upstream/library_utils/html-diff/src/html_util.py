"""
HTML utility functions for html-diff
"""

import enum
import re
from itertools import zip_longest
from xml.etree import ElementTree as ET


class PropertyType(enum.Enum):
    """
    This drives how we might want to display a property in the table.
    """

    # Text field dat
    FIELD = enum.auto()
    # DS URL
    DATASHEET = enum.auto()
    # Some "internal" data not directly entered as strings
    NATIVE = enum.auto()

    """
    Which HTML tag type should be used for the first cell in the table (Name/Type)?
    """

    def get_html_header_tag(self) -> str:
        if self == PropertyType.FIELD:
            return "pre"

        return "strong"

    """
    Which HTML tag type should be used for cells containing the old/new values?
    """

    def get_html_value_tag(self) -> str | None:
        if self == PropertyType.DATASHEET:
            return "a"
        elif self == PropertyType.FIELD:
            return "pre"

        return None


class DiffProperty:
    """
    Class that represents some property of a symbol that night change.
    """

    name: str
    _old: str | None
    _new: str | None
    prop_type: PropertyType

    def __init__(
        self, name: str, old: str | None, new: str | None, prop_type: PropertyType
    ):
        """
        :param name: The name of the property
        :param old: The old value of the property, or none if the old property is not present
        :param new: The new value of the property, or none if the new property is not present
        :param prop_type: The type of the property
        """

        self._old = old
        self._new = new

        self.name = name
        self.prop_type = prop_type

    @property
    def old(self) -> str:
        return self._old if self._old is not None else ""

    @property
    def new(self) -> str:
        return self._new if self._new is not None else ""


class DiffMultiProperty:
    """
    Class that represents multiple properties of a symbol that might change together or separately.
    """

    name: str
    old_new: list[tuple[str, str]] | None
    prop_type: PropertyType

    def __init__(
        self,
        name: str,
        old: list[str] | None,
        new: list[str] | None,
        prop_type: PropertyType,
    ):
        """
        :param name: The name of the property
        :param old: The old value of the property, or none if the old property is not present
        :param new: The new value of the property, or none if the new property is not present
        :param prop_type: The type of the property
        """

        self.old_new = list(zip_longest(old, new))

        self.name = name
        self.prop_type = prop_type


def heading(tag: str, text: str) -> ET.Element:
    """
    Create a heading element with the given tag and text.
    """

    elem = ET.Element(tag)
    elem.text = text

    return elem


def header_row(entries: list[str]) -> ET.Element:

    row = ET.Element("tr")
    for entry in entries:
        cell = ET.Element("th")
        cell.text = entry
        row.append(cell)

    return row


def diff_cell(val: str, cls: str | None, inner_tag: str | None = None) -> ET.Element:

    val = str(val) if val is not None else ""

    cell = ET.Element("td")
    if cls:
        cell.set("class", cls)

    if inner_tag is None:

        # look for URLS anywhere in the text
        url_pattern = re.compile(r"(https?://[^\s]+)")

        # Split text around URLs
        parts = url_pattern.split(val)
        for part in parts:
            if url_pattern.fullmatch(part):
                # Create a link element for URLs
                link = ET.SubElement(cell, "a", attrib={"href": part})
                link.text = part
            else:
                # Add regular text (create tail text if needed)
                if len(cell) > 0:
                    cell[-1].tail = (cell[-1].tail or "") + part
                else:
                    cell.text = (cell.text or "") + part
    else:
        if inner_tag == "a":
            inner = ET.Element("a")
            inner.text = val
            inner.set("target", "_blank")
            inner.set("href", val)
        else:
            inner = ET.Element(inner_tag)
            inner.text = val
        cell.append(inner)

    return cell


def make_property_diff_table(properties: list[DiffProperty]) -> ET.Element:

    table = ET.Element("table")
    table.attrib["id"] = "properties-table"
    table.append(header_row(["Name", "Old Value", "New Value"]))

    for prop in properties:

        row = ET.Element("tr")

        cls = None
        if prop.old == prop.new:
            cls = "prop-same"

        if prop.prop_type == PropertyType.DATASHEET:
            row.attrib["class"] = "datasheet"

        row.append(diff_cell(prop.name, None, prop.prop_type.get_html_header_tag()))
        row.append(diff_cell(prop.old, cls, prop.prop_type.get_html_value_tag()))
        row.append(diff_cell(prop.new, cls, prop.prop_type.get_html_value_tag()))

        table.append(row)

    return table


def make_property_multidiff_table(
    properties: list[DiffMultiProperty], headers: list[str]
) -> ET.Element:

    table = ET.Element("table")
    table.attrib["id"] = "properties-table"
    table.append(
        header_row(
            ["Name"] + [f"Old {h}" for h in headers] + [f"New {h}" for h in headers]
        )
    )

    for prop in properties:

        row = ET.Element("tr")
        new_els = []

        if prop.prop_type == PropertyType.DATASHEET:
            row.attrib["class"] = "datasheet"

        row.append(diff_cell(prop.name, None, prop.prop_type.get_html_header_tag()))

        for old, new in prop.old_new:
            cls = "prop-same" if old == new else None

            row.append(diff_cell(old, cls, prop.prop_type.get_html_value_tag()))
            new_els.append(diff_cell(new, cls, prop.prop_type.get_html_value_tag()))

        row.extend(new_els)
        table.append(row)

    return table


def make_count_table(counts: list[DiffProperty]) -> ET.Element:

    table = ET.Element("table")
    table.append(header_row(["Type", "Old Count", "New Count"]))

    for count in counts:

        cls = "prop-same" if count.old == count.new else None

        row = ET.Element("tr")
        row.append(diff_cell(count.name, None, "strong"))
        row.append(diff_cell(str(count.old), cls))
        row.append(diff_cell(str(count.new), cls))

        table.append(row)

    return table
