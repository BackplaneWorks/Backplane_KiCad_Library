import re

from kicad_sym import KicadSymbol
from rules_symbol.rule import KLCRule, pinString


class Rule(KLCRule):
    """Pins should be grouped by function"""

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        # This rule will handle fine-grained exceptions
        self.finegrained_exceptions = True

        pinsnames_with_exceptions = list(self.exceptions_map.keys())
        self.pins_to_check = []
        for pin in self.component.pins:
            if pin.name in pinsnames_with_exceptions:
                self.exception(
                    f"Exception for {pinString(pin)}: {self.exceptions_map[pin.name]}"
                )
            else:
                self.pins_to_check.append(pin)

    def checkGroundPins(self) -> None:
        # Includes negative power pins
        GND = ["^[ad]*g(rou)*nd(a)*$", "^[ad]*v(ss)$"]

        first = True
        for pin in self.pins_to_check:
            name = str(pin.name.lower())
            for gnd in GND:
                if re.search(gnd, name, flags=re.IGNORECASE) is not None:
                    # Pin orientation should be "up"
                    if pin.get_direction() != "U":
                        if first:
                            first = False
                            self.warning(
                                "Ground and negative power pins should be placed at"
                                " bottom of symbol"
                            )
                        self.warningExtra(pinString(pin))

    def checkPositivePowerInPins(self) -> None:
        """
        Check that positive power pins are placed at the top of the symbol,
        or the left of the symbol if there are power_out pins.
        """

        # Positive power pins only
        def is_positive_power(pin):
            pos_power_patterns = [r"^[ad]*v(aa|cc|dd|bat|in)$", r"^in\+?$"]
            return any(
                re.search(patt, pin.name, flags=re.IGNORECASE)
                for patt in pos_power_patterns
            )

        seen_error_names = set()

        positive_power_input_pins = [
            pin for pin in self.power_in_pins if is_positive_power(pin)
        ]

        for pin in positive_power_input_pins:

            # Skip if we've already seen an error for this pin name
            if pin.name in seen_error_names:
                continue

            pin_error = False

            # If there are any power_out pins, the inputs should be on the left
            # else they should be on the top
            if len(self.power_out_pins) == 0:
                if pin.get_direction() != "D":
                    self.error("Positive power pins should be placed at top of symbol")
                    self.errorExtra(
                        "Power conversion devices (e.g. regulators) with both power inputs and outputs "
                        "are an exception (for these, inputs on left, outputs on right)"
                    )
                    pin_error = True
            else:
                if pin.get_direction() != "R":
                    self.error(
                        "For a power converter symbol, positive power pins should be placed at left of symbol"
                    )
                    self.errorExtra(
                        "This symbol has power input and output pins, so it is assumed to be a power converter. "
                        "If this symbol not a power converter, you can ignore this error."
                    )
                    pin_error = True

            if pin_error:
                self.errorExtra(pinString(pin))
                seen_error_names.add(pin.name)

    def checkPowerOutPins(self) -> None:
        seen_error_names = set()

        for pin in self.power_out_pins:

            # Skip if we've already seen an error for this pin name
            if pin.name in seen_error_names:
                continue

            if pin.get_direction() != "L":
                self.error("Power output pins should be placed at right of symbol")
                self.errorExtra(pinString(pin))
                seen_error_names.add(pin.name)

    def check(self) -> bool:
        # no need to check pins on a derived symbols
        if self.component.extends is not None:
            return False

        # We don't handle these in this check
        if self.component.is_power_symbol():
            return

        # All the pins actually marked with the power types
        self.power_in_pins = [p for p in self.pins_to_check if p.etype == "power_in"]
        self.power_out_pins = [p for p in self.pins_to_check if p.etype == "power_out"]

        self.checkGroundPins()
        self.checkPositivePowerInPins()
        self.checkPowerOutPins()

        # No errors, only warnings
        return False

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fixing not supported")
