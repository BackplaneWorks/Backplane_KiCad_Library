import inspect
import os
import re
from enum import Enum
from typing import List

from print_color import PrintColor


# Static functions
def isValidName(
    name, checkForGraphicSymbol: bool = False, checkForPowerSymbol: bool = False
) -> bool:
    name = str(name).lower()
    firstChar = True
    for c in name:
        # first character may be '~' in some cases
        if (checkForPowerSymbol or checkForGraphicSymbol) and firstChar and c == "~":
            continue

        firstChar = False
        # Numeric characters check
        if c.isalnum():
            continue

        # Alpha characters (simple set only)
        if "a" <= c <= "z":
            continue

        if c in "_-.+,":
            continue

        return False

    return True


def checkLineEndings(filename: str):
    """
    Check for proper (Unix) line endings
    """
    filecontentsraw = open(filename, "rb").readline()

    LE1 = ord(chr(filecontentsraw[-2]))
    LE2 = ord(chr(filecontentsraw[-1]))

    # 0x0D0A = Windows (CRLF)
    # 0x__0D = Mac OS 9 (CR)
    # 0x__0A = Unix (LF)
    if (LE1 == 0x0D and LE2 == 0x0A) or (LE2 == 0x0D):
        return False

    return True


class Verbosity(Enum):
    SILENT = -1
    NONE = 0
    NORMAL = 1
    HIGH = 2
    DEBUG = 3


