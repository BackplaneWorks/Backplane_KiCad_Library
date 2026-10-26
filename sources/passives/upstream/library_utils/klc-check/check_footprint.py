#!/usr/bin/env python3

import argparse
import os
import re
import sys
import traceback
from glob import glob
from typing import Tuple

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

import junit
from kicad_mod import KicadMod
from print_color import PrintColor
from rulebase import Verbosity
from rules_footprint import get_all_footprint_rules
from rules_footprint.rule import KLCRule


def check_library(
    filename: str, rules, junit_suite: junit.JunitTestSuite, args
) -> Tuple[int, int]:
    """
    Returns (error count, warning count)
    """

    if not os.path.exists(filename):
        printer.red("File does not exist: %s" % filename)
        return (1, 0)

    if not filename.endswith(".kicad_mod"):
        printer.red("File is not a .kicad_mod : %s" % filename)
        return (1, 0)

    if args.errors:
        module = KicadMod(filename)
    else:
        try:
            module = KicadMod(filename)
        except Exception as e:
            printer.red("Could not parse footprint: %s. (%s)" % (filename, e))
            if args.verbose:
                # printer.red("Error: " + str(e))
                traceback.print_exc()
            return (1, 0)

    junit_case = junit.JunitTestCase(module.name)
    junit_suite.add_case(junit_case)

    # check which kind of tests we want to run
    if args.unittest:
        ec, wc = do_unittest(module, rules)
    else:
        ec, wc = do_rulecheck(module, rules, junit_case)
    # done checking the footpint
    return (ec, wc)


def do_unittest(footprint, rules) -> Tuple[int, int]:
    error_count = 0
    m = re.match(r"(\w+)__(.+)__(.+)", footprint.name)
    if not m:
        printer.red("Test '{foot}' could not be parsed".format(foot=footprint.name))
        return (1, 0)
    unittest_result = m.group(1)
    unittest_rule = m.group(2)
    unittest_descrp = m.group(3)  # noqa: F841
    for rule_class in rules:
        rule = rule_class(footprint, args)
        if unittest_rule == rule.name:
            rule.check()
            if unittest_result == "Fail" and rule.error_count == 0:
                printer.red("Test '{foot}' failed".format(foot=footprint.name))
                error_count += 1
                continue
            if unittest_result == "Warn" and rule.warning_count == 0:
                printer.red("Test '{foot}' failed".format(foot=footprint.name))
                error_count += 1
                continue
            if unittest_result == "Pass" and (
                rule.warning_count != 0 or rule.error_count != 0
            ):
                printer.red("Test '{foot}' failed".format(foot=footprint.name))
                error_count += 1
                continue
            printer.green("Test '{foot}' passed".format(foot=footprint.name))

        else:
            continue
    return (error_count, warning_count)


def do_rulecheck(module, rules, junit_case: junit.JunitTestCase) -> Tuple[int, int]:
    ec = 0
    wc = 0
    first = True

    for index, rule in enumerate(rules):
        rule = rule(module, args)

        # run the actual check
        rule.check()

        # count errors
        if rule.hasErrors:
            ec += rule.error_count
        if rule.hasWarnings:
            wc += rule.warning_count

        if args.nowarnings and not rule.hasErrors:
            continue

        if rule.hasOutput:
            if first:
                printer.green("Checking footprint '{fp}':".format(fp=module.name))
                first = False

            printer.yellow("Violating " + rule.name + " - " + rule.url, indentation=2)

            junit.add_klc_rule_results(junit_case, rule)
            rule.printOutput(printer, verbosity)

        if rule.hasErrors:
            if args.fix:
                if args.fixmore and rule.needsFixMore:
                    rule.fixmore()
                rule.fix()
                rule.printOutput(printer, verbosity, args.silent)
                rule.recheck()

    # No messages?
    if first:
        if not args.silent:
            printer.green(
                "Checking footprint '{fp}' - No errors".format(fp=module.name)
            )

    if (args.fix or args.fixmore) and ec > 0:
        module.save()

    return (ec, wc)


