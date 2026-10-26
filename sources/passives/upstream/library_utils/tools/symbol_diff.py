#!/usr/bin/env python3

"""
This script loads 2 symbols and prints out a diff between them
in various formats.

Example usage:
python symbol_diff.py old/lib.kicad_sym:hal9000 new/lib.kicad_sym:hal9000

By default the tool prints both parsed and s-expr diff. If you want only one
of them, pass -p or -s respectively.
"""

import argparse
import difflib
import os
import sys

PYTEST_AVAILABLE = True
try:
    from _pytest.assertion.util import _compare_eq_any
except ImportError:
    PYTEST_AVAILABLE = False


common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)

if common not in sys.path:
    sys.path.insert(0, common)

from kicad_sym import KicadFileFormatError, KicadLibrary
from sexpr import build_sexp, format_sexp


def error(message: str):
    print(message)
    exit(1)


parser = argparse.ArgumentParser(description=("Print diff of two symbols"))
parser.add_argument("A", help="First symbol (libpath:symbolname)")
parser.add_argument("B", help="Second symbol (libpath:symbolname)")
parser.add_argument(
    "-p",
    "--parsed",
    action="store_true",
    help="Print out semantic diff of parsed symbol",
)
parser.add_argument(
    "-s",
    "--sexpr",
    action="store_true",
    help="Print out unified diff of s-expr representation",
)

args = parser.parse_args()

A_parts = args.A.rsplit(":", 1)
B_parts = args.B.rsplit(":", 1)

if len(A_parts) != 2 or len(B_parts) != 2:
    error("Symbol should be in libpath:symbolname format")

if not os.path.isfile(A_parts[0]):
    error(f"File does not exist: {A_parts[0]}")

if not os.path.isfile(B_parts[0]):
    error(f"File does not exist: {B_parts[0]}")

try:
    A_lib = KicadLibrary.from_file(A_parts[0])
except KicadFileFormatError as e:
    error(f"Could not parse library: {A_parts[0]}\n{e}")

try:
    B_lib = KicadLibrary.from_file(B_parts[0])
except KicadFileFormatError as e:
    error(f"Could not parse library: {B_parts[0]}\n{e}")

A_symbols = {sym.name: sym for sym in A_lib.symbols}
B_symbols = {sym.name: sym for sym in B_lib.symbols}

if not A_parts[1] in A_symbols:
    error(f"No symbol {A_parts[1]} found in library {A_parts[0]}")

if not B_parts[1] in B_symbols:
    error(f"No symbol {B_parts[1]} found in library {B_parts[0]}")

A = A_symbols[A_parts[1]]
B = B_symbols[B_parts[1]]

if args.parsed or not args.sexpr:
    if PYTEST_AVAILABLE:
        print("Parsed diff:\n")

        difflines = _compare_eq_any(A, B, 2)

        for line in difflines:
            print(line)
    else:
        print("Can not print parsed diff, pytest package is not available.")

    if args.sexpr or not args.parsed:
        print("\n")

if args.sexpr or not args.parsed:
    print("S-expr diff:\n")
    A_sexpr = format_sexp(build_sexp(A.get_sexpr())).splitlines()
    B_sexpr = format_sexp(build_sexp(B.get_sexpr())).splitlines()
    difflines = [line.rstrip() for line in difflib.unified_diff(A_sexpr, B_sexpr)]

    for line in difflines:
        print(line)
