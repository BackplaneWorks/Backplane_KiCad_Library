#!/usr/bin/env python3

import argparse
import os
import queue
import re
import sys
import time
import traceback
from dataclasses import dataclass
from functools import lru_cache
from glob import glob  # enable windows wildcards
from multiprocessing import JoinableQueue, Lock, Process, Queue
from typing import List, Optional, Tuple

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

import junit
from kicad_sym import KicadFileFormatError, KicadLibrary
from print_color import PrintColor
from rulebase import Severity, Verbosity
from rules_symbol import get_all_symbol_rules
from rules_symbol.rule import KLCRule


class SymbolCheck:
    def __init__(
        self,
        selected_rules: Optional[List[str]] = None,
        excluded_rules: Optional[List[str]] = None,
        verbosity: Verbosity = Verbosity.NONE,
        disable_exceptions: bool = False,
        footprints=None,
        use_color: bool = True,
        no_warnings: bool = False,
        log: bool = False,
    ):
        self.footprints = footprints
        self.printer = PrintColor(use_color=use_color)
        self.verbosity: Verbosity = verbosity
        self.disable_exceptions: bool = disable_exceptions
        self.no_warnings: bool = no_warnings
        self.log: bool = log
        self.error_count: int = 0
        self.warning_count: int = 0
        self.junit_cases = []

        # build a list of rules to work with
        self.rules: List[KLCRule] = []

        for rule_name, rule in get_all_symbol_rules().items():
            if selected_rules is None or rule_name in selected_rules:
                if excluded_rules is not None and rule_name in excluded_rules:
                    pass
                else:
                    self.rules.append(rule.Rule)

    def do_unittest(self, symbol) -> Tuple[int, int]:
        error_count = 0
        m = re.match(r"(\w+)__(.+)__(.+)", symbol.name)
        if not m:
            self.printer.red("Test '{sym}' could not be parsed".format(sym=symbol.name))
            return (1, 0)
        unittest_result = m.group(1)
        unittest_rule = m.group(2)
        unittest_descrp = m.group(3)  # noqa: F841
        for rule_class in self.rules:
            rule_class.footprints_dir = self.footprints
            rule = rule_class(symbol)
            rule.disable_exceptions = self.disable_exceptions
            if unittest_rule == rule.name:
                # check if there is an exception for this rule
                rule.parse_exceptions(symbol.properties)
                rule.check()
                rule.apply_exceptions()
                if unittest_result == "Fail" and rule.error_count == 0:
                    self.printer.red("Test '{sym}' failed".format(sym=symbol.name))
                    error_count += 1
                    continue
                if unittest_result == "Warn" and rule.warning_count == 0:
                    self.printer.red("Test '{sym}' failed".format(sym=symbol.name))
                    error_count += 1
                    continue
                if unittest_result == "Pass" and (
                    rule.warning_count != 0 or rule.error_count != 0
                ):
                    self.printer.red("Test '{sym}' failed".format(sym=symbol.name))
                    error_count += 1
                    continue
                self.printer.green("Test '{sym}' passed".format(sym=symbol.name))

            else:
                continue
        return (error_count, 0)

    def do_rulecheck(self, symbol) -> Tuple[int, int]:
        symbol_error_count = 0
        symbol_warning_count = 0

        junit_case = junit.JunitTestCase(name=f"{symbol.libname}:{symbol.name}")
        self.junit_cases.append(junit_case)

        for index, rule_class in enumerate(self.rules):
            rule_class.footprints_dir = self.footprints
            rule = rule_class(symbol)
            rule.disable_exceptions = self.disable_exceptions

            # check if there is an exception for this rule
            for exception_note in rule.exception_notes:
                # add them to the junit reporter
                # we don't need to print anything, the rulebase will take care of this
                junit_case.add_result(Severity.INFO, junit.JUnitResult(exception_note))

            # now run the actual check
            rule.check()

            # call the generic printer function
            rule.printOutput(
                self.printer, self.verbosity, self.no_warnings, first=(index == 0)
            )

            # if there are only warnings, and we disabled warnings, don't do anything
            # and start checking the next rule
            if self.no_warnings and not rule.hasErrors:
                continue

            # if there is an exception, that also means that is cannot produce 'real'
            # errors or warnings. So we need to nullify them
            rule.apply_exceptions()

            # add info about this check to the junit reporter
            junit.add_klc_rule_results(junit_case, rule)

            # increment the number of violations
            symbol_error_count += rule.error_count
            symbol_warning_count += rule.warning_count

        return (symbol_error_count, symbol_warning_count)

    @lru_cache(maxsize=None)
    def _load_library(self, filename):
        return KicadLibrary.from_path(filename)

    def check_library(
        self, filename: str, component=None, pattern=None, is_unittest: bool = False
    ) -> Tuple[int, int]:
        error_count = 0
        warning_count = 0
        if not os.path.exists(filename):
            self.printer.red("File does not exist: %s" % filename)
            return (1, 0)

        if not (filename.endswith(".kicad_sym") or filename.endswith(".kicad_symdir")):
            self.printer.red(
                "File is not a .kicad_sym nor .kicad_symdir: %s" % filename
            )
            return (1, 0)

        try:
            library = self._load_library(filename)
        except KicadFileFormatError as e:
            self.printer.red("Could not parse library: %s. (%s)" % (filename, e))
            if self.verbosity:
                self.printer.red("Error: " + str(e))
                traceback.print_exc()
            return (1, 0)

        for symbol in library.symbols:
            if component:
                if component.lower() != symbol.name.lower():
                    continue

            if pattern:
                if not re.search(pattern, symbol.name, flags=re.IGNORECASE):
                    continue

            # check which kind of tests we want to run
            if is_unittest:
                ec, wc = self.do_unittest(symbol)
            else:
                ec, wc = self.do_rulecheck(symbol)

            error_count += ec
            warning_count += wc

        # done checking the lib
        self.error_count += error_count
        self.warning_count += warning_count
        return (error_count, warning_count)