parser = argparse.ArgumentParser(
    description=(
        "Checks KiCad footprint files (.kicad_mod) against KiCad Library Convention"
        " (KLC) rules. You can find the KLC at http://kicad.org/libraries/klc/"
    )
)
parser.add_argument("kicad_mod_files", nargs="+")
parser.add_argument("--fix", help="fix the violations if possible", action="store_true")
parser.add_argument(
    "--fixmore",
    help=(
        "fix additional violations, not covered by --fix (e.g. rectangular courtyards),"
        " implies --fix!"
    ),
    action="store_true",
)
parser.add_argument(
    "-r",
    "--rule",
    help="specify single rule to check (default = check all rules)",
    action="store",
)
parser.add_argument(
    "--nocolor", help="does not use colors to show the output", action="store_true"
)
parser.add_argument(
    "-v",
    "--verbose",
    help=(
        "Enable verbose output. -v shows brief information, -vv shows complete"
        " information, -vvv shows debug"
    ),
    action="count",
)
parser.add_argument(
    "--exclude",
    help=(
        "Exclude a particular rule (or rules) to check against. Use comma separated"
        ' values to select multiple rules. e.g. "-e F3.1,F4.2"'
    ),
)
parser.add_argument(
    "-s",
    "--silent",
    help="skip output for footprints passing all checks",
    action="store_true",
)
parser.add_argument(
    "-e", "--errors", help="Do not suppress fatal parsing errors", action="store_true"
)
parser.add_argument(
    "-w", "--nowarnings", help="Hide warnings (only show errors)", action="store_true"
)
parser.add_argument(
    "-u",
    "--unittest",
    help="unit test mode (to be used with test-footprints)",
    action="store_true",
)
parser.add_argument(
    "--junit",
    help="Path to save results in JUnit XML format. Specify with e.g. './xxx --junit file.xml'",
    metavar="file",
)

args = parser.parse_args()
if args.fixmore:
    args.fix = True

printer = PrintColor(use_color=not args.nocolor)

# Set verbosity globally
verbosity: Verbosity = Verbosity.NONE
if args.verbose:
    verbosity = Verbosity(args.verbose)
KLCRule.verbosity = verbosity

# create a list of rules that should be checked
if args.rule:
    selected_rules = args.rule.split(",")
else:
    selected_rules = None

if args.exclude:
    excluded_rules = args.exclude.split(",")
else:
    excluded_rules = None

rules = []
for rule_name, rule in get_all_footprint_rules().items():
    if selected_rules is None or rule_name in selected_rules:
        if excluded_rules is not None and rule_name in excluded_rules:
            pass
        else:
            rules.append(rule.Rule)

# figure out which files should be checked
files = []
for f in args.kicad_mod_files:
    files += glob(f)

if not files:
    printer.red("File argument invalid: {f}".format(f=args.kicad_mod_files))
    sys.exit(1)

# Sort the files for consistent output
files.sort()

junit_suite = junit.JunitTestSuite(name="Footprint KLC Checks", id="klc-fp")

# now iterate over all files and check them
error_count = 0
warning_count = 0
for filename in files:
    ec, wc = check_library(filename, rules, junit_suite, args)
    error_count += ec
    warning_count += wc

if args.fix:
    printer.light_red(
        "Some files were updated - ensure that they still load correctly in KiCad"
    )

if args.junit:
    # create the junit xml report
    if args.verbose:
        printer.light_green(f"Creating JUnit report: {args.junit}")

    junit_report = junit.JUnitReport(args.junit)
    junit_report.add_suite(junit_suite)
    junit_report.save_report()

ret_code = 0  # pass

if error_count:
    # This will fail the pipeline
    ret_code = 3
elif warning_count:
    # This will be an "allowed failure"
    ret_code = 2

sys.exit(ret_code)
