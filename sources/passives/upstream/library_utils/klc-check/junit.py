import os
import sys
from typing import List
from xml.etree import ElementTree as ET

# Path to common directory
common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)

if common not in sys.path:
    sys.path.insert(0, common)

from rulebase import Severity

SeverityToStr = {
    Severity.INFO: "Info",
    Severity.ERROR: "Errors",
    Severity.WARNING: "Warnings",
}


class JUnitResult:

    def __init__(self, message: str, extras: list[str] = []):
        self.message = message
        self.extras = extras


class JunitTestCase:

    name: str
    description: str
    results: dict[Severity, List[JUnitResult]]

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.results = {}

    def add_result(self, severity: Severity, result: JUnitResult):

        if severity not in self.results:
            self.results[severity] = []

        self.results[severity].append(result)


class JunitTestSuite:
    """
    A class to represent a Junit test suite
    """

    name: str
    cases: List[JunitTestCase]

    def __init__(self, name, id=None):
        self.name = name
        self.id = id
        self.cases = []

    def add_case(self, case: JunitTestCase):
        self.cases.append(case)


class JUnitReport:

    path: str
    suites: list[JunitTestSuite]

    def __init__(self, path: str):

        self.path = path
        self.suites = []

        # Load the existing report (don't parse it in detail, we just need to be able to append to it)
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                data = f.read()
                self.root = ET.fromstring(data)
        else:
            self.root = ET.Element("testsuites")

    def save_report(self):
        """
        Write the report to the parh.
        """

        for suite in self.suites:
            suite_et = ET.SubElement(
                self.root,
                "testsuite",
                {
                    "name": suite.name,
                },
            )

            if suite.id is not None:
                suite_et.set("id", suite.id)

            failures = 0
            tests = 0

            for case in suite.cases:

                if not case.results:
                    # Create a test case for each component that passes
                    tests += 1
                    ET.SubElement(
                        suite_et,
                        "testcase",
                        {
                            "classname": suite.name,
                            "name": case.name,
                        },
                    )
                else:
                    # Create a test case for each component×severity
                    for severity, results in case.results.items():
                        tests += 1
                        testcase_et = ET.SubElement(
                            suite_et,
                            "testcase",
                            {
                                # Classname=suite name makes it appear in the Gitlab UI
                                # https://gitlab.com/gitlab-org/gitlab/-/issues/299086
                                "classname": suite.name,
                                "name": f"{case.name} - {SeverityToStr[severity]}",
                                "type": SeverityToStr[severity],
                            },
                        )

                        failure_type = (
                            "FAILURE"
                            if severity == Severity.ERROR
                            else "WARNING" if severity == Severity.WARNING else "Info"
                        )

                        # we remove duplicates, while preserving the order of the list,
                        # because on footprints, there can be many:
                        # Some THT pads have incorrect layer settings
                        # - Pad '41' missing layer '*.Mask'
                        # - Pad '41' missing layer '*.Mask'
                        # - Pad '41' missing layer '*.Mask'
                        unique_results = list(dict.fromkeys(results))

                        for result in unique_results:
                            failures += 1
                            full_msg = (
                                result.message + "\n    " + "\n    ".join(result.extras)
                            )

                            ET.SubElement(
                                testcase_et,
                                "failure",
                                {
                                    "message": result.message,
                                    "type": failure_type,
                                },
                            ).text = full_msg

            suite_et.set("tests", str(tests))
            suite_et.set("failures", str(failures))

        tree = ET.ElementTree(self.root)
        ET.indent(tree)
        tree.write(self.path, encoding="utf-8", xml_declaration=True)

    def add_suite(self, suite: JunitTestSuite):
        self.suites.append(suite)


def add_klc_rule_results(test_case: JunitTestCase, rule):
    """
    Transforms the log entries of a KLC rule into JUnit test results.

    One result per severity per rule.
    """

    sev_msgs = {}

    for log_entry in rule.logEntries:
        severity = log_entry.severity

        if severity not in sev_msgs:
            sev_msgs[severity] = [rule.url]

        sev_msgs[severity].append(log_entry.message)
        sev_msgs[severity] += ["   - " + m for m in log_entry.extras]

    for severity, msgs in sev_msgs.items():
        result_msg = rule.name + ": " + rule.description
        test_case.add_result(severity, JUnitResult(result_msg, msgs))
