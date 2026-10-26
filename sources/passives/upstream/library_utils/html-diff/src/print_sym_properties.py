#!/usr/bin/env python3

import re
from xml.etree import ElementTree as ET

from html_util import (
    DiffMultiProperty,
    DiffProperty,
    PropertyType,
    make_count_table,
    make_property_diff_table,
    make_property_multidiff_table,
)
from kicad_sym import KicadSymbol, Property


def _symbol_properties(old: KicadSymbol, new: KicadSymbol) -> list[DiffProperty]:

    leaf_props = [
        ["Name", "name"],
        ["Extends", "extends"],
    ]

    # These are properties that are on the root symbol, not the leaf symbols
    root_props = [
        ["Pin name offset", "pin_names_offset"],
        ["Pin names hidden", "hide_pin_names"],
        ["Pin numbers hidden", "hide_pin_numbers"],
        ["Is power symbol", "is_power"],
        ["Is in BOM", "in_bom"],
        ["Is on board", "on_board"],
        ["Number of units", "unit_count"],
        ["Number of styles", "body_style_count"],
    ]

    properties = []

    for name, attr in leaf_props:
        old_val = getattr(old, attr) if old else None
        new_val = getattr(new, attr) if new else None
        properties.append(DiffProperty(name, old_val, new_val, PropertyType.NATIVE))

    old_root = old.get_root_symbol() if old else None
    new_root = new.get_root_symbol() if new else None

    for name, attr in root_props:
        old_val = getattr(old_root, attr) if old_root else None
        new_val = getattr(new_root, attr) if new_root else None
        properties.append(DiffProperty(name, old_val, new_val, PropertyType.NATIVE))

    # Gather the props in the old and new symbols
    old_props = set()
    new_props = set()

    if old:
        for prop in old.properties:
            old_props.add(prop.name)

    if new:
        for prop in new.properties:
            new_props.add(prop.name)

    for prop_name in old_props.union(new_props):

        old_prop_val: Property = None
        new_prop_val: Property = None

        if prop_name in old_props:
            old_prop_val = old.get_property(prop_name)
        if prop_name in new_props:
            new_prop_val = new.get_property(prop_name)

        prop_type = (
            PropertyType.DATASHEET if prop_name == "Datasheet" else PropertyType.FIELD
        )

        properties.append(
            DiffProperty(
                prop_name,
                old_prop_val.value if old_prop_val else None,
                new_prop_val.value if new_prop_val else None,
                prop_type,
            )
        )

    return properties


def _symbol_counts(
    old: KicadSymbol | None, new: KicadSymbol | None
) -> list[DiffProperty]:

    attrs = ["pins", "rectangles", "circles", "arcs", "polylines", "texts"]

    counts = []

    for attr in attrs:
        new_count = len(getattr(new, attr)) if new else 0
        old_count = len(getattr(old, attr)) if old else 0

        diff = DiffProperty(attr, old_count, new_count, PropertyType.NATIVE)

        counts.append(diff)

    return counts


