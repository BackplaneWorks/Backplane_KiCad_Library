#!/usr/bin/env python3

"""
This script checks the validity of a library table against existing libraries
KiCad maintains the following default library tables:

* Symbols - sym_lib_table
* Footprints - fp_lib_table

It is important that the official libraries match the entries in these tables.

"""

import argparse
import os
import sys

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

import junit
from lib_table import LibTable


def check_entries(lib_table, lib_names, junit_suite: junit.JunitTestSuite):

    errors = [0]

    def add_error(case_name, error_msg):
        print(f"ERROR: {error_msg}")
        jtestcase = junit.JunitTestCase(name=case_name)
        jtestcase.add_result(junit.Severity.ERROR, junit.JUnitResult(error_msg))
        junit_suite.add_case(jtestcase)
        # List allows mutability of the errors variable
        errors[0] += 1

    # Check for entries that are incorrectly formatted
    for entry in lib_table.entries:
        nickname = entry["name"]
        uri = entry["uri"]

        if "\\" in uri:
            error_msg = f"Found '\\' character in entry '{nickname}' - Path separators must be '/'"
            add_error("Path separators", error_msg)

        uri_last = ".".join(uri.split("/")[-1].split(".")[:-1])

        if not uri_last == nickname:
            error_msg = f"Nickname '{nickname}' does not match path '{uri}'"
            add_error("Incorrect nickname", error_msg)

    lib_table_names = [entry["name"] for entry in lib_table.entries]

    # Check for libraries that are in the lib_table but should not be
    for name in lib_table_names:
        if name not in lib_names:
            error_msg = f"Extra library '{name}' found in library table"
            add_error("Extra library", error_msg)

        if lib_table_names.count(name) > 1:
            error_msg = f"Library '{name}' is duplicated in table"
            add_error("Duplicated library", error_msg)

    # Check for libraries that are not in the lib_table but should be
    for name in lib_names:
        if name not in lib_table_names:
            error_msg = f"Library '{name}' missing from library table"
            add_error("Missing library", error_msg)

    # Incorrect lines in the library table
    for error in lib_table.errors:
        add_error("Library table bad lines", error)
        error_msg = f"Incorrect line found in library table:\n\t{error}"

    return errors[0]


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Compare a sym-lib-table file against a list of .lib library files"
    )
    parser.add_argument("libs", nargs="+", help=".lib files")
    parser.add_argument("-t", "--table", help="sym-lib-table file", action="store")
    parser.add_argument(
        "--junit",
        help="Path to save results in JUnit XML format. Specify with e.g. './xxx --junit file.xml'",
        metavar="file",
    )

    args = parser.parse_args()

    lib_names = []

    for lib in args.libs:
        lib_name = ".".join(os.path.basename(lib).split(".")[:-1])
        lib_names.append(lib_name)

    print(
        "Checking library table - '{table}'".format(table=os.path.basename(args.table))
    )

    print("Found {n} libraries".format(n=len(lib_names)))

    table = LibTable(args.table)
    junit_suite = junit.JunitTestSuite(name="Library Table Checks", id="lib-table-fp")

    errors = check_entries(table, lib_names, junit_suite)

    if args.junit:
        junit_report = junit.JUnitReport(args.junit)
        junit_report.add_suite(junit_suite)
        junit_report.save_report()

    sys.exit(errors)