class Severity(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    SUCCESS = 3


class KLCRuleLogItem:
    def __init__(self, severity: Severity, message: str):
        self.severity = severity
        self.message = message
        self.extras = []

    def add_extra(self, extra: str):
        self.extras.append(extra)


class KLCRuleBase:
    """
    A base class to represent a KLC rule
    """

    disable_exceptions = False
    verbosity: Verbosity = Verbosity.NONE
    logEntries: List[KLCRuleLogItem] = []
    klc_rule_re = re.compile(r"^(KLC_)([^_]+)_*(.*?)$")

    @property
    def name(self) -> str:
        path = inspect.getfile(self.__class__)
        path = os.path.basename(path)
        path = "".join(path.split(".")[:-1])
        return path.replace("_", ".")

    @property
    def url(self) -> str:
        if self.name.startswith("EC"):
            return "(extended check)"

        categories = {"F": "footprint", "G": "general", "M": "model", "S": "symbol"}

        category = categories[self.name[0]]
        name = self.name.lower()
        group = name.split(".")[0]
        url = f"https://klc.kicad.org/{category}/{group}/{name}/"

        return url

    def __init__(self):
        self.description = self.__doc__.strip().splitlines()[0].strip()
        self.logEntries = []

        # this array holds messages we can print and put into the log
        self.exception_notes = []
        # this map holds details about the exception that can be used by the rule for detailed checking
        self.exceptions_map = {}
        # a rule-implementation can set this to true. That means the rule itself will take care of
        # exception processing. Examples are if the exception is coded to be for only one specific pin
        self.finegrained_exceptions = False

        self.resetErrorCount()
        self.resetWarningCount()
        self.resetExceptionCount()

    def resetErrorCount(self) -> None:
        self.error_count: int = 0

    def resetWarningCount(self) -> None:
        self.warning_count: int = 0

    def resetExceptionCount(self) -> None:
        self.exception_count: int = 0

    @property
    def hasErrors(self) -> bool:
        return self.error_count > 0

    @property
    def hasWarnings(self) -> bool:
        return self.warning_count > 0

    @property
    # this is identical to asking if there are errors or warnings
    def hasOutput(self) -> bool:
        return len(self.logEntries) > 0

    # if there is an exception, that also means that is cannot produce 'real'
    # errors or warnings. So we need to nullify them
    def apply_exceptions(self) -> None:
        if (
            self.hasOutput
            and len(self.exceptions_map) > 0
            and not self.finegrained_exceptions
            and not self.disable_exceptions
        ):
            self.error_count = 0
            self.warning_count = 0

    # adds message into buffer only if such level of verbosity is wanted
    def verboseOut(
        self, msgVerbosity: Verbosity, severity: Severity, message: str
    ) -> None:
        self.messageBuffer.append((message, msgVerbosity, severity, []))

    def exception(self, msg: str) -> None:
        self.exception_count += 1
        self.logEntries.append(KLCRuleLogItem(Severity.INFO, msg))

    def warning(self, msg: str) -> None:
        self.warning_count += 1
        self.logEntries.append(KLCRuleLogItem(Severity.WARNING, msg))

    def warningExtra(self, msg: str) -> None:
        self.logEntries[-1].add_extra(msg)

    def error(self, msg: str) -> None:
        self.error_count += 1
        self.logEntries.append(KLCRuleLogItem(Severity.ERROR, msg))

    def errorExtra(self, msg: str) -> None:
        self.logEntries[-1].add_extra(msg)

    def info(self, msg: str) -> None:
        self.logEntries.append(KLCRuleLogItem(Severity.INFO, msg))

    def success(self, msg: str) -> None:
        self.logEntries.append(KLCRuleLogItem(Severity.SUCCESS, msg))

    def check(self, component, exception=None) -> None:
        raise NotImplementedError("The check method must be implemented")

    def fix(self, component) -> None:
        raise NotImplementedError("The fix method must be implemented")

    def recheck(self) -> None:

        self.resetErrorCount()
        self.resetWarningCount()

        self.check()

        if self.hasErrors():
            self.error("Could not fix all errors")
        else:
            self.success("Everything fixed")

    def parse_exceptions(self, properties) -> None:
        for index, prop in enumerate(properties):
            if matches := self.klc_rule_re.match(prop.name):
                # example matches object ['KLC_', 'S4.2', 'VDD33_{LDO}']
                # hint: the group(0) contains the whole matched string
                # so to get the rule-name, we need to call group(2)
                if matches.group(2) == self.name:
                    # the map should contain key-value pairs that the actual check can use
                    # for a more granular exception system. For example
                    # {'Pin13': 'this is actually a output and is on the left side'}
                    # We get that from the name of the property with the regex above
                    # But the 3rd element might not exist, because people don't need to
                    # add this detailed info
                    if map_key := matches.group(3):
                        pass
                    else:
                        map_key = f"Index_{index}"
                    message = f"({map_key}): {prop.value}"
                    self.exceptions_map |= {map_key: prop.value}
                    self.exception_notes.append(message)

    def print_rule_hint_line(self, printer, verbosity):
        if verbosity.value > Verbosity.NONE.value:
            printer.light_blue(
                f"{self.description} - {self.name} - {self.url}",
                indentation=4,
                max_width=100,
            )

    def printOutput(
        self,
        printer: PrintColor,
        verbosity: Verbosity = Verbosity.NONE,
        no_warnings: bool = False,
        first: bool = False,
    ) -> bool:

        # print this message only for the first rule that gets checked per symbol
        if first and not verbosity == Verbosity.SILENT:
            printer.green(f"Checking component '{self.component_name}':")

        if verbosity.value >= Verbosity.DEBUG.value:
            printer.white("Checking rule " + self.name)

        # No violations
        if len(self.logEntries) == 0:
            return False

        # Verbosity.NONE:   Only print that a rule was violated
        # Verbosity.NORMAL: Print the errors/warning. Also in blue, print the name of the rule
        # Verbosity.HIGH:   Also print 'extraError'
        #
        # It should look like this
        # [Yellow] Violating F9.1 - https://klc.kicad.org/footprint/f9/f9.1/
        # [Blue]     Footprint meta-data is filled in as appropriate - F9.1 - https://klc.kicad.org/footprint/f9/f9.1/
        # [Orange]     Description field does not contain a URL - add the URL to the datasheet

        # only print those lines if requested by verbosity
        if verbosity.value >= Verbosity.NONE.value:
            # Decide how the first line (Violating...) should look like
            # Because we know there are errors, we can print it right away
            # but only if there aren't any active exceptions

            # 1. Exceptions are disabled globally or there are no exceptions
            # 2. Exceptions are enabled and not fine-grained (this is the default)
            # 3. The current rule implements fine-grained exceptions
            if self.disable_exceptions or len(self.exception_notes) == 0:
                # Case 1: Exception system disabled or not exceptions present
                for message in self.exception_notes:
                    printer.gray(f"Disabled exception - {message}", indentation=2)
                printer.yellow(
                    "Violating " + self.name + " - " + self.url, indentation=2
                )
                self.print_rule_hint_line(printer, verbosity)
            else:  # exceptions are enabled
                if self.finegrained_exceptions:
                    # Case3: We have fine grained exceptions
                    # if we are here, that means something is violated
                    printer.yellow(
                        "Violating " + self.name + " - " + self.url, indentation=2
                    )
                    self.print_rule_hint_line(printer, verbosity)
                else:
                    # Case2: normal Exceptions are enabled, that means there cannot be any violations
                    for message in self.exception_notes:
                        printer.yellow(
                            f"Exception {self.name} - {message}", indentation=2
                        )
                    # we also need to make sure the errors and warnings are not printed in red
                    for entry in self.logEntries:
                        entry.severity = Severity.INFO

        # now print all the log entries
        for entry in self.logEntries:
            s = entry.severity  # Severity
            entry_verbosity = {
                Severity.INFO: Verbosity.NONE,
                Severity.WARNING: Verbosity.NORMAL,
                Severity.ERROR: Verbosity.NORMAL,
                Severity.SUCCESS: Verbosity.NORMAL,
            }[s]

            if entry_verbosity.value <= verbosity.value:

                msg = entry.message

                # Join the message with the extra message
                if verbosity.value >= Verbosity.HIGH.value:
                    for e in entry.extras:
                        msg += "\n      - " + e

                if s == Severity.INFO:
                    printer.gray(msg, indentation=4)
                elif s == Severity.WARNING:
                    printer.brown(msg, indentation=4)
                elif s == Severity.ERROR:
                    printer.red(msg, indentation=4)
                elif s == Severity.SUCCESS:
                    printer.green(msg, indentation=4)
                else:
                    printer.red("unknown severity: " + msg, indentation=4)

        return True
