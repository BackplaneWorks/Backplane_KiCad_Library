from typing import List

from kicad_sym import KicadSymbol, Pin, mm_to_mil
from rules_symbol.rule import KLCRule, pinString


class Rule(KLCRule):
    """General pin requirements"""

    def __init__(self, component: KicadSymbol):
        super().__init__(component)

        self.violating_pins: List[Pin] = []

    def checkPinOrigin(self, gridspacing: int = 100) -> bool:
        self.violating_pins = []
        err = False
        for pin in self.component.pins:
            grid = gridspacing
            posx = mm_to_mil(pin.posx)
            posy = mm_to_mil(pin.posy)
            if pin.etype == "no_connect":
                # allow no_connect pins to be on a 50mil grid
                # when pinlength is 50 or 150mil, and they are on the outline, they will not be
                # on a 100mil grid.  we don't really care if they can easily be connected to, because
                # they are not supposed to be connected
                grid = 50
            if (posx % grid) != 0 or (posy % grid) != 0:
                self.violating_pins.append(pin)
                if not err:
                    self.error(
                        "Pins not located on {0}mil (={1:.3}mm) grid:".format(
                            grid, grid * 0.0254
                        )
                    )
                self.error(" - {0} ".format(pinString(pin, loc=True)))
                err = True

        return len(self.violating_pins) > 0

    def checkNameNumberPins(self) -> bool:
        err = False
        for pin in self.component.pins:
            if not pin.number:
                self.error(f"Pin {pinString(pin)} does not have a number")
                err = True
            if not pin.name:
                # pins might not have a name, for example TVS diode arrays
                self.warning(f"Pin {pinString(pin)} does not have a name")
                err = True

        return err

    def checkDuplicatePins(self) -> bool:
        test_pins = self.component.pins
        seen = set()
        for pin in test_pins:
            identity = (pin.number, pin.body_style_idx, pin.unit)
            if identity in seen:
                self.error("Pin {n} is duplicated:".format(n=pin.number))
                self.errorExtra(pinString(pin))
            seen.add(identity)

        return len(seen) != len(test_pins)  # true iff there are duplicates

    def checkPinLength(
        self, errorPinLength: int = 49, warningPinLength: int = 99
    ) -> bool:
        self.violating_pins = []

        for pin in self.component.pins:
            length = mm_to_mil(pin.length)

            err = False

            # ignore zero-length pins e.g. hidden power pins
            if length == 0:
                continue

            if length <= errorPinLength:
                self.error(
                    "{pin} length ({len}mils) is below {pl}mils".format(
                        pin=pinString(pin), len=length, pl=errorPinLength + 1
                    )
                )
            elif length <= warningPinLength:
                self.warning(
                    "{pin} length ({len}mils) is below {pl}mils".format(
                        pin=pinString(pin), len=length, pl=warningPinLength + 1
                    )
                )

            if length % 50 != 0:
                self.warning(
                    "{pin} length ({len}mils) is not a multiple of 50mils".format(
                        pin=pinString(pin), len=length
                    )
                )

            # length too long flags a warning
            if length > 300:
                err = True
                self.error(
                    "{pin} length ({length}mils) is longer than maximum (300mils)".format(
                        pin=pinString(pin), length=length
                    )
                )

            if err:
                self.violating_pins.append(pin)

        return len(self.violating_pins) > 0

    def check(self) -> bool:
        # no need to check pins on a derived symbols
        if self.component.extends is not None:
            return False

        # determine pin-grid:
        #  - standard components should use 100mil
        #  - "small" symbols (resistors, diodes, ...) should use 50mil
        pingrid = 100
        errorPinLength = 49
        warningPinLength = 99
        if self.component.is_small_component_heuristics():
            pingrid = 50
            errorPinLength = 24
            warningPinLength = 49

        return any(
            [
                self.checkPinOrigin(pingrid),
                self.checkPinLength(errorPinLength, warningPinLength),
                self.checkDuplicatePins(),
                self.checkNameNumberPins(),
            ]
        )

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """

        self.info("Fix not supported")

        if self.checkPinOrigin():
            pass

        if self.checkPinLength():
            pass
