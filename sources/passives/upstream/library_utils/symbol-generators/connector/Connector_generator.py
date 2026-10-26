#!/usr/bin/python3

import argparse
import fnmatch
import os
import re
import sys
from collections import namedtuple
from math import sqrt

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

import kicad_sym
from DrawingElements import (
    Drawing,
    DrawingArc,
    DrawingArray,
    DrawingCircle,
    DrawingPin,
    DrawingPolyline,
    DrawingRectangle,
    DrawingText,
    ElementFill,
)
from Point import Point

# ##############################  Parameters ##################################
pin_per_row_range = range(1, 61)
# For some dual row connectors all numbering schemes generate the same symbol for the 1 pin per row
# variant.
pin_per_row_range_dual = range(2, 41)
pin_per_row_range_screw = range(1, 21)
pin_range_dual_row_odd_count = range(2, 38)

reference_designator = "J"

pin_grid = 100
pin_spacing_y = 100
pin_length = 150

mp_artwork_to_body = 30
extra_pin_grid = 50

body_width_per_row = 100
body_fill = ElementFill.FILL_BACKGROUND

ref_fontsize = 50
value_fontsize = 50
pin_number_fontsize = 50

body_outline_line_width = 10
inner_graphics_line_width = 6

inner_graphic_width = 50
inner_graphic_pin_neutral_height = 10
inner_graphic_socket_radius = 20
inner_graphic_screw_radius = 25
inner_graphic_screw_slit_width = 10


filter_terminal_block = ["TerminalBlock*:*"]
filter_single_row = ["Connector*:*_1x??{pn_modifier:s}*"]
filter_dual_row = ["Connector*:*_2x??{pn_modifier:s}*"]

filter_dual_row_odd_count = [
    "Connector*:*2Rows*Pins{pn_modifier:s}_*",
    "*FCC*2Rows*Pins{pn_modifier:s}_*",
]


CONNECTOR = namedtuple(
    "CONNECTOR",
    [
        "num_rows",
        "pin_per_row_range",
        "odd_count",
        "symbol_name_format",
        "top_pin_number",
        "pin_number_generator",
        "description",
        "keywords",
        "datasheet",
        "default_footprint",
        "footprint_filter",
        "graphic_type",
        "enclosing_rectangle",
        "mirror",
        # adds an additional gap after the specified pin row to generate
        # polarized connector symbols: None (default) or dict
        "pin_gap_positions",
    ],
)
CONNECTOR.__new__.__defaults__ = (None,) * len(CONNECTOR._fields)


def num_gen_row_letter_first(old_number):
    return old_number[:1] + str(int(old_number[1:]) + 1)


def num_gen_row_letter_first_by2(old_number):
    return old_number[:1] + str(int(old_number[1:]) + 2)


def num_gen_row_letter_last(old_number):
    return str(int(old_number[:-1]) + 1) + old_number[-1:]


conn_screw_terminal = {
    "single_row_screw": CONNECTOR(
        num_rows=1,
        pin_per_row_range=pin_per_row_range_screw,
        odd_count=False,
        symbol_name_format="Screw_Terminal_01x{num_pins_per_row:02d}{suffix:s}",
        top_pin_number=[1],
        pin_number_generator=[lambda old_number: old_number + 1],
        description="Generic screw terminal, single row, 01x{num_pins_per_row:02d}",
        keywords="screw terminal",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_terminal_block,
        graphic_type=3,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    )
}