@dataclass
class CheckResults:
    identifier: int
    error_count: int
    warning_count: int
    test_cases: List[junit.JunitTestCase]


def worker(
    inp,
    outp,
    lock,
    selected_rules,
    excluded_rules,
    verbosity: Verbosity,
    disable_exceptions,
    footprints,
    args,
    i=0,
):
    # have one instance of SymbolCheck per worker
    checker = SymbolCheck(
        selected_rules,
        excluded_rules,
        verbosity,
        disable_exceptions,
        footprints,
        not args.nocolor,
        no_warnings=args.nowarnings,
        log=args.log,
    )
    checker.printer.buffered = True

    while True:
        try:
            fn = inp.get(block=False)
            # run the check on this file
            checker.check_library(fn, args.component, args.pattern, args.unittest)
            # print the console output, all at once while we have the lock
            lock.acquire()
            checker.printer.flush()
            lock.release()
            # signal that we are done with this item
            inp.task_done()
        except queue.Empty:
            break

    # output all the results at once
    outp.put(
        CheckResults(
            i,
            checker.error_count,
            checker.warning_count,
            checker.junit_cases,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Checks KiCad library files (.kicad_sym) against KiCad Library Convention"
            " (KLC) rules. You can find the KLC at https://kicad.org/libraries/klc/"
        )
    )
    parser.add_argument("kicad_sym_files", nargs="+")
    parser.add_argument(
        "-c", "--component", help="check only a specific component", action="store"
    )
    parser.add_argument(
        "-p",
        "--pattern",
        help="Check multiple components by matching a regular expression",
        action="store",
    )
    parser.add_argument(
        "-r",
        "--rule",
        help=(
            "Select a particular rule (or rules) to check against (default = all"
            ' rules). Use comma separated values to select multiple rules. e.g. "-r'
            ' S3.1,EC02"'
        ),
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help=(
            "Exclude a particular rule (or rules) to check against. Use comma separated"
            ' values to select multiple rules. e.g. "-e S3.1,EC02"'
        ),
    )
    # currently there is no write support for a kicad symbol
    #    parser.add_argument('--fix', help='fix the violations if possible', action='store_true')
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
        "-x",
        "--no-exceptions",
        help="Disable rule-exceptions processing",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--silent",
        help="skip output for symbols passing all checks",
        action="store_true",
    )
    parser.add_argument(
        "-l", "--log", help="Path to JSON file to log error information"
    )
    parser.add_argument(
        "-w",
        "--nowarnings",
        help="Hide warnings (only show errors)",
        action="store_true",
    )
    parser.add_argument(
        "-u",
        "--unittest",
        help="unit test mode (to be used with test-symbols)",
        action="store_true",
    )
    parser.add_argument(
        "--junit",
        help="Path to save results in JUnit XML format. Specify with e.g. './xxx --junit file.xml'",
        metavar="file",
    )
    parser.add_argument("-j", "--multiprocess", help="use parallel processing")
    parser.add_argument(
        "--footprints",
        help="Path to footprint library dir. Usually same path as KICADx_FOOTPRINT_DIR in KiCad settings.",
    )
    args = parser.parse_args()

    #
    if args.rule:
        selected_rules = args.rule.split(",")
    else:
        selected_rules = None

    if args.exclude:
        excluded_rules = args.exclude.split(",")
    else:
        excluded_rules = None

    # Set verbosity globally
    verbosity = Verbosity.NONE
    if args.verbose:
        verbosity = Verbosity(args.verbose)
    if args.silent:
        verbosity = Verbosity.SILENT
    KLCRule.verbosity = verbosity

    # Set disable_exceptions globally
    disable_exceptions = False
    if args.no_exceptions:
        disable_exceptions = args.no_exceptions

    # check if a footprints dir was passed
    footprints = args.footprints

    # populate list of files
    files = []
    for f in args.kicad_sym_files:
        files += glob(f)

    if not files:
        print("File argument invalid: {f}".format(f=args.kicad_sym_files))
        sys.exit(1)

    # re work files list to include size
    for i in range(len(files)):
        files[i] = (files[i], os.path.getsize(files[i]))
    # Sort list by file size, largest on top
    # the idea is to further speed up multiprocessing by working on the bigger items first
    if not args.unittest:
        files.sort(key=lambda filename: filename[1], reverse=True)

    junit_suite = junit.JunitTestSuite(name="Symbol KLC Checks", id="klc-sym")

    # Create queues for multiprocessing
    task_queue = JoinableQueue()
    out_queue = Queue()

    for filename, size in files:
        task_queue.put(filename)

    jobs = []

    # create the workers
    lock = Lock()
    for i in range(int(args.multiprocess) if args.multiprocess else 1):
        p = Process(
            target=worker,
            args=(
                task_queue,
                out_queue,
                lock,
                selected_rules,
                excluded_rules,
                verbosity,
                disable_exceptions,
                footprints,
                args,
                i,
            ),
        )
        jobs.append(p)
        p.start()

    error_count = 0
    warning_count = 0
    ret_code = 0  # pass

    # wait for all workers to finish
    while jobs:
        for p in jobs:
            while True:
                try:
                    results = out_queue.get(block=False)

                    for junit_case in results.test_cases:
                        junit_suite.add_case(junit_case)

                    error_count += results.error_count
                    warning_count += results.warning_count
                except queue.Empty:
                    break
            if not p.is_alive():
                if p.exitcode:
                    ret_code = p.exitcode
                jobs.remove(p)

    out_queue.put("STOP")

    time.sleep(1)

    if args.junit:
        # create the junit xml report
        if args.verbose:
            print(f"Creating JUnit report: {args.junit}")

        junit_report = junit.JUnitReport(args.junit)
        junit_report.add_suite(junit_suite)
        junit_report.save_report()

    out_queue.close()

    if not ret_code:
        if error_count:
            # This will fail the pipeline
            ret_code = 3
        elif warning_count:
            # This will be an "allowed failure"
            ret_code = 2

    sys.exit(ret_code)