def _pin_data(
    old: KicadSymbol | None, new: KicadSymbol | None
) -> list[DiffMultiProperty]:

    def _to_sorting_key(n: str) -> tuple:

        # We want to sort pads with multiple name components such that A2 comes after A1 and before A10,
        # and all the Ax come before all Bx.
        # Example sort order: "", "0", "1", "2", "10", "A", "A1", "A2", "A10", "A100", "B", "B1"...
        # To achieve this, we split by name components such that digit sequences stay as individual tokens.
        # We will later compare lists of tuples, with the list length being the component count.

        # Split the strings into substrings containing digits and those containing everything else.
        # For example: 'a10.2' => ['a', '10', '.', '2']
        substrings = re.findall(r"\d+|[^\d]+", n)
        # To avoid comparing ints to strings, we create tuples with each item and its category number.
        # Ints sort before strings, so they are category 1, and strings get category 2.
        # For example: ['a', '10', '.', '2'] => [(2, 'a'), (1, 10), (2, '.'), (1, 2)]
        return tuple(
            [
                (1, int(substr)) if substr.isdigit() else (2, substr)
                for substr in substrings
            ]
        )

    def _extract_number(pin):
        if pin and pin.number:
            return (1, _to_sorting_key(pin.number), pin.number)
        else:
            return (2, "")

    def _mils(mm):
        return int(mm / (25.4 / 1000))

    def _format_pin(key, pinset):
        if key not in pinset.keys():
            return ""
        pin = pinset[key]
        altfuncs = ""
        for func in pin.altfuncs:
            altfuncs += f"\n'{func.name}' ({func.etype})"

        return [
            f"'{pin.name}' ({pin.etype}){altfuncs}",
            f"x:{str(_mils(pin.posx))},y:{str(_mils(pin.posy))}",
        ]

    num_diffs = []

    new_pins = {_extract_number(pin): pin for pin in new.pins} if new else {}
    old_pins = {_extract_number(pin): pin for pin in old.pins} if old else {}

    pinlist = list(set(list(new_pins.keys()) + list(old_pins.keys())))
    pinlist.sort()

    for key in pinlist:
        num_diffs.append(
            DiffMultiProperty(
                key[-1],
                _format_pin(key, old_pins),
                _format_pin(key, new_pins),
                PropertyType.NATIVE,
            )
        )

    name_diffs = []
    new_pin_names = {}
    if new:
        for pin in getattr(new, "pins"):
            if pin.name not in new_pin_names.keys():
                new_pin_names[pin.name] = [(_extract_number(pin), pin)]
            else:
                new_pin_names[pin.name].append((_extract_number(pin), pin))

    old_pin_names = {}
    if old:
        for pin in getattr(old, "pins"):
            if pin.name not in old_pin_names.keys():
                old_pin_names[pin.name] = [(_extract_number(pin), pin)]
            else:
                old_pin_names[pin.name].append((_extract_number(pin), pin))

    namelist = list(set(list(new_pin_names.keys()) + list(old_pin_names.keys())))
    namelist.sort()

    def _format_namelist(key, pinset):
        if key not in pinset.keys():
            return ""
        pinlist = pinset[key]

        # Sort only by the sorting key, lists of Pins cannot be sorted
        # and would crash if two keys are equal (e.g. same pins, different body styles)
        pinlist.sort(key=lambda x: x[0])

        pin_description = "\n".join(
            [f"'{pin[-1].number}' ({pin[-1].etype})" for pin in pinlist]
        )
        pin_pos = "\n".join(
            [
                f"x:{str(_mils(pin[-1].posx))},y:{str(_mils(pin[-1].posy))}"
                for pin in pinlist
            ]
        )
        return [pin_description, pin_pos]

    for key in namelist:
        name_diffs.append(
            DiffMultiProperty(
                key,
                _format_namelist(key, old_pin_names),
                _format_namelist(key, new_pin_names),
                PropertyType.NATIVE,
            )
        )

    return num_diffs, name_diffs


def format_properties(old: KicadSymbol | None, new: KicadSymbol | None) -> str:

    properties = _symbol_properties(old, new)

    container = ET.Element("div")

    prop_table = make_property_diff_table(properties)
    container.append(prop_table)

    # From here, we compare resolved root symbols, otherwise inherited
    # symbols will show 0 and indicate no differences, even when a changed
    # root symbol does have differences.
    new_root = new.get_root_symbol() if new else None
    old_root = old.get_root_symbol() if old else None

    count_header = ET.Element("h4")
    count_header.text = "Primitive counts:"
    container.append(count_header)

    count_table = make_count_table(_symbol_counts(old_root, new_root))
    container.append(count_table)

    pins_header = ET.Element("h4")
    pins_header.text = "Pins:"
    container.append(pins_header)

    multidiff_hdrs = ["Value", "Pos"]
    pin_data = _pin_data(old_root, new_root)
    pins_table = make_property_multidiff_table(pin_data[0], multidiff_hdrs)
    container.append(pins_table)

    pins_header = ET.Element("h4")
    pins_header.text = "Pin names:"
    container.append(pins_header)

    pin_names_table = make_property_multidiff_table(pin_data[1], multidiff_hdrs)
    container.append(pin_names_table)

    # Convert the XML container to a string
    out = ET.tostring(container, encoding="unicode", method="html")
    return out