conn_pin_socket = {
    "single_row_pin": CONNECTOR(
        num_rows=1,
        pin_per_row_range=pin_per_row_range,
        odd_count=False,
        symbol_name_format="Conn_01x{num_pins_per_row:02d}_Pin{suffix:s}",
        top_pin_number=[1],
        pin_number_generator=[lambda old_number: old_number + 1],
        description=(
            "Generic{extra_pin:s} connector, single row, 01x{num_pins_per_row:02d}"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_single_row,
        graphic_type=1,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=False,
        mirror=True,
    ),
    "single_row_socket": CONNECTOR(
        num_rows=1,
        pin_per_row_range=pin_per_row_range,
        odd_count=False,
        symbol_name_format="Conn_01x{num_pins_per_row:02d}_Socket{suffix:s}",
        top_pin_number=[1],
        pin_number_generator=[lambda old_number: old_number + 1],
        description=(
            "Generic{extra_pin:s} connector, single row, 01x{num_pins_per_row:02d}"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_single_row,
        graphic_type=2,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=False,
        mirror=False,
    ),
}

conn_generic = {
    "single_row": CONNECTOR(
        num_rows=1,
        pin_per_row_range=pin_per_row_range,
        odd_count=False,
        symbol_name_format="Conn_01x{num_pins_per_row:02d}{suffix:s}",
        top_pin_number=[1],
        pin_number_generator=[lambda old_number: old_number + 1],
        description=(
            "Generic{extra_pin:s} connector, single row, 01x{num_pins_per_row:02d}"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_single_row,
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_odd-even": CONNECTOR(
        num_rows=2,
        pin_per_row_range=pin_per_row_range_dual,
        odd_count=False,
        symbol_name_format="Conn_02x{num_pins_per_row:02d}_Odd_Even{suffix:s}",
        top_pin_number=[1, lambda num_pin_per_row: 2],
        pin_number_generator=[
            lambda old_number: old_number + 2,
            lambda old_number: old_number + 2,
        ],
        description=(
            "Generic{extra_pin:s} connector, double row, 02x{num_pins_per_row:02d},"
            " odd/even pin numbering scheme (row 1 odd numbers, row 2 even numbers)"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_dual_row,
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_counter-clockwise": CONNECTOR(
        num_rows=2,
        pin_per_row_range=pin_per_row_range_dual,
        odd_count=False,
        symbol_name_format="Conn_02x{num_pins_per_row:02d}_Counter_Clockwise{suffix:s}",
        top_pin_number=[1, lambda num_pin_per_row: 2 * num_pin_per_row],
        pin_number_generator=[
            lambda old_number: old_number + 1,
            lambda old_number: old_number - 1,
        ],
        description=(
            "Generic{extra_pin:s} connector, double row, 02x{num_pins_per_row:02d},"
            " counter clockwise pin numbering scheme (similar to DIP package numbering)"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_dual_row,
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_top-bottom": CONNECTOR(
        num_rows=2,
        pin_per_row_range=pin_per_row_range_dual,
        odd_count=False,
        symbol_name_format="Conn_02x{num_pins_per_row:02d}_Top_Bottom{suffix:s}",
        top_pin_number=[1, lambda num_pin_per_row: num_pin_per_row + 1],
        pin_number_generator=[
            lambda old_number: old_number + 1,
            lambda old_number: old_number + 1,
        ],
        description=(
            "Generic{extra_pin:s} connector, double row, 02x{num_pins_per_row:02d},"
            " top/bottom pin numbering scheme (row 1: 1...pins_per_row, row2:"
            " pins_per_row+1 ... num_pins)"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_dual_row,
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_02x01_numbered": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[1],
        odd_count=False,
        symbol_name_format="Conn_02x{num_pins_per_row:02d}{suffix:s}",
        top_pin_number=[1, lambda num_pin_per_row: num_pin_per_row + 1],
        pin_number_generator=[
            lambda old_number: old_number + 1,
            lambda old_number: old_number + 1,
        ],
        description=(
            "Generic{extra_pin:s} connector, double row, 02x01, this symbol is"
            " compatible with counter-clockwise, top-bottom and odd-even numbering"
            " schemes."
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_dual_row,
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_letter-first": CONNECTOR(
        num_rows=2,
        pin_per_row_range=pin_per_row_range,
        odd_count=False,
        symbol_name_format="Conn_02x{num_pins_per_row:02d}_Row_Letter_First{suffix:s}",
        top_pin_number=["a1", lambda num_pin_per_row: "b1"],
        pin_number_generator=[num_gen_row_letter_first, num_gen_row_letter_first],
        description=(
            "Generic{extra_pin:s} connector, double row, 02x{num_pins_per_row:02d}, row"
            " letter first pin numbering scheme (pin number consists of a letter for"
            " the row and a number for the pin index in this row. a1, ..., aN; b1,"
            " ..., bN)"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_dual_row,
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_letter-last": CONNECTOR(
        num_rows=2,
        pin_per_row_range=pin_per_row_range,
        odd_count=False,
        symbol_name_format="Conn_02x{num_pins_per_row:02d}_Row_Letter_Last{suffix:s}",
        top_pin_number=["1a", lambda num_pin_per_row: "1b"],
        pin_number_generator=[num_gen_row_letter_last, num_gen_row_letter_last],
        description=(
            "Generic{extra_pin:s} connector, double row, 02x{num_pins_per_row:02d}, row"
            " letter last pin numbering scheme (pin number consists of a number for the"
            " row and a letter for the pin index in this row. 1a, ..., Na; 1b, ...,"
            " Nb))"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_dual_row,
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_odd_pin_count": CONNECTOR(
        num_rows=2,
        pin_per_row_range=pin_range_dual_row_odd_count,
        odd_count=True,
        symbol_name_format="Conn_2Rows-{num_pins:02d}Pins{suffix:s}",
        top_pin_number=[1, lambda num_pin_per_row: 2],
        pin_number_generator=[
            lambda old_number: old_number + 2,
            lambda old_number: old_number + 2,
        ],
        description=(
            "Generic{extra_pin:s} connector, double row, {num_pins:02d} pins, odd/even"
            " pin numbering scheme (row 1 odd numbers, row 2 even numbers)"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=filter_dual_row_odd_count,
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
}

conn_iec_din = {
    "single_row_din41612_a": CONNECTOR(
        num_rows=1,
        pin_per_row_range=[32],
        odd_count=False,
        symbol_name_format="DIN41612_01x{num_pins_per_row:02d}{suffix:s}_A",
        top_pin_number=["a1"],
        pin_number_generator=[num_gen_row_letter_first],
        description="DIN41612 connector, single row (A), 01x{num_pins_per_row:02d}",
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*1x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_din41612_ab": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[10, 16, 32],
        odd_count=False,
        symbol_name_format="DIN41612_02x{num_pins_per_row:02d}_AB",
        top_pin_number=["a1", lambda num_pin_per_row: "b1"],
        pin_number_generator=[num_gen_row_letter_first, num_gen_row_letter_first],
        description="DIN41612 connector, double row (AB), 02x{num_pins_per_row:02d}",
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*2x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_din41612_ac": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[10, 16, 32],
        odd_count=False,
        symbol_name_format="DIN41612_02x{num_pins_per_row:02d}_AC",
        top_pin_number=["a1", lambda num_pin_per_row: "c1"],
        pin_number_generator=[num_gen_row_letter_first, num_gen_row_letter_first],
        description="DIN41612 connector, double row (AC), 02x{num_pins_per_row:02d}",
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*2x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_din41612_ae": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[10, 16, 32],
        odd_count=False,
        symbol_name_format="DIN41612_02x{num_pins_per_row:02d}_AE",
        top_pin_number=["a1", lambda num_pin_per_row: "e1"],
        pin_number_generator=[num_gen_row_letter_first, num_gen_row_letter_first],
        description="DIN41612 connector, double row (AE), 02x{num_pins_per_row:02d}",
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*2x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_din41612_zb": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[10, 16, 32],
        odd_count=False,
        symbol_name_format="DIN41612_02x{num_pins_per_row:02d}_ZB",
        top_pin_number=["z1", lambda num_pin_per_row: "b1"],
        pin_number_generator=[num_gen_row_letter_first, num_gen_row_letter_first],
        description="DIN41612 connector, double row (ZB), 02x{num_pins_per_row:02d}",
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*2x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_din41612_ab_even-pins": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[5, 8, 16],
        odd_count=False,
        symbol_name_format="DIN41612_02x{num_pins_per_row:02d}_AB_EvenPins",
        top_pin_number=["a2", lambda num_pin_per_row: "b2"],
        pin_number_generator=[
            num_gen_row_letter_first_by2,
            num_gen_row_letter_first_by2,
        ],
        description=(
            "DIN41612 connector, double row (AB) even pins only,"
            " 02x{num_pins_per_row:02d}"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*2x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_din41612_ac_even-pins": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[5, 8, 16],
        odd_count=False,
        symbol_name_format="DIN41612_02x{num_pins_per_row:02d}_AC_EvenPins",
        top_pin_number=["a2", lambda num_pin_per_row: "c2"],
        pin_number_generator=[
            num_gen_row_letter_first_by2,
            num_gen_row_letter_first_by2,
        ],
        description=(
            "DIN41612 connector, double row (AC) even pins only,"
            " 02x{num_pins_per_row:02d}"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*2x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_din41612_ae_even-pins": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[5, 8, 16],
        odd_count=False,
        symbol_name_format="DIN41612_02x{num_pins_per_row:02d}_AE_EvenPins",
        top_pin_number=["a2", lambda num_pin_per_row: "e2"],
        pin_number_generator=[
            num_gen_row_letter_first_by2,
            num_gen_row_letter_first_by2,
        ],
        description=(
            "DIN41612 connector, double row (AE) even pins only,"
            " 02x{num_pins_per_row:02d}"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*2x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
    "dual_row_din41612_zb_even-pins": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[5, 8, 16],
        odd_count=False,
        symbol_name_format="DIN41612_02x{num_pins_per_row:02d}_ZB_EvenPins",
        top_pin_number=["z2", lambda num_pin_per_row: "b2"],
        pin_number_generator=[
            num_gen_row_letter_first_by2,
            num_gen_row_letter_first_by2,
        ],
        description=(
            "DIN41612 connector, double row (ZB) even pins only,"
            " 02x{num_pins_per_row:02d}"
        ),
        keywords="connector",
        datasheet="~",  # generic symbol, no datasheet, ~ to make travis happy
        default_footprint="",  # generic symbol, no default footprint
        footprint_filter=["DIN41612*2x*"],
        graphic_type=0,  # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
    ),
}

conn_samtec = {
    "Samtec_HSEC8-DV": CONNECTOR(
        num_rows=2,
        pin_per_row_range=[10 * (n + 1) for n in range(10)] + [9, 13, 25, 37, 49],
        odd_count=False,
        symbol_name_format=(
            "HSEC8-1{num_pins_per_row:02d}-X-X-DV-X_2x{num_pins_per_row:02d}{suffix:s}"
        ),
        top_pin_number=[1, lambda num_pin_per_row: 2],
        pin_number_generator=[
            lambda old_number: old_number + 2,
            lambda old_number: old_number + 2,
        ],
        description="Samtec card edge connector HSEC8 series, 2x{num_pins_per_row:d} contacts",
        keywords="connector card-edge",
        datasheet="https://suddendocs.samtec.com/prints/hsec8-1xxx-xx-xx-dv-x-xx-x-xx-mkt.pdf",
        default_footprint="",  # no default footprint
        footprint_filter=[
            "Samtec*HSEC8*DV*P0.8mm*Socket*",
            "Samtec*HSEC8*DV*P0.8mm*Edge*",
        ],
        graphic_type=0,  # 0 = neutral, 1 = male, 2 = female, 3 = screw terminal
        enclosing_rectangle=True,
        mirror=False,
        pin_gap_positions={
            9: [3],
            13: [5],
            25: [5],
            37: [20],
            40: [21],
            49: [26],
            50: [26],
            60: [31],
            70: [31],
            80: [31],
            90: [31],
            100: [31],
        },
    ),
}


def pinname_update_function(old_name, new_number):
    return "Pin_{}".format(new_number)


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def draw_mp_end(pin_pos, pin_len):
    artwork = Drawing()

    center = pin_pos.translate(
        {"x": 0, "y": pin_len}, apply_on_copy=True, new_grid=None
    )

    xd = body_width_per_row / 2 - 10

    artwork.append(
        DrawingPolyline(
            points=[
                Point({"x": center.x - xd, "y": center.y}),
                Point({"x": center.x + xd, "y": center.y}),
            ],
            line_width=inner_graphics_line_width,
        )
    )

    center_text = center.translate(
        {"x": 0, "y": mp_artwork_to_body / 2}, apply_on_copy=True, new_grid=None
    )

    artwork.append(
        DrawingText(at=center_text, text="Mounting", size=mp_artwork_to_body - 15)
    )

    return artwork


SHIELD_PIN = {"number": "SH", "name": "Shield", "deco": None, "offset": 0}

MOUNT_PIN = {
    "number": "MP",
    "name": "MountPin",
    "deco": draw_mp_end,
    "offset": mp_artwork_to_body,
}

all_symbols = [
    {
        "lib_name": "Connector",
        "symbol_def": merge_dicts(conn_screw_terminal, conn_pin_socket),
        "extra_pin": None,
        "pn_modifier": "_",
        "suffix": "",
        "extra_pin_descr": "",
    },
    {
        "lib_name": "Connector_Generic",
        "symbol_def": conn_generic,
        "extra_pin": None,
        "pn_modifier": "_",
        "suffix": "",
        "extra_pin_descr": "",
    },
    {
        "lib_name": "Connector_Generic_Shielded",
        "symbol_def": conn_generic,
        "extra_pin": SHIELD_PIN,
        "pn_modifier": "-1SH",
        "suffix": "_Shielded",
        "extra_pin_descr": " shielded",
    },
    {
        "lib_name": "Connector_Generic_MountingPin",
        "symbol_def": conn_generic,
        "extra_pin": MOUNT_PIN,
        "pn_modifier": "-1MP",
        "suffix": "_MountingPin",
        "extra_pin_descr": " connectable mounting pin",
    },
    {
        "lib_name": "Connector_IEC_DIN",
        "symbol_def": conn_iec_din,
        "extra_pin": None,
        "pn_modifier": "_",
        "suffix": "",
        "extra_pin_descr": "",
    },
    {
        "lib_name": "Connector_Samtec_HSEC8",
        "symbol_def": conn_samtec,
        "extra_pin": None,
        "pn_modifier": "_",
        "suffix": "",
        "extra_pin_descr": "",
    },
]


def innerArtwork(type=0):
    artwork = Drawing()

    # 0 = neutral, 1 = pin, 2 = socket, 3 = screw terminal
    if type == 0:
        artwork.append(
            DrawingRectangle(
                start=Point({"x": 0, "y": inner_graphic_pin_neutral_height // 2}),
                end=Point(
                    {
                        "x": inner_graphic_width,
                        "y": -inner_graphic_pin_neutral_height // 2,
                    }
                ),
                fill=ElementFill.NO_FILL,
                line_width=inner_graphics_line_width,
            )
        )
    if type == 1:
        from_edge = inner_graphic_width // 3
        artwork.append(
            DrawingRectangle(
                start=Point(
                    {"x": from_edge, "y": inner_graphic_pin_neutral_height // 2}
                ),
                end=Point(
                    {
                        "x": inner_graphic_width,
                        "y": -inner_graphic_pin_neutral_height // 2,
                    }
                ),
                fill=ElementFill.FILL_FOREGROUND,
                line_width=inner_graphics_line_width,
            )
        )
        artwork.append(
            DrawingPolyline(
                points=[Point({"x": 0, "y": 0}), Point({"x": from_edge, "y": 0})],
                line_width=inner_graphics_line_width,
            )
        )
    if type == 2:
        artwork.append(
            DrawingArc(
                at=Point({"x": inner_graphic_width, "y": 0}),
                radius=inner_graphic_socket_radius,
                angle_start=901,
                angle_end=-901,
                line_width=inner_graphics_line_width,
            )
        )
        artwork.append(
            DrawingPolyline(
                points=[
                    Point({"x": 0, "y": 0}),
                    Point(
                        {"x": inner_graphic_width - inner_graphic_socket_radius, "y": 0}
                    ),
                ],
                line_width=inner_graphics_line_width,
            )
        )
    if type == 3:
        center = Point({"x": body_width_per_row // 2, "y": 0})
        artwork.append(
            DrawingCircle(
                at=center,
                radius=inner_graphic_screw_radius,
                line_width=inner_graphics_line_width,
            )
        )

        p_slit_1 = Point(
            {
                "x": inner_graphic_screw_slit_width // 2,
                "y": int(
                    sqrt(
                        inner_graphic_screw_radius**2
                        - (inner_graphic_screw_slit_width / 2) ** 2
                    )
                ),
            }
        ).translate({"x": center.x, "y": 0})
        line1 = DrawingPolyline(
            points=[p_slit_1, p_slit_1.mirrorVertical(apply_on_copy=True)],
            line_width=inner_graphics_line_width,
        )
        artwork.append(line1)
        artwork.append(
            line1.translate(
                distance={"x": -inner_graphic_screw_slit_width, "y": 0},
                apply_on_copy=True,
            )
        )
        artwork.rotate(angle=45, origin=center)
        # artwork.rotate(angle = 45)
    return artwork


def generateSingleSymbol(library, series_params, num_pins_per_row, lib_params):
    pincount = series_params.num_rows * num_pins_per_row + (
        1 if series_params.odd_count else 0
    )
    symbol_name = series_params.symbol_name_format.format(
        num_pins_per_row=num_pins_per_row,
        suffix=lib_params.get("suffix", ""),
        num_pins=pincount,
    )

    fp_filter = [
        fp_filter.format(pn_modifier=lib_params.get("pn_modifier", ""))
        for fp_filter in series_params.footprint_filter
    ]

    libname = os.path.basename(library.filename)
    libname = os.path.splitext(libname)[0]

    current_symbol = kicad_sym.KicadSymbol.new(
        symbol_name,
        libname,
        reference_designator,
        "",
        series_params.datasheet,
        series_params.keywords,
        series_params.description.format(
            num_pins_per_row=num_pins_per_row,
            num_pins=pincount,
            extra_pin=lib_params.get("extra_pin_descr", ""),
        )
        + ", script generated",
        fp_filter,
    )
    library.symbols.append(current_symbol)

    current_symbol.hide_pin_names = True
    current_symbol.pin_names_offset = kicad_sym.mil_to_mm(40)

    # pin gaps
    if isinstance(series_params.pin_gap_positions, dict):
        pin_gap_positions = series_params.pin_gap_positions.get(num_pins_per_row, [])
    elif series_params.pin_gap_positions:
        pin_gap_positions = series_params.pin_gap_positions
    else:
        pin_gap_positions = []
    num_pin_gaps = len(pin_gap_positions)

    # ######################## reference points ################################
    num_pins_left_side = num_pins_per_row + (1 if series_params.odd_count else 0)

    top_left_pin_position = Point(
        {
            "x": -pin_length - body_width_per_row,
            "y": pin_spacing_y * (num_pins_left_side + num_pin_gaps - 1) / 2.0,
        },
        grid=pin_grid,
    )

    if series_params.num_rows == 2:
        top_right_pin_position = top_left_pin_position.translate(
            {"x": 2 * pin_length + 2 * body_width_per_row, "y": 0}, apply_on_copy=True
        )

    body_top_left_corner = top_left_pin_position.translate(
        {"x": pin_length, "y": pin_spacing_y / 2}, apply_on_copy=True, new_grid=None
    )

    body_width = pin_spacing_y * series_params.num_rows
    body_bottom_right_corner = body_top_left_corner.translate(
        {"x": body_width, "y": -pin_spacing_y * (num_pins_left_side + num_pin_gaps)},
        apply_on_copy=True,
    )

    extra_pin = lib_params.get("extra_pin")

    if extra_pin:
        extra_pin_pos = body_bottom_right_corner.translate(
            {"x": -body_width / 2, "y": -pin_length},
            apply_on_copy=True,
            new_grid=extra_pin_grid,
        )
        extra_pin_length = (
            body_bottom_right_corner.y - extra_pin_pos.y - extra_pin["offset"]
        )

    if extra_pin == SHIELD_PIN:
        shield_top_left_corner = body_top_left_corner
        shield_bottom_right_corner = body_bottom_right_corner

        body_top_left_corner = shield_top_left_corner.translate(
            {"x": 10, "y": -10}, apply_on_copy=True, new_grid=None
        )
        body_bottom_right_corner = shield_bottom_right_corner.translate(
            {"x": -10, "y": 10}, apply_on_copy=True, new_grid=None
        )

    # ########################## symbol fields #################################
    ref_pos = body_top_left_corner.translate(
        {"x": body_width / 2, "y": ref_fontsize}, apply_on_copy=True
    )

    reference = current_symbol.get_property("Reference")
    reference.set_pos_mil(ref_pos.x, ref_pos.y, 0)
    reference.effects.sizex = kicad_sym.mil_to_mm(ref_fontsize)
    reference.effects.sizey = reference.effects.sizex

    value_pos = body_bottom_right_corner.translate(
        {"x": -body_width / 2 + (50 if extra_pin else 0), "y": -ref_fontsize},
        apply_on_copy=True,
    )

    value = current_symbol.get_property("Value")
    value.set_pos_mil(value_pos.x, value_pos.y, 0)
    value.effects.sizex = kicad_sym.mil_to_mm(ref_fontsize)
    value.effects.sizey = value.effects.sizex
    value.effects.v_justify = "left" if extra_pin else "center"

    # ########################## artwork #################################
    drawing = Drawing()

    if series_params.enclosing_rectangle:
        drawing.append(
            DrawingRectangle(
                start=body_top_left_corner,
                end=body_bottom_right_corner,
                line_width=body_outline_line_width,
                fill=body_fill,
            )
        )

    if extra_pin == SHIELD_PIN:
        drawing.append(
            DrawingRectangle(
                start=shield_top_left_corner,
                end=shield_bottom_right_corner,
                line_width=inner_graphics_line_width,
                fill=ElementFill.NO_FILL,
            )
        )

    if extra_pin:
        drawing.append(
            DrawingPin(
                at=extra_pin_pos,
                number=extra_pin["number"],
                name=extra_pin["name"],
                pin_length=extra_pin_length,
                orientation=DrawingPin.PinOrientation.UP,
            )
        )
        if extra_pin["deco"]:
            drawing.append(extra_pin["deco"](extra_pin_pos, extra_pin_length))

    repeated_drawing = [innerArtwork(series_params.graphic_type)]

    if series_params.num_rows == 2:
        repeated_drawing.append(
            repeated_drawing[0]
            .mirrorHorizontal(apply_on_copy=True)
            .translate({"x": body_bottom_right_corner.x, "y": top_right_pin_position.y})
        )
    repeated_drawing[0].translate(
        {"x": body_top_left_corner.x, "y": top_left_pin_position.y}
    )

    pin_number_0 = series_params.top_pin_number[0]
    pin_name_0 = pinname_update_function(None, pin_number_0)
    repeated_drawing[0].append(
        DrawingPin(
            at=top_left_pin_position,
            number=pin_number_0,
            name=pin_name_0,
            pin_length=pin_length + (10 if extra_pin == SHIELD_PIN else 0),
            orientation=DrawingPin.PinOrientation.RIGHT,
        )
    )

    if series_params.num_rows == 2:
        pin_number_1 = series_params.top_pin_number[1](num_pins_per_row)
        pin_name_1 = pinname_update_function(None, pin_number_1)
        repeated_drawing[1].append(
            DrawingPin(
                at=top_right_pin_position,
                number=pin_number_1,
                name=pin_name_1,
                pin_length=pin_length + (10 if extra_pin == SHIELD_PIN else 0),
                orientation=DrawingPin.PinOrientation.LEFT,
            )
        )

    drawing.append(
        DrawingArray(
            original=repeated_drawing[0],
            distance={"x": 0, "y": -pin_spacing_y},
            number_of_instances=num_pins_left_side,
            pinnumber_update_function=series_params.pin_number_generator[0],
            pinname_update_function=pinname_update_function,
            pin_gap_positions=pin_gap_positions,
        )
    )

    if series_params.num_rows == 2:
        drawing.append(
            DrawingArray(
                original=repeated_drawing[1],
                distance={"x": 0, "y": -pin_spacing_y},
                number_of_instances=num_pins_per_row,
                pinnumber_update_function=series_params.pin_number_generator[1],
                pinname_update_function=pinname_update_function,
                pin_gap_positions=pin_gap_positions,
            )
        )

    if series_params.mirror:
        drawing.mirrorHorizontal()

    drawing.appendToSymbol(current_symbol)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generator for Generic{extra_pin:s} connector symbols"
    )
    parser.add_argument(
        "--filter",
        type=str,
        nargs="?",
        help="what symbols should be generated",
        default="*",
    )
    args = parser.parse_args()

    modelfilter = args.filter
    libname = "conn_new"
    for arg in sys.argv[1:]:
        if arg.startswith("sf="):
            modelfilter = arg[len("sf=") :]
        if arg.startswith("o="):
            libname = arg[len("o=") :]

    if not modelfilter:
        modelfilter = "*"

    model_filter_regobj = re.compile(fnmatch.translate(modelfilter))

    for lib in all_symbols:
        library = kicad_sym.KicadLibrary(lib["lib_name"] + ".kicad_sym")
        print(lib["lib_name"])
        for series_name, series_params in lib["symbol_def"].items():
            if model_filter_regobj.match(series_name):
                for num_pins_per_row in series_params.pin_per_row_range:
                    generateSingleSymbol(library, series_params, num_pins_per_row, lib)
        library.write()
