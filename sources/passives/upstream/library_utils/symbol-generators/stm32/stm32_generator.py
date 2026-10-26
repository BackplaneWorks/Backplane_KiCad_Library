#!/usr/bin/env python3

import atexit
import fnmatch
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import groupby

import click
import tqdm
from bs4 import BeautifulSoup

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
from DrawingElements import Drawing, DrawingPin, DrawingRectangle, ElementFill
from Point import Point

# Device which appear in the CubeMX chip database, but do not seem to be orderable, or which we do not want to include
# for other reasons.
ignore_devices = [
    # Device does not appear on ST's website, and does not have a datasheet.
    "STM32G471*",
    "STM32G071C6T*",
    "STM32G071C6U*",
    "STM32G071G6U*",
    "STM32G071K6T*",
    "STM32G071K6U*",
    "STM32G071R6T*",
    "STM32G411*",
    "STM32G414*",
    "STM32L485*",
    "STM32WBA50KEU*",
    "STM32WBA50KGU*",
]

# Manual overrides for parts with non-standard datasheet locations
datasheet_fixups = {
    "STM32F768A*": "https://www.st.com/resource/en/datasheet/stm32f767zi.pdf",
    "STM32F769*": "https://www.st.com/resource/en/datasheet/stm32f767zi.pdf",
    "STM32WLE5*": "https://www.st.com/resource/en/datasheet/stm32wle5j8.pdf",
    "STM32U5F*": "https://www.st.com/resource/en/datasheet/stm32u5f7vj.pdf",
    "STM32WBA5*": "https://www.st.com/resource/en/datasheet/stm32wba52ce.pdf",
    "STM32F439*": "https://www.st.com/resource/en/datasheet/stm32f437ai.pdf",
}

# Match everything before the first separator, which may be one of [space], /, -.
# However, do match dashes (-) when they are the last character in the name (VREF-)
_PINNAME_MATCH = re.compile("[^ /-]*(-$)?")


def pinkey(pin):
    """Split pin name into alphabetic and numeric parts and parse numeric parts, for
    sorting. Example:

    'DDR1_DQ15B' -> ('DDR', 1, '_DQ', 15, 'B')
    """
    return tuple(
        [
            int(num) if num else char
            for num, char in re.findall("([0-9]+)|([^0-9]+)", pin.name)
        ]
    )


@dataclass
class DataPin:
    num: str  # may also be an BGA pin coordinate
    name: str
    pintype: str
    altfuncs: list = field(default_factory=list)
    graphical_type: str = "other"
    electrical_type: str = "input"
    variant: str | None = None

    def __post_init__(self):
        # Maps regex for {XML pintype}/{XML pin name} to {graphical}/{electrical} type.
        # Graphical type is used by this script further down to determine placement,
        # and electrical type is saved in the symbol for KiCad's electrical rule check.
        type_lookup = {
            r"(Power|MonoIO)/VREF": "special_power/input",
            r"Power/VCAP": "vcap/power_output",
            r"Power/(VDD|VBAT|VLCD)": "vdd/power_input",
            r"Power/VSS": "vss/power_input",
            r"Power/VFB": "other/input",
            r"Power/VLCD": "vdd/power_output",
            r"Power/REGOFF": "other/input",
            r"Power/RFU": "nc/nc",
            r"Power/PDR_ON": "other/input",
            r"Power/PWR_(ON|LP)": "other/output",
            r"Power/IRROFF": "other/input",
            r"Power/NPOR": "other/input",
            r"I/O/PWR_CPU_ON": "other/output",
            r"Power/": "special_power/power_input",
            r"(I/O|MonoIO)/(.*-)?OSC_(IN|OUT)": "clock/input",
            r"I/O/(OPAMP|AOP).*": "other/input",
            r"I/O": "port/bidir",
            r"Clock/P([A-Z)([0-9]+)": "port/bidir",
            r"Clock/": "clock/input",
            r"Reset/": "reset/input",
            r"Boot/": "boot/input",
            r"NC/": "nc/nc",
            r"MonoIO/": "monoio/bidir",
        }

        name_lookup = {
            "PC14OSC32_IN": "PC14",
            "PC15OSC32_OUT": "PC15",
            "PF11BOOT0": "PF11",
        }

        if self.name in name_lookup:
            self.name = name_lookup[self.name]

        for k, v in type_lookup.items():
            if re.match(k, f"{self.pintype}/{self.name}"):
                self.graphical_type, self.electrical_type = v.split("/")
                break
        else:
            self.graphical_type = "other"

    def draw(self, pin_length=200, direction="left", x=0, y=0, visible=True):
        visibility = (
            DrawingPin.PinVisibility.VISIBLE
            if visible
            else DrawingPin.PinVisibility.INVISIBLE
        )  # NOQA
        orientation = getattr(DrawingPin.PinOrientation, direction.upper())
        el_type = getattr(
            DrawingPin.PinElectricalType, f"EL_TYPE_{self.electrical_type.upper()}"
        )

        # invisible stacked power pins should have passive electrical type or the linter gets angry
        if self.electrical_type == "power_input" and not visible:
            el_type = DrawingPin.PinElectricalType.EL_TYPE_PASSIVE

        return DrawingPin(
            Point(x, y),
            self.num,
            orientation=orientation,
            visibility=visibility,
            pin_length=pin_length,
            name=self.name,
            altfuncs=self.altfuncs,
            el_type=el_type,
        )


