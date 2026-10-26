#!/usr/bin/env python3

from xml.etree import ElementTree as ET

import html_util
from html_util import DiffProperty, PropertyType
from kicad_mod import KicadMod


def lookup(l, k, default=None):  # NOQA: 741
    for elem in l:
        if isinstance(elem, list) and len(elem) > 1:
            if elem[0] == k:
                return elem[1:]
    return default


def _fp_properties(old: KicadMod, new: KicadMod) -> list[DiffProperty]:

    properties = []

    simple_props = [
        ["Name", "name"],
        ["Version", "version"],
        ["Generator", "generator"],
        ["Description", "description"],
        ["Tags", "tags"],
        ["Layer", "layer"],
        ["Footprint type", "footprint_type"],
        ["Exclude from BOM", "exclude_from_bom"],
        ["Exclude from pos files", "exclude_from_pos_files"],
    ]

    for name, attr in simple_props:
        old_val = getattr(old, attr) if old else None
        new_val = getattr(new, attr) if new else None
        properties.append(DiffProperty(name, old_val, new_val, PropertyType.NATIVE))

    # Annoyingly this is a dict when read out of a file, it should really be a type
    def format_textitem(prop_dict: dict, text_key: str) -> str:

        strs = [
            f"Text: {prop_dict[text_key]}",
            f"Layer: {prop_dict['layer']}",
            f"Pos: {prop_dict['pos']}",
            f"Font: {prop_dict['font']}",
            f"Hidden: {prop_dict['hide']}",
        ]

        return "\n".join([str(s) for s in strs])

    mod_properties = [
        ["Reference", "reference"],
        ["Value", "value"],
    ]

    for name, prop_name in mod_properties:
        old_val = None
        new_val = None
        if old:
            old_val = format_textitem(old.getProperty(prop_name), prop_name)
        if new:
            new_val = format_textitem(new.getProperty(prop_name), prop_name)

        properties.append(DiffProperty(name, old_val, new_val, PropertyType.FIELD))

    # Pull out the user texts and compare them
    old_usertexts = old.userText if old else []
    new_usertexts = new.userText if new else []

    for i in range(max(len(old_usertexts), len(new_usertexts))):
        old_val = None
        new_val = None

        if i < len(old_usertexts):
            old_val = format_textitem(old_usertexts[i], "user")

        if i < len(new_usertexts):
            new_val = format_textitem(new_usertexts[i], "user")

        properties.append(
            DiffProperty(f"User text {i}", old_val, new_val, PropertyType.FIELD)
        )

    # Annoyingly this is a dict when read out of a file, it should really be a type
    def format_model(model: dict) -> str:
        strs = [
            model["file"],
            str(model["pos"]),
            str(model["scale"]),
        ]
        return "\n".join(strs)

    # Break the models down to text lines
    old_model_str = ""
    new_model_str = ""

    if old:
        old_models = old.models
        old_model_str += "\n\n".join([format_model(m) for m in old_models])

    if new:
        new_models = new.models
        new_model_str += "\n\n".join([format_model(m) for m in new_models])

    properties.append(
        DiffProperty("Models", old_model_str, new_model_str, PropertyType.FIELD)
    )
    return properties


def _fp_counts(old: KicadMod | None, new: KicadMod | None) -> list[DiffProperty]:

    tag_types = ["fp_line", "fp_rect", "fp_circle", "fp_poly", "pad", "zone", "group"]

    old_sexp = old.sexpr_data if old else []
    new_sexp = new.sexpr_data if new else []

    counts = {tag: [0, 0] for tag in tag_types}

    for tag, *values in old_sexp:
        if tag in tag_types:
            counts[tag][0] += 1

    for tag, *values in new_sexp:
        if tag in tag_types:
            counts[tag][1] += 1

    diffs = []
    for tag in tag_types:
        diffs.append(
            DiffProperty(
                tag, str(counts[tag][0]), str(counts[tag][1]), PropertyType.NATIVE
            )
        )

    # Sort by count descending, but tag alphabetically ascending
    diffs.sort(key=lambda x: (x.name, -int(x.new)))

    return diffs


def format_properties(old_mod: KicadMod | None, new_mod: KicadMod | None) -> str:

    props = _fp_properties(old_mod, new_mod)

    container = ET.Element("div")

    container.append(html_util.make_property_diff_table(props))
    container.append(html_util.heading("h4", "Item counts:"))

    counts = _fp_counts(old_mod, new_mod)
    container.append(html_util.make_count_table(counts))

    # Convert the XML container to a string
    out = ET.tostring(container, encoding="unicode", method="html")
    return out