class Device:
    _name_search = re.compile(r"^(.+)\((.+)\)(.+)$")
    _pincount_search = re.compile(r"^[a-zA-Z]+([0-9]+)$")
    _pkgname_sub = re.compile(r"([a-zA-Z]+)([0-9]+)(-.*|)")

    # useful command for identifying datasheets in pdftotext output:
    # sha256sum (ag '^[^a-zA-Z]*[0-9][^a-zA-Z]*This (pin|ball) should' -l|sed s/.txt/.pdf/|sort)
    _NC_OVERRIDES = {
        # These parts have some NC pins with very specific requirements that are sadly not marked
        # in the source XML. The affected parts are all in TFBGA240 packages. On their sister
        # models, these pins are used for the internal switchmode regulator.
        # See https://gitlab.com/kicad/libraries/kicad-symbols/-/issues/3135
        r"STM32H74[23]X.*H.|STM32H750X.*H.|STM32H753X.*H.": {
            "F1": ("Power", "VDD_OR_VSS"),
            "F2": ("Power", "VSS"),
            "G2": ("Power", "VSS"),
        },
    }
    _POWER_PAD_FIX_PACKAGES = {"UFQFPN32", "UFQFPN48", "VFQFPN36", "VFQFPN68"}
    _FOOTPRINT_MAPPING = {
        "SO8N": (
            "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "SO*3.9x4.9mm*P1.27mm*",
        ),  # NOQA
        "LFBGA100": (
            "Package_BGA:LFBGA-100_10x10mm_Layout10x10_P0.8mm",
            "LFBGA*10x10mm*Layout10x10*P0.8mm*",
        ),  # NOQA
        "LFBGA144": (
            "Package_BGA:LFBGA-144_10x10mm_Layout12x12_P0.8mm",
            "LFBGA*10x10mm*Layout12x12*P0.8mm*",
        ),  # NOQA
        "LFBGA289": (
            "Package_BGA:LFBGA-289_14x14mm_Layout17x17_P0.8mm",
            "LFBGA*14x14mm*Layout17x17*P0.8mm*",
        ),  # NOQA
        "LFBGA354": (
            "Package_BGA:ST_LFBGA-354_16x16mm_Layout19x19_P0.8mm",
            "ST*LFBGA*16x16mm*Layout19x19*P0.8mm*",
        ),  # NOQA
        "LFBGA448": (
            "Package_BGA:ST_LFBGA-448_18x18mm_Layout22x22_P0.8mm",
            "ST*LFBGA*18x18mm*Layout22x22*P0.8mm*",
        ),  # NOQA
        "LQFP32": ("Package_QFP:LQFP-32_7x7mm_P0.8mm", "LQFP*7x7mm*P0.8mm*"),  # NOQA
        "LQFP48": ("Package_QFP:LQFP-48_7x7mm_P0.5mm", "LQFP*7x7mm*P0.5mm*"),  # NOQA
        "LQFP64": (
            "Package_QFP:LQFP-64_10x10mm_P0.5mm",
            "LQFP*10x10mm*P0.5mm*",
        ),  # NOQA
        "LQFP80-12X12": (
            "Package_QFP:LQFP-80_12x12mm_P0.5mm",
            "LQFP*12x12mm*P0.5mm*",
        ),  # NOQA
        "LQFP80-14X14": (
            "Package_QFP:LQFP-80_14x14mm_P0.65mm",
            "LQFP*14x14mm*P0.65mm*",
        ),  # NOQA
        "LQFP100": (
            "Package_QFP:LQFP-100_14x14mm_P0.5mm",
            "LQFP*14x14mm*P0.5mm*",
        ),  # NOQA
        "LQFP128": (
            "Package_QFP:LQFP-128_14x14mm_P0.4mm",
            "LQFP*14x14mm*P0.4mm*",
        ),  # NOQA
        "LQFP144": (
            "Package_QFP:LQFP-144_20x20mm_P0.5mm",
            "LQFP*20x20mm*P0.5mm*",
        ),  # NOQA
        "LQFP176": (
            "Package_QFP:LQFP-176_24x24mm_P0.5mm",
            "LQFP*24x24mm*P0.5mm*",
        ),  # NOQA
        "LQFP208": (
            "Package_QFP:LQFP-208_28x28mm_P0.5mm",
            "LQFP*28x28mm*P0.5mm*",
        ),  # NOQA
        "TFBGA64": (
            "Package_BGA:TFBGA-64_5x5mm_Layout8x8_P0.5mm",
            "TFBGA*5x5mm*Layout8x8*P0.5mm*",
        ),  # NOQA
        "TFBGA100": (
            "Package_BGA:TFBGA-100_8x8mm_Layout10x10_P0.8mm",
            "TFBGA*8x8mm*Layout10x10*P0.8mm*",
        ),  # NOQA
        "TFBGA169": (
            "Package_BGA:ST_TFBGA-169_7x7mm_Layout13x13_P0.5mm",
            "ST*TFBGA*7x7mm*Layout13x13*P0.5mm*",
        ),  # NOQA
        "TFBGA216": (
            "Package_BGA:TFBGA-216_13x13mm_Layout15x15_P0.8mm",
            "TFBGA*13x13mm*Layout15x15*P0.8mm*",
        ),  # NOQA
        "TFBGA225": (
            "Package_BGA:ST_TFBGA-225_13x13mm_Layout15x15_P0.8mm",
            "ST*TFBGA*13x13mm*Layout15x15*P0.8mm*",
        ),  # NOQA
        "TFBGA240": (
            "Package_BGA:TFBGA-265_14x14mm_Layout17x17_P0.8mm",
            "TFBGA*14x14mm*Layout17x17*P0.8mm*",
        ),  # NOQA
        "TFBGA257": (
            "Package_BGA:ST_TFBGA-257_10x10mm_Layout19x19_P0.5mmP0.65mm",
            "ST*TFBGA*10x10mm*Layout19x19*P0.5mmP0.65mm*",
        ),  # NOQA
        "TFBGA289": (
            "Package_BGA:TFBGA-289_9x9mm_Layout17x17_P0.5mm",
            "TFBGA*9x9mm*Layout17x17*P0.5mm*",
        ),  # NOQA
        "TFBGA320": (
            "Package_BGA:ST_TFBGA-320_11x11mm_Layout21x21_P0.5mm",
            "ST*TFBGA*11x11mm*Layout21x21*P0.5mm*",
        ),  # NOQA
        "TFBGA361": (
            "Package_BGA:ST_TFBGA-361_12x12mm_Layout23x23_P0.5mmP0.65mm",
            "ST*TFBGA*12x12mm*Layout23x23*P0.5mmP0.65mm*",
        ),  # NOQA
        "TFBGA436": (
            "Package_BGA:ST_TFBGA-436_18x18mm_Layout22x22_P0.8mm",
            "ST*TFBGA*18x18mm*Layout22x22*P0.8mm*",
        ),  # NOQA
        "TSSOP14": (
            "Package_SO:TSSOP-14_4.4x5mm_P0.65mm",
            "TSSOP*4.4x5mm*P0.65mm*",
        ),  # NOQA
        "TSSOP20": (
            "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm",
            "TSSOP*4.4x6.5mm*P0.65mm*",
        ),  # NOQA
        "UFBGA59": (
            "Package_BGA:ST_UFBGA-59_5x5mm_Layout8x8_P0.5mm",
            "ST*UFBGA*5x5mm*Layout8x8*P0.5mm*",
        ),  # NOQA
        "UFBGA64": (
            "Package_BGA:UFBGA-64_5x5mm_Layout8x8_P0.5mm",
            "UFBGA*5x5mm*Layout8x8*P0.5mm*",
        ),  # NOQA
        "UFBGA73": (
            "Package_BGA:ST_UFBGA-73_5x5mm_Layout9x9_P0.5mm",
            "ST*UFBGA*5x5mm*Layout9x9*P0.5mm*",
        ),  # NOQA
        "UFBGA81": (
            "Package_BGA:ST_UFBGA-81_5x5mm_Layout9x9_P0.5mm",
            "ST*UFBGA*5x5mm*Layout9x9*P0.5mm*",
        ),  # NOQA
        "UFBGA100": (
            "Package_BGA:UFBGA-100_7x7mm_Layout12x12_P0.5mm",
            "UFBGA*7x7mm*Layout12x12*P0.5mm*",
        ),  # NOQA
        "UFBGA121": (
            "Package_BGA:ST_UFBGA-121_6x6mm_Layout11x11_P0.5mm",
            "ST*UFBGA*6x6mm*Layout11x11*P0.5mm*",
        ),  # NOQA
        "UFBGA129": (
            "Package_BGA:ST_UFBGA-129_7x7mm_Layout13x13_P0.5mm",
            "ST*UFBGA*7x7mm*Layout13x13*P0.5mm*",
        ),  # NOQA
        "UFBGA132": (
            "Package_BGA:UFBGA-132_7x7mm_Layout12x12_P0.5mm",
            "UFBGA*7x7mm*Layout12x12*P0.5mm*",
        ),  # NOQA
        "UFBGA144-7X7": (
            "Package_BGA:UFBGA-144_7x7mm_Layout12x12_P0.5mm",
            "UFBGA*7x7mm*Layout12x12*P0.5mm*",
        ),  # NOQA
        "UFBGA144-10X10": (
            "Package_BGA:UFBGA-144_10x10mm_Layout12x12_P0.8mm",
            "UFBGA*10x10mm*Layout12x12*P0.8mm*",
        ),  # NOQA
        "UFBGA169": (
            "Package_BGA:UFBGA-169_7x7mm_Layout13x13_P0.5mm",
            "UFBGA*7x7mm*Layout13x13*P0.5mm*",
        ),  # NOQA
        "UFBGA176": (
            "Package_BGA:UFBGA-201_10x10mm_Layout15x15_P0.65mm",
            "UFBGA*10x10mm*Layout15x15*P0.65mm*",
        ),  # NOQA
        "VFBGA361": (
            "Package_BGA:ST_VFBGA-361_10x10mm_Layout19x19_P0.5mm",
            "ST*VFBGA*10x10mm*Layout19x19*P0.5mm*",
        ),  # NOQA
        "VFBGA424": (
            "Package_BGA:ST_VFBGA-424_14x14mm_Layout27x27_P0.5mmP0.5x0.5mm_Stagger",
            "ST*VFBGA*14x14mm*Layout27x27*P0.5mmP0.5x0.5mm*Stagger*",
        ),  # NOQA
        "UFQFPN20": (
            "Package_DFN_QFN:ST_UFQFPN-20_3x3mm_P0.5mm",
            "ST*UFQFPN*3x3mm*P0.5mm*",
        ),  # NOQA
        "UFQFPN28": (
            "Package_DFN_QFN:QFN-28_4x4mm_P0.5mm",
            "QFN*4x4mm*P0.5mm*",
        ),  # NOQA
        "UFQFPN32": (
            "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm",
            "QFN*1EP*5x5mm*P0.5mm*",
        ),  # NOQA
        "VFQFPN32": (
            "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.7x3.7mm",
            "QFN*1EP*5x5mm*P0.5mm*",
        ),  # NOQA
        "VFQFPN36": (
            "Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm_EP4.1x4.1mm",
            "QFN*1EP*6x6mm*P0.5mm*",
        ),  # NOQA
        "UFQFPN48": (
            "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
            "QFN*1EP*7x7mm*P0.5mm*",
        ),  # NOQA
        "VFQFPN48": (
            "Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.5mm_EP4.4x4.4mm",
            "QFN*1EP*6x6MM*P0.5mm*",
        ),  # NOQA
        "VFQFPN68": (
            "Package_DFN_QFN:QFN-68-1EP_8x8mm_P0.4mm_EP6.4x6.4mm",
            "QFN*1EP*8x8mm*P0.4mm*",
        ),  # NOQA
    }
    _WLCSP_MAP = {
        "ST_WLCSP-100_Die495": (
            "Package_CSP:ST_WLCSP-100_4.4x4.38mm_Layout10x10_P0.4mm_Offcenter",
            "ST*WLCSP*4.4x4.38mm*Layout10x10*P0.4mm*Offcenter*",
        ),  # NOQA
        "ST_WLCSP-100_Die471": (
            "Package_CSP:ST_WLCSP-100_4.437x4.456mm_Layout10x10_P0.4mm",
            "ST*WLCSP*4.437x4.456mm*Layout10x10*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-99_Die415": (
            "Package_CSP:ST_WLCSP-99_4.42x3.77mm_Layout11x9_P0.35mm",
            "ST*WLCSP*4.42x3.77mm*Layout11x9*P0.35mm*",
        ),  # NOQA
        "ST_WLCSP-115_Die483": (
            "Package_CSP:ST_WLCSP-115_3.73x4.15mm_Layout11x21_P0.35mm_Stagger",
            "ST*WLCSP*3.73x4.15mm*Layout11x21*P0.35mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-115_Die461": (
            "Package_CSP:ST_WLCSP-115_4.63x4.15mm_Layout21x11_P0.4mm_Stagger",
            "ST*WLCSP*4.63x4.15mm*Layout21x11*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-132_Die480": (
            "Package_CSP:ST_WLCSP-132_4.57x4.37mm_Layout12x11_P0.35mm",
            "ST*WLCSP*4.57x4.37mm*Layout12x11*P0.35mm*",
        ),  # NOQA
        "ST_WLCSP-156_Die450": (
            "Package_CSP:ST_WLCSP-156_4.96x4.64mm_Layout13x12_P0.35mm",
            "ST*WLCSP*4.96x4.64mm*Layout13x12*P0.35mm*",
        ),  # NOQA
        "ST_WLCSP-18_Die466": (
            "Package_CSP:ST_WLCSP-18_1.86x2.14mm_Layout7x5_P0.4mm_Stagger",
            "ST*WLCSP*1.86x2.14mm*Layout7x5*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-25_Die460": (
            "Package_CSP:ST_WLCSP-25_2.3x2.48mm_Layout5x5_P0.4mm",
            "ST*WLCSP*2.3x2.48mm*Layout5x5*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-36_Die464": (
            "Package_CSP:ST_WLCSP-36_2.58x3.07mm_Layout6x6_P0.4mm",
            "ST*WLCSP*2.58x3.07mm*Layout6x6*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-49_Die468": (
            "Package_CSP:ST_WLCSP-49_3.15x3.13mm_Layout7x7_P0.4mm",
            "ST*WLCSP*3.15x3.13mm*Layout7x7*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-64_Die479": (
            "Package_CSP:ST_WLCSP-64_3.56x3.52mm_Layout8x8_P0.4mm",
            "ST*WLCSP*3.56x3.52mm*Layout8x8*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-81_Die469": (
            "Package_CSP:ST_WLCSP-81_4.02x4.27mm_Layout9x9_P0.4mm",
            "ST*WLCSP*4.02x4.27mm*Layout9x9*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-81_Die472": (
            "Package_CSP:ST_WLCSP-81_4.36x4.07mm_Layout9x9_P0.4mm",
            "ST*WLCSP*4.36x4.07mm*Layout9x9*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-20_Die456": (
            "Package_CSP:ST_WLCSP-20_1.94x2.4mm_Layout4x5_P0.4mm",
            "ST*WLCSP*1.94x2.4mm*Layout4x5*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-49_Die494": (
            "Package_CSP:ST_WLCSP-49_3.3x3.38mm_Layout7x7_P0.4mm_Offcenter",
            "ST*WLCSP*3.3x3.38mm*Layout7x7*P0.4mm*Offcenter*",
        ),  # NOQA
        "ST_WLCSP-52_Die467": (
            "Package_CSP:ST_WLCSP-52_3.09x3.15mm_Layout13x8_P0.4mm_Stagger",
            "ST*WLCSP*3.09x3.15mm*Layout13x8*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-90_Die482": (
            "Package_CSP:ST_WLCSP-90_4.2x3.95mm_Layout18x10_P0.4mm_Stagger",
            "ST*WLCSP*4.2x3.95mm*Layout18x10*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-12_Die443": (
            "Package_CSP:ST_WLCSP-12_1.7x1.42mm_Layout4x6_P0.35mm_Stagger",
            "ST*WLCSP*1.7x1.42mm*Layout4x6*P0.35mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-25_Die474": (
            "Package_CSP:ST_WLCSP-25_2.33x2.24mm_Layout5x5_P0.4mm",
            "ST*WLCSP*2.33x2.24mm*Layout5x5*P0.4mm*",
        ),  # NOQA
        "ST_WLCSP-80_Die484": (
            "Package_CSP:ST_WLCSP-80_3.5x3.27mm_Layout10x16_P0.35mm_Stagger_Offcenter",
            "ST*WLCSP*3.5x3.27mm*Layout10x16*P0.35mm*Stagger*Offcenter*",
        ),  # NOQA
        "ST_WLCSP-208_Die481": (
            "Package_CSP:ST_WLCSP-208_5.38x5.47mm_Layout26x16_P0.35mm_Stagger",
            "ST*WLCSP*5.38x5.47mm*Layout26x16*P0.35mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-150_Die481": (
            "Package_CSP:ST_WLCSP-150_5.38x5.47mm_Layout13x23_P0.4mm_Stagger",
            "ST*WLCSP*5.38x5.47mm*Layout13x23*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-56_Die455": (
            "Package_CSP:ST_WLCSP-56_3.38x3.38mm_Layout14x8_P0.4mm_Stagger",
            "ST*WLCSP*3.38x3.38mm*Layout14x8*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-72_Die455": (
            "Package_CSP:ST_WLCSP-72_3.38x3.38mm_Layout16x9_P0.35mm_Stagger",
            "ST*WLCSP*3.38x3.38mm*Layout16x9*P0.35mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-42_Die489": (
            "Package_CSP:ST_WLCSP-42_2.93x2.82mm_Layout12x7_P0.4mm_Stagger",
            "ST*WLCSP*2.93x2.82mm*Layout12x7*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-101_Die485": (
            "Package_CSP:ST_WLCSP-101_3.86x3.79mm_Layout11x19_P0.35mm_Stagger",
            "ST*WLCSP*3.86x3.79mm*Layout11x19*P0.35mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-27_Die459": (
            "Package_CSP:ST_WLCSP-27_2.34x2.55mm_Layout9x6_P0.4mm_Stagger",
            "ST*WLCSP*2.34x2.55mm*Layout9x6*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-208_Die476": (
            "Package_CSP:ST_WLCSP-208_5.8x5.6mm_Layout26x16_P0.35mm_Stagger",
            "ST*WLCSP*5.8x5.6mm*Layout26x16*P0.35mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-49_Die01E": (
            "Package_CSP:ST_WLCSP-49_3.14x3.14mm_Layout7x7_P0.4mm_Offcenter",
            "ST*WLCSP*3.14x3.14mm*Layout7x7*P0.4mm*Offcenter*",
        ),  # NOQA
        "ST_WLCSP-36_Die028": (
            "Package_CSP:ST_WLCSP-36_2.652x2.592mm_Layout7x12_P0.4mm_Stagger_Offcenter",
            "ST*WLCSP*2.652x2.592mm*Layout7x12*P0.4mm*Stagger*Offcenter*",
        ),  # NOQA
        "ST_WLCSP-36_Die032": (
            "Package_CSP:ST_WLCSP-36_2.83x2.99mm_Layout7x13_P0.4mm_Stagger_Offcenter",
            "ST*WLCSP*2.83x2.99mm*Layout7x13*P0.4mm*Stagger*Offcenter*",
        ),  # NOQA
        "ST_WLCSP-39_Die478": (
            "Package_CSP:ST_WLCSP-39_2.76x2.78mm_Layout11x7_P0.4mm_Stagger",
            "ST*WLCSP*2.76x2.78mm*Layout11x7*P0.4mm*Stagger*",
        ),  # NOQA
        "ST_WLCSP-19_Die493": (
            "Package_CSP:ST_WLCSP-19_1.643x2.492mm_Layout4x11_P0.35mm_Stagger",
            "ST*WLCSP*1.643x2.492mm*Layout4x11*P0.35mm*Stagger*",
        ),  # NOQA
    }
    _LEGACY_WLCSPs = [
        "ST_WLCSP-100_Die422",
        "ST_WLCSP-100_Die446",
        "ST_WLCSP-100_Die452",
        "ST_WLCSP-100_Die461",
        "ST_WLCSP-104_Die437",
        "ST_WLCSP-143_Die419",
        "ST_WLCSP-143_Die449",
        "ST_WLCSP-144_Die470",
        "ST_WLCSP-168_Die434",
        "ST_WLCSP-180_Die451",
        "ST_WLCSP-25_Die425",
        "ST_WLCSP-25_Die444",
        "ST_WLCSP-25_Die457",
        "ST_WLCSP-36_Die417",
        "ST_WLCSP-36_Die440",
        "ST_WLCSP-36_Die445",
        "ST_WLCSP-36_Die458",
        "ST_WLCSP-49_Die423",
        "ST_WLCSP-49_Die431",
        "ST_WLCSP-49_Die433",
        "ST_WLCSP-49_Die435",
        "ST_WLCSP-49_Die438",
        "ST_WLCSP-49_Die439",
        "ST_WLCSP-49_Die447",
        "ST_WLCSP-49_Die448",
        "ST_WLCSP-63_Die427",
        "ST_WLCSP-64_Die414",
        "ST_WLCSP-64_Die427",
        "ST_WLCSP-64_Die435",
        "ST_WLCSP-64_Die436",
        "ST_WLCSP-64_Die441",
        "ST_WLCSP-64_Die442",
        "ST_WLCSP-64_Die462",
        "ST_WLCSP-66_Die411",
        "ST_WLCSP-66_Die432",
        "ST_WLCSP-72_Die415",
        "ST_WLCSP-81_Die415",
        "ST_WLCSP-81_Die421",
        "ST_WLCSP-81_Die463",
        "ST_WLCSP-90_Die413",
    ]

    def __init__(self, xml):
        soup = BeautifulSoup(xml.read_text(), features="xml").find("Mcu")
        self.name = soup["RefName"].replace("(", "_").replace(")", "_")

        # Get the package code
        package = soup["Package"]

        package, _, pinout_variant = package.partition(" ")

        # Some C0 series parts such as the STM32C071x8/xB have two variants in some packages, where one variant
        # sacrifices a GPIO for an additional VDDIO pin. For some reason, ST decided to put that info here as a suffix
        # ("_GP" - normal, "general purpose" I guess?, "_N" alternate with additional VDDIO), so we have to cut it off
        # as the actual physical packages are completely identical, at least from the outside.
        package, _, pinout_variant = package.partition("_")

        if package == "UFBGA144":
            # ST uses the name "UFBGA144" for two sizes of BGA, and there's no way to tell to pick
            # them apart besides the part number's package ID letter
            try:
                # Some newer parts have an extra "Q" at the end of their RPN indicating an alternate pinout.
                package_letter = self.name.rstrip("Q")[-2]
                package += {
                    "H": "-7X7",
                    "I": "-7X7",
                    "J": "-10X10",
                }[package_letter]
            except KeyError:
                tqdm.tqdm.write(
                    "Unable to determine UFBGA144 variant (7x7mm or 10x10mm) "
                    f"for device {self.name}"
                )

        elif package == "LQFP80":
            # Same as above
            try:
                package += {
                    "T": "-12X12",
                    "S": "-14X14",
                }[self.name[-2]]
            except KeyError:
                tqdm.tqdm.write(
                    "Unable to determine LQFP80 variant "
                    f"(12x12mm/p0.5 or 14x14mm/p0.65) for device {self.name}"
                )

        self.package = package

        if m := re.fullmatch(r"E?WLCSP([0-9]*)", package):
            # Differentiate the WLCSP packages by die code
            die = soup.find("Die").text.title()

            if m.group(1) == "59" and die == "Die497":
                # This chip has no datasheet, is not on ST's website and cannot be bought.
                self.footprint_filters = "*"
                self.footprint = ""

            else:
                pkg = f"ST_WLCSP-{m.group(1)}_{die}"

                if pkg in self._WLCSP_MAP:
                    self.footprint, self.footprint_filters = self._WLCSP_MAP[pkg]
                elif pkg in self._LEGACY_WLCSPs:
                    self.footprint_filters = f"ST*WLCSP*{die}*"
                    self.footprint = f"Package_CSP:{pkg}"
                else:
                    tqdm.tqdm.write(
                        "Missing WLCSP package for "
                        f"device {self.name}, package {self.package}, die ID {die}"
                    )
                    self.footprint_filters = "*"
                    self.footprint = ""

        elif package in self._FOOTPRINT_MAPPING:
            self.footprint, self.footprint_filters = self._FOOTPRINT_MAPPING[
                self.package
            ]

        else:
            tqdm.tqdm.write(
                "No footprint/footprint filters found for "
                f"device {self.name}, package {self.package}"
            )
            self.footprint_filters = "*"
            self.footprint = ""

        for pattern, nc_override in self._NC_OVERRIDES.items():
            if re.fullmatch(pattern, self.name):
                break
        else:
            nc_override = {}

        # Read the information for each pin
        pins_by_number = defaultdict(lambda: [])
        for child in soup.find_all("Pin"):
            pos, name, pintype = child["Position"], child["Name"], child["Type"]

            # Apply overrides for semantically relevant pins that are not properly described in the
            # XML.
            # NOTE: The VDD*_Unused pins must not be mapped to NCs. They are necessary when
            # designing a board that should be upwards-compatible.
            if name in ("NC", "DNU"):
                pintype, name = nc_override.get(pos, ("NC", name))

            altfuncs = []
            for signal in child.find_all("Signal"):
                altfunction = signal["Name"]
                if altfunction != "GPIO":
                    altfuncs.append(
                        kicad_sym.AltFunction(altfunction, "bidirectional", "line")
                    )

            name = _PINNAME_MATCH.match(name).group()
            pins_by_number[pos].append(
                DataPin(pos, name, pintype, altfuncs, variant=child.get("Variant"))
            )

        # If this part has a power pad, we have to add it manually
        if (
            soup["HasPowerPad"] == "true"
            or self.package in Device._POWER_PAD_FIX_PACKAGES
        ):
            # Read pin count from package name
            packPinCountR = Device._pincount_search.search(self.package)
            powerpinnumber = str(int(packPinCountR.group(1)) + 1)
            # Create power pad pin
            if powerpinnumber not in pins_by_number:
                pins_by_number[powerpinnumber].append(
                    DataPin(powerpinnumber, "VSS", "Power")
                )

        # Merge pins where multiple pins of the die are bonded out to a single pin on the package.
        self.pins = []
        for pos, pin_list in pins_by_number.items():
            # Pins with the Variant attribute are not bonded, but describe
            # a remapping. Default after reset is no remap.
            default = [pin for pin in pin_list if pin.variant is None]
            remapped = [pin for pin in pin_list if pin.variant is not None]

            def alternates_of(pin):
                yield kicad_sym.AltFunction(pin.name, "bidirectional", "line")
                for func in pin.altfuncs:
                    yield kicad_sym.AltFunction(
                        f"{func.name} ({pin.name})", func.etype, func.shape
                    )

            if len(default) == 1:
                merged = default[0]
            else:
                default = sorted(default, key=pinkey)
                merged = DataPin(
                    pos,
                    "/".join(pin.name for pin in default),
                    default[0].pintype,
                    [alt for pin in default for alt in alternates_of(pin)],
                )

            merged.altfuncs = merged.altfuncs + [
                alt
                for pin in sorted(remapped, key=pinkey)
                for alt in alternates_of(pin)
            ]
            self.pins.append(merged)

    def create_symbol(self, lib, keywords, desc, datasheet):
        # Make the symbol
        self.symbol = kicad_sym.KicadSymbol.new(
            self.name,
            lib.filename,
            "U",
            self.footprint,
            datasheet,
            keywords,
            desc,
            self.footprint_filters,
        )

        lib.symbols.append(self.symbol)

        # Draw the symbol
        self.draw_symbol()

    def draw_symbol(self):
        pin_length = 100 if all(len(pin.num) < 3 for pin in self.pins) else 200

        pins = defaultdict(lambda: [])
        # Classify pins
        for pin in self.pins:
            pins[pin.graphical_type].append(pin)

        pins = defaultdict(
            lambda: [], {k: sorted(v, key=pinkey) for k, v in pins.items()}
        )

        def split_groups(pins, expr=r".*"):
            """Split pin list by either a regex or a list of regexes.

            If a single regex is given: Split list into one group for each distinct match value.
            E.g. for input P1A, P1B, P2A, P2B:

            'P.' -> [P1A, P1B], [P2A, P2B]

            If a list of regexis is given: Split the list into one group for each matching regex.
            e.g. for input USB_DP, USB_DM, ANA0, ANA1:

            ['USB.*', 'ANA.*'] -> [USB_DP, USB_DM], [ANA0, ANA1]
            """
            if isinstance(expr, str):
                pins = sorted(
                    ((re.match(expr, pin.name).group(0), pin) for pin in pins),
                    key=lambda e: e[0],
                )
            else:
                expr = [re.compile(e) for e in [*expr, r".*"]]

                def match_pin(pin):
                    return next(
                        i for i, e in enumerate(expr) if e.fullmatch(pinkey(pin)[0])
                    )

                pins = sorted(
                    ((match_pin(pin), pin) for pin in pins), key=lambda e: e[0]
                )
            return [
                [e for key, e in group]
                for _key, group in groupby(pins, key=lambda e: e[0])
            ]

        monoio_groups = [
            "DDR_BA.*",
            "DDR_A.*",
            "DDR_DQM.*",
            "DDR_DQS.*",
            "DDR_DQ.*",
            "DDR_.*",
            "JTCK|JTDI|JTDO|JTMS|NJTRST",
            "USB.*|OTG.*",
            "PDR.*|BYPASS_REG.*",
            "ANA.*",
        ]
        left = [
            pins["reset"],
            pins["boot"],
            pins["special_power"],
            pins["clock"],
            pins["other"],
            *split_groups(pins["monoio"], monoio_groups),
            pins["vcap"],
        ]

        unhandled = [
            pin.name for pin in pins["port"] if not re.match("P[A-Z][0-9]+", pin.name)
        ]
        if unhandled:
            warnings.warn("Unhandled I/O pin name(s):" + " ".join(unhandled))
        # Split IO port pins in spaced groups by port number (i.e. PB0...15 [space] PC0...15 ...)
        right = split_groups(pins["port"], r"P.|.*")

        # [[1,2,3],[],[],[4,5,6],[7,8,9],[]] ->  [1, 2, 3, None, 4, 5, 6, None, 7, 8, 9]
        def spaced(groups) -> list:
            return [
                e
                for group in groups
                for alt in [group, [None]]
                for e in alt
                if group
            ][:-1]  # fmt: skip

        def spaced_len(lst) -> int:
            return len(spaced(lst))

        # Balance out pins on left and right sides
        while spaced_len(left) < spaced_len(right[:-1]):
            left.insert(-1, right.pop())  # insert before VCAP pin group

        # Calculate height of the symbol
        box_height = max(spaced_len(left), spaced_len(right)) * 100 + 300

        # Calculate the width of the symbol
        # Newstroke at font size 50 mil has characters around 50 mil width.
        def name_width(pins) -> int:
            return max(len(p.name) * 47 for p in pins if p) if pins else 0

        spaced_left, spaced_right = spaced(left), spaced(right)
        name_width_sides = name_width(spaced_left + spaced_right)

        stacked_vss = {
            key: list(group)
            for key, group in groupby(pins["vss"], lambda pin: pin.name)
        }
        # this depends on dict being ordered
        pins["vss"] = [group[0] for group in stacked_vss.values()]

        spaced_top, spaced_bottom = pins["vdd"], pins["vss"]
        top_width, bottom_width = len(spaced_top) * 100, len(spaced_bottom) * 100
        pin_width_top_bottom = max(top_width, bottom_width)

        box_width = (
            math.ceil(
                (name_width_sides + pin_width_top_bottom + name_width_sides + 100) / 200
            )
            * 200
        )

        drawing = Drawing()
        drawing.append(
            DrawingRectangle(
                Point(0, 0),
                Point(box_width, box_height),
                unit_idx=0,
                fill=ElementFill.FILL_BACKGROUND,
            )
        )

        for i, pin in enumerate(spaced_left, start=2):
            if pin:
                drawing.append(
                    pin.draw(pin_length, "right", x=-pin_length, y=box_height - i * 100)
                )

        for i, pin in enumerate(spaced_right, start=2):
            if pin:
                drawing.append(
                    pin.draw(
                        pin_length,
                        "left",
                        x=box_width + pin_length,
                        y=box_height - i * 100,
                    )
                )

        last_top_x = 0
        for i, pin in enumerate(spaced_top, start=1):
            if pin:
                # memorize position to later put component value here
                last_top_x = ((box_width - top_width) // 100 // 2 + i) * 100
                drawing.append(
                    pin.draw(
                        pin_length, "down", x=last_top_x, y=box_height + pin_length
                    )
                )

        for i, pin in enumerate(spaced_bottom, start=1):
            if pin:
                x = ((box_width - bottom_width) // 100 // 2 + i) * 100
                drawing.append(pin.draw(pin_length, "up", x=x, y=-pin_length))

                if pin.graphical_type == "vss":
                    for stacked in stacked_vss[pin.name][1:]:
                        drawing.append(
                            stacked.draw(
                                pin_length, "up", x=x, y=-pin_length, visible=False
                            )
                        )

        for i, pin in enumerate(pins["nc"]):
            if pin:
                # x=0 because of https://klc.kicad.org/symbol/s4/s4.6/
                drawing.append(
                    pin.draw(pin_length, "right", x=0, y=i * 100, visible=False)
                )

        # Center the symbol
        cx, cy = (
            -math.floor(box_width / 2 / 100) * 100,
            -math.floor(box_height / 2 / 100) * 100,
        )
        drawing.translate(Point(cx, cy))

        property = self.symbol.get_property("Reference")
        property.set_pos_mil(cx, cy + box_height + 50, 0)
        property.effects.h_justify = "left"

        property = self.symbol.get_property("Value")
        property.set_pos_mil(cx + last_top_x + 100, cy + box_height + 50, 0)
        property.effects.h_justify = "left"

        property = self.symbol.get_property("Footprint")
        property.set_pos_mil(cx, cy, 0)
        property.effects.h_justify = "right"
        property.effects.is_hidden = True

        drawing.appendToSymbol(self.symbol)


def upgrade_library(kicad_cli: str, output: pathlib.Path) -> None:
    """Rewrite the output through kicad-cli to get KiCad formatting

    This helps to get minimal diffs when copying to kicad-symbols.
    """
    try:
        subprocess.run(
            [kicad_cli, "sym", "upgrade", "--force", str(output)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        raise SystemExit(
            f"Could not run {kicad_cli}. Set --kicad-cli or KICAD_CLI, or pass "
            "--no-upgrade to write the file without it."
        )
    except subprocess.CalledProcessError as error:
        raise SystemExit(
            f"{' '.join(error.cmd)} exited with status {error.returncode}."
        )


@click.command()
@click.option(
    "--part-number",
    "-p",
    "part_number_pattern",
    default="*",
    help="Filter part numbers by glob",
)
@click.option(
    "--verify-datasheets/--no-verify-datasheets", help="Verify datasheet URLs exists"
)
@click.option(
    "--retry-datasheets/--no-retry-datasheets",
    default=False,
    help="Retry fetching datasheet URLs that could not be found in the past",
)
@click.option(
    "--http-timeout",
    type=float,
    default=3,
    help="Timeout for --verify-datasheet HTTP requests",
)
@click.option(
    "--skip-without-footprint/--keep-without-footprint",
    default=False,
    help="Skip generating symbols for which no footprint could be found",
)
@click.option(
    "--skip-without-datasheet/--keep-without-datasheet",
    default=False,
    help="Skip generating symbols for which no datasheet could be found",
)
@click.option(
    "--url-cache",
    type=click.Path(file_okay=True, dir_okay=False, path_type=pathlib.Path),
    help="JSON cache file for datasheet URLs",
)
@click.option(
    "--kicad-cli",
    default=lambda: os.environ.get("KICAD_CLI", "kicad-cli"),
    help="kicad-cli executable, defaults to $KICAD_CLI",
)
@click.option(
    "--upgrade/--no-upgrade",
    default=True,
    help="Rewrite the output with kicad-cli so it matches what KiCad itself writes",
)
@click.argument(
    "cubemx_mcu_db_dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path),
)
@click.argument(
    "output_file",
    type=click.Path(file_okay=True, dir_okay=True, path_type=pathlib.Path),
)
def cli(
    cubemx_mcu_db_dir,
    part_number_pattern,
    output_file,
    kicad_cli,
    upgrade,
    verify_datasheets,
    url_cache,
    skip_without_footprint,
    skip_without_datasheet,
    http_timeout,
    retry_datasheets,
):
    soup = BeautifulSoup(
        (cubemx_mcu_db_dir / "families.xml").read_text(), features="xml"
    )
    files = defaultdict(lambda: [])
    for tag in soup.find_all("Mcu", recursive=True):
        if not fnmatch.fnmatch(tag["RPN"].lower(), part_number_pattern.lower()):
            continue

        # Parse information for documentation
        frequency = tag.find("Frequency")
        frequency = f"{frequency.text} MHz, " if frequency else ""
        ram = int(tag.find("Ram").text)
        flash = tag.find("Flash")
        flash = int(flash.text) if flash else None
        io = int(tag.find("IONb").text)
        voltage = tag.find("Voltage")
        if voltage:
            voltage = f'{voltage.get("Min", voltage.get("Max", "?"))}-{voltage.get("Max", voltage.get("Min", "?"))}V, '
        else:
            voltage = ""
        refname = tag["RefName"]
        package = tag["PackageName"]
        core = tag.find("Core").text

        # Make strings for DCM entries
        flash_desc = "{flash}KB flash, " if flash is not None else ""
        desc = (
            f"STMicroelectronics {core} MCU, {flash_desc}"
            f"{{ram}}KB RAM, {frequency}{voltage}{io} GPIO, {{package}}"
        )
        keywords = (
            f'{tag.find("Core").text} {tag.parent.parent["Name"]} {tag.parent["Name"]}'
        )
        datasheet = f'https://www.st.com/resource/en/datasheet/{tag["RPN"].lower()}.pdf'

        files[tag["Name"]].append(
            (desc, keywords, datasheet, flash, ram, refname, package)
        )

    print(f"Found {sum(len(e) for e in files)} part variants.")
    print("Generating symbols...")

    lib = kicad_sym.KicadLibrary(output_file)

    if url_cache:
        url_cache_dict = json.loads(url_cache.read_text())

        @atexit.register
        def save_url_cache() -> None:
            # Sort by key for stabler diffs
            sorted_cache = dict(sorted(url_cache_dict.items()))
            url_cache.write_text(json.dumps(sorted_cache, indent=2))

    else:
        url_cache = {}

    def try_fetch_url(url):
        status_code = url_cache_dict.get(url)

        if status_code in (200, 302):
            return url

        elif status_code is None or (
            status_code in ("curl timeout", "curl error", 404) and retry_datasheets
        ):
            tqdm.tqdm.write(f"Re-trying {status_code} for {url}")
            try:
                res = subprocess.run(
                    [
                        "curl",
                        "--compressed",
                        "-H",
                        "User-Agent: Mozilla/5.0 () Gecko/20100101 Firefox/999.0",
                        "-H",
                        "From: kicad-libraries@jaseg.de",
                        "--http2",
                        "-I",
                        "--max-time",
                        str(http_timeout),
                        url,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                response_line, *_headers = res.stdout.splitlines()
                http_version, _, status_code = response_line.partition(" ")
                status_code = int(status_code)
                url_cache_dict[url] = status_code

                tqdm.tqdm.write(f"    -> {status_code}")
                if status_code in (200, 302):
                    return url

            except subprocess.CalledProcessError as e:
                if e.returncode == 28:
                    tqdm.tqdm.write("    -> curl timeout")
                    url_cache_dict[url] = "curl timeout"
                else:
                    tqdm.tqdm.write("    -> curl error")
                    url_cache_dict[url] = "curl error"

        return None

    def verify_datasheet(refname, datasheet):
        if not verify_datasheets:
            return datasheet

        if url := try_fetch_url(datasheet):
            return url

        # For most parts, the computed part numbers above work just fine. For some parts however, the filename is
        # not the complete RPN, but instead a shorter prefix of it. In case the request above was not answered
        # successfully, retry with a truncated part number. If that still doesn't work, we give up.
        for cutoff in [-5, -6]:
            # try cutting off one letter from the part number
            testurl = datasheet[:cutoff] + ".pdf"

            if url := try_fetch_url(testurl):
                tqdm.tqdm.write(
                    f"Datasheet for {refname} unexpectedly found at {testurl} instead "
                    f"of {datasheet}"
                )
                return testurl

        for pattern, url in datasheet_fixups.items():
            if fnmatch.fnmatch(refname, pattern):
                return url

        return ""

    for filename, variants in tqdm.tqdm(
        files.items(), desc=pathlib.Path(output_file).stem
    ):
        xml = cubemx_mcu_db_dir / f"{filename}.xml"

        desc, keywords, datasheet_base, flash, ram, refname, package = variants[0]

        if len(variants) == 1:
            desc = desc.format(flash=flash, ram=ram, package=package)
        else:
            flashes = [
                flash
                for _desc, _keywords, _datasheet, flash, _ram, _refname, _package in variants
                if flash is not None
            ]
            ramses = [
                ram
                for _desc, _keywords, _datasheet, _flash, ram, _refname, _package in variants
            ]
            packages = "/".join(
                sorted(
                    set(
                        package
                        for _desc, _keywords, _datasheet, _flash, _ram, _refname, package in variants
                    )
                )
            )
            minf, maxf = min(flashes, default=None), max(flashes, default=None)
            minr, maxr = min(ramses), max(ramses)
            desc = desc.format(
                package=packages,
                flash=f"{minf}-{maxf}" if minf != maxf else str(minf),
                ram=f"{minr}-{maxr}" if minr != maxr else str(minr),
            )

        if package.startswith("LGA"):
            # These are RF SoMs that for some reason has an STM32 PN and ended
            # up in features.xml. Ignore them.
            tqdm.tqdm.write(f"Skipping RF SoM {refname}.")
            continue

        variants_out = []
        for var in variants:
            _desc, _keywords, _datasheet, _flash, _ram, refname, _package = var
            if any(fnmatch.fnmatch(refname, pattern) for pattern in ignore_devices):
                tqdm.tqdm.write(f"Skipping device from ignore list {refname}.")
                continue
            variants_out.append(var)
        variants = variants_out

        if not variants:
            continue

        dev = Device(xml)

        if skip_without_footprint and not dev.footprint:
            tqdm.tqdm.write(
                f"\033[91mNo footprint for device {dev.name} "
                f"with ST package name {dev.package}, "
                f"skipping (--skip-without-footprint).\033[0m"
            )
            continue

        datasheet = verify_datasheet(refname, datasheet_base)
        if not datasheet:
            if skip_without_datasheet:
                tqdm.tqdm.write(
                    f"\033[91mNo datasheet for device {dev.name}, skipping (--skip-without-datasheet).\033[0m"
                )  # NOQA
                continue
            else:
                tqdm.tqdm.write(
                    f"\033[91mDatasheet for {refname} ({dev.name}) not found at {datasheet_base}\033[0m"
                )

        dev.create_symbol(lib, keywords=keywords, desc=desc, datasheet=datasheet)

        if len(variants) > 1:
            for desc, keywords, datasheet, flash, ram, refname, package in variants:
                desc = desc.format(flash=flash, ram=ram, package=package)

                derived_symbol = kicad_sym.KicadSymbol.new(
                    refname,
                    lib.filename,
                    "U",
                    dev.footprint,
                    datasheet,
                    keywords,
                    desc,
                    dev.footprint_filters,
                )

                derived_symbol.extends = dev.name

                def clone_formatting(dest, src, name):
                    src, dest = src.get_property(name), dest.get_property(name)
                    dest.posx = src.posx
                    dest.posy = src.posy
                    dest.effects = src.effects

                clone_formatting(derived_symbol, dev.symbol, "Reference")
                clone_formatting(derived_symbol, dev.symbol, "Value")
                clone_formatting(derived_symbol, dev.symbol, "Footprint")

                lib.symbols.append(derived_symbol)

    if lib.filename.suffix == ".kicad_symdir":
        for symbol in lib.symbols:
            symbol.libname = lib.filename.stem
            symbol.filename = lib.filename / f"{symbol.name}.kicad_sym"

    if not lib.symbols:
        tqdm.tqdm.write(f"\033[91mNo symbols for {lib.filename.name}.\033[0m")
        return

    lib.write(write_modified_only=False)

    if upgrade:
        upgrade_library(kicad_cli, lib.filename)


if __name__ == "__main__":
    cli()
